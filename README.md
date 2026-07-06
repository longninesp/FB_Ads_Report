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
