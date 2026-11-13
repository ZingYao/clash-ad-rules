#!/usr/bin/env python3
"""合并三个广告域名库，保留匹配语义，原子生成去重快照；不修改手机配置。"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCES = {
    "antiad": "https://anti-ad.net/clash.yaml",
    "awads": "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-Clash-Only.Ads.yaml",
    "217heidai": "https://github.com/217heidai/adblockfilters/releases/download/rule/adblockmihomo.yaml",
}
MINIMUM_ENTRIES = {"antiad": 50000, "awads": 100, "217heidai": 100000}


def parse_payload(content):
    """仅接受本次三源使用的简单 YAML 域名列表，遇到新语法时停止生成。"""
    rules = []
    for line in content.splitlines():
        value = line.strip()
        if not value or value.startswith("#") or value == "payload:":
            continue
        if not value.startswith("- "):
            raise ValueError("出现未支持的 YAML 结构，保留旧快照")
        value = value[2:].strip()
        if value.startswith(("'", '"')):
            if value[-1] != value[0]:
                raise ValueError("域名字符串引号不完整")
            value = value[1:-1]
        if not value or any(char.isspace() for char in value) or any(char in value for char in "*#,!/\\"):
            raise ValueError("出现需要专门处理的新规则语法：" + value)
        domain = value[2:] if value.startswith("+.") else value
        if not re.fullmatch(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+", domain):
            raise ValueError("出现未支持的域名语法：" + value)
        rules.append(value.lower())
    if not rules:
        raise ValueError("规则列表为空，保留旧快照")
    return rules


def ancestors(domain):
    """按当前域名及父域枚举；不对字符串做包含匹配。"""
    labels = domain.split(".")
    return (".".join(labels[index:]) for index in range(len(labels)))


def compact(rules):
    """仅消除同动作规则的精确重复和可证明被父域覆盖的条目。"""
    unique = set(rules)
    suffix = {rule[2:] for rule in unique if rule.startswith("+.")}
    subdomain = {rule[1:] for rule in unique if rule.startswith(".") and not rule.startswith("+.")}
    exact = unique - {"+." + domain for domain in suffix} - {"." + domain for domain in subdomain}
    if subdomain:
        raise ValueError("出现仅子域匹配语法，需要先补充等价验证")
    retained_suffix = {domain for domain in suffix if not any(parent in suffix for parent in list(ancestors(domain))[1:])}
    retained_exact = {domain for domain in exact if not any(parent in suffix for parent in ancestors(domain))}
    output = sorted({"+." + domain for domain in retained_suffix} | retained_exact)
    for original in unique:
        domain = original[2:] if original.startswith("+.") else original
        covered = any(parent in retained_suffix for parent in ancestors(domain))
        if not covered and (original.startswith("+.") or domain not in retained_exact):
            raise AssertionError("覆盖验证失败：" + original)
    return output, {"input_entries": len(rules), "unique_exact_patterns": len(unique), "exact_duplicates_removed": len(rules) - len(unique), "parent_covered_patterns_removed": len(unique) - len(output), "output_entries": len(output), "coverage_checked_patterns": len(unique)}


def check_counts(sources, output_count, previous=None):
    """源缺失、条目过少或相对上一版缩减超过 30% 时中止发布。"""
    counts = {name: len(rules) for name, _, rules in sources}
    if set(counts) != set(SOURCES):
        raise ValueError("广告源不完整，保留上一版")
    for name, count in counts.items():
        if count < MINIMUM_ENTRIES[name]:
            raise ValueError(name + " 条目低于最低阈值，保留上一版")
        if previous and count < previous["sources"][name]["entries"] * .7:
            raise ValueError(name + " 条目比上一版减少超过 30%，保留上一版")
    if previous and output_count < previous["output_entries"] * .7:
        raise ValueError("合并结果比上一版减少超过 30%，保留上一版")


def shadowrocket_rules(domains):
    """保留精确与后缀匹配，拦截策略由引用此文件的 RULE-SET 指定。"""
    for domain in domains:
        if domain.startswith("+."):
            yield f"DOMAIN-SUFFIX,{domain[2:]}\n"
        else:
            yield f"DOMAIN,{domain}\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, help="使用已下载的 antiad.yaml、awads.yaml、217heidai.yaml")
    parser.add_argument("--mihomo", type=Path, help="可选：同时编译 MRS")
    parser.add_argument("--previous-stats", type=Path, help="上一发布版本的 stats.json，用于异常缩减检查")
    args = parser.parse_args()

    def fetch(source):
        if args.source_dir:
            raw = (args.source_dir / (source + ".yaml")).read_bytes()
        else:
            for attempt in range(3):
                try:
                    request = urllib.request.Request(SOURCES[source], headers={"User-Agent": "clash-ad-rules/1.0"})
                    with urllib.request.urlopen(request, timeout=30) as response:
                        raw = response.read(20 * 1024 * 1024 + 1)
                    break
                except (OSError, TimeoutError):
                    if attempt == 2:
                        raise
                    time.sleep(2 ** (attempt + 1))
            if len(raw) > 20 * 1024 * 1024:
                raise ValueError("源文件超出 20 MiB 上限")
        return source, raw, parse_payload(raw.decode("utf-8-sig"))

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        sources = list(executor.map(fetch, SOURCES))
    merged, stats = compact([rule for _, _, rules in sources for rule in rules])
    previous = json.loads(args.previous_stats.read_text()) if args.previous_stats else None
    check_counts(sources, len(merged), previous)
    stats["generated_at"] = datetime.now(timezone.utc).isoformat()
    stats["sources"] = {name: {"url": SOURCES[name], "entries": len(rules), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()} for name, raw, rules in sources}
    text = "# Generated three-source union; source hashes and statistics are in stats.json.\npayload:\n" + "".join("  - '" + rule + "'\n" for rule in merged)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # 下载、覆盖验证和可选编译全部成功后才替换快照；单个文件使用同盘原子替换。
    with tempfile.TemporaryDirectory(prefix=".ad-rules-", dir=args.output.parent) as staging:
        temporary = Path(staging) / "rules.yaml"
        temporary.write_text(text, encoding="utf-8")
        pending = [(temporary, args.output)]
        if args.mihomo:
            temporary_mrs = Path(staging) / "rules.mrs"
            subprocess.run([str(args.mihomo), "convert-ruleset", "domain", "yaml", str(temporary), str(temporary_mrs)], check=True)
            stats["mrs_bytes"] = temporary_mrs.stat().st_size
            stats["mrs_sha256"] = hashlib.sha256(temporary_mrs.read_bytes()).hexdigest()
            pending.append((temporary_mrs, args.output.with_suffix(".mrs")))
        stats["yaml_bytes"] = temporary.stat().st_size
        stats["yaml_sha256"] = hashlib.sha256(temporary.read_bytes()).hexdigest()
        temporary_list = Path(staging) / "shadowrocket.list"
        with temporary_list.open("w", encoding="utf-8", newline="\n") as output:
            output.writelines(shadowrocket_rules(merged))
        stats["shadowrocket_bytes"] = temporary_list.stat().st_size
        stats["shadowrocket_sha256"] = hashlib.sha256(temporary_list.read_bytes()).hexdigest()
        pending.append((temporary_list, args.output.with_suffix(".list")))
        temporary_stats = Path(staging) / "stats.json"
        temporary_stats.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        pending.append((temporary_stats, args.output.with_suffix(".stats.json")))
        for staged, destination in pending:
            staged.replace(destination)
    print(json.dumps({key: value for key, value in stats.items() if key != "sources"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
