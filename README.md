# Clash 广告规则合并订阅

自动合并 antiAD、AWAvenue Only Ads、217heidai 三个公开域名库，保留匹配并集，去除完全重复和已被父域覆盖的冗余条目，发布 Mihomo MRS 与可编辑 YAML。

GitHub Actions 每 6 小时尝试更新一次（UTC 00:27、06:27、12:27、18:27），支持手动运行。内容不变时保留当前 Release。

## 固定订阅地址

- MRS：<https://github.com/ZingYao/clash-ad-rules/releases/latest/download/ads.mrs>
- YAML：<https://github.com/ZingYao/clash-ad-rules/releases/latest/download/ads.yaml>
- 统计与来源哈希：<https://github.com/ZingYao/clash-ad-rules/releases/latest/download/stats.json>
- 校验和：<https://github.com/ZingYao/clash-ad-rules/releases/latest/download/SHA256SUMS>

这是广告规则源，不包含代理节点，须与自己的代理订阅配合使用。仓库仅包含公开规则和构建代码。

## Mihomo 接入

```yaml
rule-providers:
  zing-ad-union:
    type: http
    behavior: domain
    format: mrs
    url: https://github.com/ZingYao/clash-ad-rules/releases/latest/download/ads.mrs
    path: ./ruleset/zing-ad-union.mrs
    interval: 21600

rules:
  - RULE-SET,zing-ad-union,REJECT
  # 后面接原来的分流规则
```

Clash Mi 可导入 `clashmi-ad-union.js`，它保留原代理订阅和分流，在前面加入广告拦截，并保留红果补充域名及嗅探设置。先下载文件，再作为 JS 核心覆写导入，追加覆写选择“内置-覆写”。

## 构建与保护

仅使用 Python 标准库。MRS 使用固定版本、固定 SHA-256 的官方 Mihomo 编译器。

```sh
python3 -m unittest discover -s tests -v
python3 scripts/merge_rules.py --output build/ads.yaml --mihomo /path/to/mihomo
```

三源必须全部获取成功。出现未知语法、条目低于最低阈值、相对上一正式版本减少超过 30%、覆盖验证失败或编译失败时，工作流中止并保留上一正式版本。下载最多重试 3 次。

发布先上传包含全部产物的草稿，检查上传文件齐全，再将它设为最新正式版本；旧 Release 保留，可用于回退。手机号、代理节点、私人订阅地址和访问密钥均不进入仓库。

域名拦截无法区分同一域名下的广告和正常内容；奖励广告被拦截后可能无法领取奖励。白名单、误杀反馈可通过修改上游或暂时关闭拦截处理。

GitHub 定时任务可能延迟，公开仓库长期无活动时也可能自动停用计划运行；可在 Actions 页面查看运行记录并手动恢复。

## 来源

参见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) 和 [LICENSE](LICENSE)。每次 Release 的 stats.json 保留源地址、源文件哈希、条目数和去重统计。
