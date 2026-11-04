# 开发分支登记

| 需求 | 原始问题 | 仓库 | 开发分支 | 工作目录 | 状态 |
|---|---|---|---|---|---|
| 三源广告规则合并去重与自动订阅 | 用户于 2026-11-04 要求使用 GitHub 托管去重订阅；原始来源为本次对话，无外部工单链接 | ZingYao/clash-ad-rules | zing/feature/deduplicated-ad-subscription | outputs/clash-ad-rules | 开发和本地验证中 |

这是全新空仓库，没有已有功能分支、worktree 或 main/master 基线。首次提交在上述功能分支初始化；完成验证后建立 main 发布基线，不在 main 直接提交业务代码。后续同一需求修正继续复用上述分支。

验收：三源拉取完整、匹配并集覆盖检查、精确与父域去重测试、异常缩减保护、MRS 转换、Actions 首次发布及固定下载地址、手机加载并命中拦截。

回滚：手机切回原 adsmrs.js 三源官方 MRS 覆写；GitHub 下载/校验/编译失败不发布新版本。旧 Release 保留。
