# 开发分支登记

| 需求 | 原始问题 | 仓库 | 开发分支 | 工作目录 | 状态 |
|---|---|---|---|---|---|
| 三源广告规则合并去重与自动订阅 | 用户于 2026-11-04 要求使用 GitHub 托管去重订阅；原始来源为本次对话，无外部工单链接 | ZingYao/clash-ad-rules | zing/feature/deduplicated-ad-subscription | outputs/clash-ad-rules | 已交付：自动发布与手机拦截验收通过 |

这是全新空仓库，没有已有功能分支、worktree 或 main/master 基线。首次提交在上述功能分支初始化；完成验证后建立 main 发布基线，不在 main 直接提交业务代码。后续同一需求修正继续复用上述分支。

验收：三源拉取完整、匹配并集覆盖检查、精确与父域去重测试、异常缩减保护、MRS 转换、Actions 首次发布及固定下载地址、手机加载并命中拦截。

回滚：手机切回原 adsmrs.js 三源官方 MRS 覆写；GitHub 下载/校验/编译失败不发布新版本。旧 Release 保留。

首次交付：功能提交 a46ea6d；main 基线与该提交一致。Actions 41791099546 测试及发布成功，Release rules-20261104T071636Z-41791099546-1。手机合并源 zing-ad-union 已加载 270,058 条 MRS，红果、通用及游戏广告命中 REJECT；国内网站 HTTP 200。未 add 的 Go 文件：无。

后续验收修正：沿用原功能分支，将 checkout 升级到固定 SHA 的 v6，消除 Actions 的 Node.js 20 弃用提示，并复验读取上一版及内容不变跳过发布。

最终验收：功能及 CI 提交 63be06a 已快进合并 main。功能分支 Actions 41791496969 通过，main Actions 41791740567 的 test 和 publish 全部成功；发布日志确认 Rules unchanged; keeping the current release，已验证读取上一版及无变化跳过重复发布。手机使用 adsunion.js（16037509.js），单一 zing-ad-union MRS 源每 21,600 秒更新；结束时 VPN 保持连接、原节点选择恢复、虚拟屏与临时转发关闭。未 add 的 Go 文件：无。

2026-11-14 兼容性扩展：用户要求生成小火箭订阅链接，沿用原功能分支。提交 9ca593c 已快进合并 main。功能分支 Actions 43482075819 测试通过，main Actions 43482274785 测试和发布通过。固定 ads.list 链接实测可下载，279,389 条规则和同版 YAML 逐条一致，SHA-256 校验通过。未在 iPhone 上实测。未 add 的 Go 文件：无。

2026-11-14 直连配置：沿用原功能分支，提供 Shadowrocket 可从 URL 新增的配置。命中同一个 ads.list 时拦截，其余直连，使用系统 DNS。配置结构和远程规则地址已校验，iPhone 实机验证待用户导入。未 add 的 Go 文件：无。

2026-11-14 下载中断排查：沿用原功能分支，提交 cf9a4a1 已合并 main。Actions 43490213525 构建及同步成功，shadowrocket 发布分支由同一工作流维护。jsDelivr 配置和规则均返回 HTTP 200、零跳转，279,389 条规则的 SHA-256 与 Release 一致。iPhone 所用香港线路尚未实测。未 add 的 Go 文件：无。
