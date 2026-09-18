# Meta Campaign 配置备份

来源：Meta Ads Manager 批量导出 `export_20260918_1953.xlsx`

广告账户：`act_1761778028299301`

## 层级

- Campaign：`120249543819510430`
- Campaign 名称：`KP_ios_AI iPhone Storage Cleaner_Tyler_0901`
- Ad Set：`120249543819490430`
- Ad Set 名称：`0901`
- Ads：31 条，其中 30 条 ACTIVE，1 条 PAUSED
- 素材类型：20 条 Video Page Post Ad，11 条 Link Page Post Ad

## 主要投放配置

- 目标：应用推广（API 对应值需在创建时按当前 Graph API 版本确认）
- 购买类型：AUCTION
- Campaign 日预算：300 账户币种单位
- Campaign 出价策略：Highest volume or value
- 优化事件：PURCHASE
- 优化目标：OFFSITE_CONVERSIONS
- 计费事件：IMPRESSIONS
- 归因窗口：7-day click
- 国家：US
- 年龄：18-65
- 设备：iPad、iPhone、iPod
- 系统：iOS 14.0 及以上
- App ID：`3357661051060397`
- App Store：`https://itunes.apple.com/app/id6756252243`
- Page/Link Object ID：`105002011916079`
- Instagram Account ID：`4381770001919066`
- CTA：INSTALL_MOBILE_APP

## 文件

- `campaign_template.json`：Campaign 和 Ad Set 的可复用配置及创建注意事项。
- `creative_inventory.json`：31 条广告的文案、素材 ID、文件名和预览链接。
- `raw_non_empty_rows.json`：原始 422 列中每行所有非空字段，作为完整恢复依据。
- `export_20260918_1953.xlsx`：未经修改的原始导出。

## 创建注意事项

- 新 Campaign 默认先创建为 `PAUSED`，检查无误后再启用。
- API 的预算通常使用账户币种最小单位。创建前必须确认账户币种和 `300` 的换算值。
- 导出中的版位字段为空，通常表示自动版位；创建前应再次确认。
- Excel 不含图片或视频原文件。素材 ID 仅可在有源广告账户权限时复用或下载。
- 当前 AWD Ops token 尚未获得此广告账户权限，因此暂时不能通过 API 下载素材或直接克隆 Campaign。
