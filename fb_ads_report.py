#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_ACCOUNT_ID = "act_1594070645652115"
DEFAULT_GRAPH_VERSION = "v23.0"


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_config() -> tuple[str, str, str]:
    load_dotenv()
    token = os.environ.get("META_ACCESS_TOKEN") or os.environ.get("FB_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Missing META_ACCESS_TOKEN. Put it in .env or export it.")
    account_id = os.environ.get("META_AD_ACCOUNT_ID", DEFAULT_ACCOUNT_ID)
    version = os.environ.get("META_GRAPH_VERSION", DEFAULT_GRAPH_VERSION)
    return token, account_id, version


def graph_get(path: str, params: dict | None = None) -> dict:
    token, _account_id, version = get_config()
    params = params or {}
    query = urllib.parse.urlencode({**params, "access_token": token})
    url = f"https://graph.facebook.com/{version}/{path}?{query}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body}
        raise RuntimeError(
            f"Graph API error HTTP {exc.code}: {json.dumps(payload, ensure_ascii=False)}"
        ) from None


def as_int(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def as_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def summarize_rows(rows: list[dict]) -> dict:
    spend = 0.0
    action_totals: dict[str, int] = {}
    install_actions: dict[str, int] = {}
    add_to_cart = 0

    for row in rows:
        spend += as_float(row.get("spend"))
        for action in row.get("actions") or []:
            action_type = action.get("action_type") or ""
            value = as_int(action.get("value"))
            action_totals[action_type] = action_totals.get(action_type, 0) + value
            if action_type == "add_to_cart":
                add_to_cart += value
            if "install" in action_type.lower():
                install_actions[action_type] = install_actions.get(action_type, 0) + value

    return {
        "rows": len(rows),
        "spend": round(spend, 2),
        "add_to_cart": add_to_cart,
        "install_actions": install_actions,
        "top_actions": dict(
            sorted(action_totals.items(), key=lambda item: item[1], reverse=True)[:20]
        ),
    }


def paginate(path: str, params: dict) -> list[dict]:
    rows: list[dict] = []
    payload = graph_get(path, params)
    rows.extend(payload.get("data") or [])
    next_url = (payload.get("paging") or {}).get("next")
    while next_url:
        req = urllib.request.Request(next_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        rows.extend(payload.get("data") or [])
        next_url = (payload.get("paging") or {}).get("next")
    return rows


def cmd_diagnose(_args: argparse.Namespace) -> None:
    _token, account_id, _version = get_config()
    permissions = graph_get("me/permissions")
    adaccounts = graph_get("me/adaccounts", {"fields": "id,name,account_status", "limit": 50})
    granted = [
        item.get("permission")
        for item in permissions.get("data", [])
        if item.get("status") == "granted"
    ]
    accounts = adaccounts.get("data") or []
    print_json(
        {
            "granted_permissions": granted,
            "target_ad_account": account_id,
            "target_account_visible": any(a.get("id") == account_id for a in accounts),
            "visible_accounts": accounts,
        }
    )


def cmd_account(_args: argparse.Namespace) -> None:
    _token, account_id, _version = get_config()
    print_json(
        graph_get(
            account_id,
            {
                "fields": (
                    "id,name,account_status,timezone_name,currency,"
                    "amount_spent,balance"
                )
            },
        )
    )


def cmd_campaigns(args: argparse.Namespace) -> None:
    _token, account_id, _version = get_config()
    rows = paginate(
        f"{account_id}/campaigns",
        {
            "fields": "id,name,status,effective_status,created_time,updated_time",
            "limit": str(args.limit),
        },
    )
    print_json({"rows": len(rows), "data": rows})


def cmd_insights(args: argparse.Namespace) -> None:
    _token, account_id, _version = get_config()
    params = {
        "fields": args.fields,
        "level": args.level,
        "limit": str(args.limit),
    }
    if args.date:
        params["time_range"] = json.dumps({"since": args.date, "until": args.date})
    elif args.since and args.until:
        params["time_range"] = json.dumps({"since": args.since, "until": args.until})
    elif args.date_preset:
        params["date_preset"] = args.date_preset
    else:
        params["date_preset"] = "yesterday"

    if args.time_increment:
        params["time_increment"] = str(args.time_increment)

    rows = paginate(f"{account_id}/insights", params)
    print_json({"summary": summarize_rows(rows), "data": rows})


def print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Meta Marketing API reporting helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    diagnose = sub.add_parser("diagnose", help="Check token permissions and ad accounts.")
    diagnose.set_defaults(func=cmd_diagnose)

    account = sub.add_parser("account", help="Show target ad account info.")
    account.set_defaults(func=cmd_account)

    campaigns = sub.add_parser("campaigns", help="List campaigns.")
    campaigns.add_argument("--limit", type=int, default=100)
    campaigns.set_defaults(func=cmd_campaigns)

    insights = sub.add_parser("insights", help="Read insights and summarize spend/actions.")
    insights.add_argument("--date", help="Single date, YYYY-MM-DD.")
    insights.add_argument("--since", help="Range start date, YYYY-MM-DD.")
    insights.add_argument("--until", help="Range end date, YYYY-MM-DD.")
    insights.add_argument("--date-preset", help="Meta date preset, e.g. yesterday or last_7d.")
    insights.add_argument("--level", default="account", choices=["account", "campaign", "adset", "ad"])
    insights.add_argument("--time-increment", default=None, help="Use 1 for daily rows.")
    insights.add_argument("--limit", type=int, default=500)
    insights.add_argument(
        "--fields",
        default=(
            "date_start,date_stop,campaign_id,campaign_name,adset_id,adset_name,"
            "ad_id,ad_name,spend,actions,action_values"
        ),
    )
    insights.set_defaults(func=cmd_insights)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
