#!/usr/bin/env python3
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import fb_ads_report


CONFIG_PATH = Path("fb_config.json")
APP_STORE_RE = re.compile(r"(?:/id|id=)(\\d{8,12})")


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def extract_app_store_id(value: Any) -> str | None:
    if isinstance(value, str):
        match = APP_STORE_RE.search(value)
        return match.group(1) if match else None
    if isinstance(value, dict):
        for child in value.values():
            found = extract_app_store_id(child)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = extract_app_store_id(child)
            if found:
                return found
    return None


def action_value(row: dict[str, Any], exact_type: str) -> int:
    total = 0
    for action in row.get("actions") or []:
        if action.get("action_type") == exact_type:
            total += fb_ads_report.as_int(action.get("value"))
    return total


def install_count(row: dict[str, Any]) -> int:
    # This account's web-to-app flow reports app installs as add_to_cart.
    return action_value(row, "add_to_cart")


def creative_payload(creative: dict[str, Any] | None) -> dict[str, Any]:
    if not creative:
        return {}
    payload: dict[str, Any] = {}
    for key in ("object_story_spec", "asset_feed_spec", "url_tags"):
        if key in creative:
            payload[key] = creative[key]
    return payload


def load_ad_package_map(config: dict[str, Any]) -> dict[str, str]:
    app_store_map = config.get("app_store_id_to_package") or {}
    campaign_map = config.get("campaign_name_to_package") or {}
    ad_map: dict[str, str] = {}

    rows = fb_ads_report.paginate(
        f"{fb_ads_report.get_config()[1]}/ads",
        {
            "fields": (
                "id,name,campaign{name},creative{object_story_spec,asset_feed_spec,url_tags}"
            ),
            "limit": "500",
        },
    )

    for ad in rows:
        ad_id = ad.get("id")
        if not ad_id:
            continue

        app_store_id = extract_app_store_id(creative_payload(ad.get("creative")))
        if app_store_id and app_store_id in app_store_map:
            ad_map[ad_id] = app_store_map[app_store_id]
            continue

        campaign_name = ((ad.get("campaign") or {}).get("name") or "")
        for needle, package_name in campaign_map.items():
            if needle and needle in campaign_name:
                ad_map[ad_id] = package_name
                break

    return ad_map


def fetch_facebook_spend_by_bjt_day(bjt_day: str) -> list[dict[str, Any]]:
    datetime.strptime(bjt_day, "%Y-%m-%d")
    config = load_config()
    ad_package_map = load_ad_package_map(config)
    media_source_code = config.get("media_source_code", "facebook")

    _token, account_id, _version = fb_ads_report.get_config()
    rows = fb_ads_report.paginate(
        f"{account_id}/insights",
        {
            "fields": (
                "date_start,date_stop,campaign_id,campaign_name,adset_id,adset_name,"
                "ad_id,ad_name,spend,actions"
            ),
            "time_range": json.dumps({"since": bjt_day, "until": bjt_day}),
            "level": "ad",
            "limit": "500",
        },
    )

    agg: dict[str, dict[str, Any]] = {}
    unknown_ads: list[dict[str, Any]] = []

    for row in rows:
        spend = fb_ads_report.as_float(row.get("spend"))
        installs = install_count(row)
        ad_id = row.get("ad_id")
        package_name = ad_package_map.get(ad_id or "")

        if not package_name:
            unknown_ads.append(
                {
                    "ad_id": ad_id,
                    "ad_name": row.get("ad_name"),
                    "campaign_name": row.get("campaign_name"),
                    "spend": round(spend, 2),
                }
            )
            continue

        if package_name not in agg:
            agg[package_name] = {
                "stat_date": bjt_day,
                "package_name": package_name,
                "media_source_code": media_source_code,
                "installs": 0,
                "spend": 0.0,
            }
        agg[package_name]["installs"] += installs
        agg[package_name]["spend"] += spend

    results = []
    for item in agg.values():
        item["spend"] = round(item["spend"], 2)
        results.append(item)
    results.sort(key=lambda item: item["package_name"])
    return results, unknown_ads


def upload_rows_bulk(rows: list[dict[str, Any]], timeout: int = 20) -> dict[str, Any]:
    base_url = (load_config().get("upload_base_url") or "").rstrip("/")
    if not base_url:
        raise ValueError("upload_base_url missing in fb_config.json")

    req = urllib.request.Request(
        f"{base_url}/bulk_spend_upload/",
        data=json.dumps({"rows": rows}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = {"text": text}
            return {"success": 200 <= resp.status < 300, "status_code": resp.status, "data": data}
    except urllib.error.HTTPError as exc:
        return {
            "success": False,
            "status_code": exc.code,
            "error": exc.read().decode("utf-8", errors="replace"),
        }
    except urllib.error.URLError as exc:
        return {"success": False, "error": str(exc)}


def sync_facebook_spend_by_bjt_day(bjt_day: str, dry_run: bool = False) -> dict[str, Any]:
    rows, unknown_ads = fetch_facebook_spend_by_bjt_day(bjt_day)
    if dry_run:
        upload_result = {"success": True, "dry_run": True}
        uploaded_rows = 0
    elif rows:
        upload_result = upload_rows_bulk(rows)
        uploaded_rows = len(rows) if upload_result.get("success") else 0
    else:
        upload_result = {"success": True, "message": "No rows to upload"}
        uploaded_rows = 0

    return {
        "stat_date": bjt_day,
        "fetched_rows": len(rows) + len(unknown_ads),
        "aggregated_rows": len(rows),
        "uploaded_rows": uploaded_rows,
        "rows": rows,
        "unknown_ads": unknown_ads,
        "upload_result": upload_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Facebook Ads spend and upload it.")
    parser.add_argument("date", help="Beijing date, YYYY-MM-DD.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and aggregate without upload.")
    args = parser.parse_args()

    try:
        result = sync_facebook_spend_by_bjt_day(args.date, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("upload_result", {}).get("success") else 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
