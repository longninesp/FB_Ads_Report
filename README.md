# FB Ads Report

Meta/Facebook Marketing API reporting tools for Aquawood ad operations.

This project is intended to run on the shanshui MCC server:

```bash
ssh -F "/Users/winsmile/Documents/Codex Sandbox/程序开发/shanshui mcc/ssh_config" shanshui-mcc
cd /home/weina/FB_Ads_Report
```

## Configuration

The tool reads credentials from `.env` or environment variables.

Required:

- `META_ACCESS_TOKEN`

Defaults:

- `META_AD_ACCOUNT_ID=act_1594070645652115`
- `META_GRAPH_VERSION=v23.0`

`.env` is intentionally excluded from git.

## Commands

Account info:

```bash
./fb_ads_report.py account
```

Campaigns:

```bash
./fb_ads_report.py campaigns
```

Insights for one date:

```bash
./fb_ads_report.py insights --date 2026-07-06 --level campaign
```

Insights for a date range:

```bash
./fb_ads_report.py insights --since 2026-07-01 --until 2026-07-06 --level campaign --time-increment 1
```

Token / access diagnostic:

```bash
./fb_ads_report.py diagnose
```

## Spend Upload

Facebook spend upload follows the same server contract as the Flex `UA`
Applovin uploader:

```json
{
  "rows": [
    {
      "stat_date": "2026-07-06",
      "package_name": "com.aquawood.cleaner",
      "media_source_code": "facebook",
      "installs": 0,
      "spend": 41.05
    }
  ]
}
```

Run a dry run:

```bash
./fetch_facebook.py 2026-07-06 --dry-run
```

Fetch and upload:

```bash
./fetch_facebook.py 2026-07-06
```

The upload endpoint is `http://47.253.53.210:9000/bulk_spend_upload/`.
If upload times out on shanshui, allow outbound access from the shanshui
server to `47.253.53.210:9000`; Flex UA can already reach this endpoint.

Daily upload for yesterday and the day before yesterday:

```bash
./fb_daily.sh
```

`fb_daily.sh` uploads the last 4 completed Beijing-calendar days:
yesterday, 2 days ago, 3 days ago, and 4 days ago. This allows late Meta
conversion attribution to correct recent rows through normal upserts.

Cron template:

```cron
36 6 * * * /usr/bin/flock -n /tmp/fb_ads_report.lock /home/weina/FB_Ads_Report/fb_daily.sh > /home/weina/FB_Ads_Report/run_fb_daily.log 2>&1
```
