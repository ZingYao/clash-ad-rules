"""先上传完整草稿，再发布 latest；失败不影响上一正式订阅。"""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def main():
    stats = json.loads(Path("build/ads.stats.json").read_text())
    previous_file = Path("previous/stats.json")
    if previous_file.exists():
        previous = json.loads(previous_file.read_text())
        if all(stats[key] == previous.get(key) for key in ["mrs_sha256", "yaml_sha256"]):
            print("Rules unchanged; keeping the current release.")
            return
    Path("build/stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n")
    assets = [Path("build/ads.mrs"), Path("build/ads.yaml"), Path("build/stats.json")]
    checksums = "".join(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.name + "\n" for path in assets)
    Path("build/SHA256SUMS").write_text(checksums)
    assets.append(Path("build/SHA256SUMS"))
    notes = "\n".join([
        "公开广告规则三源合并，精确去重及父域覆盖去重，原始匹配并集已验证。",
        "", "- 输入：" + str(stats["input_entries"]),
        "- 输出：" + str(stats["output_entries"]),
        "- 完全重复移除：" + str(stats["exact_duplicates_removed"]),
        "- 父域覆盖冗余移除：" + str(stats["parent_covered_patterns_removed"]),
        "- 生成时间：" + stats["generated_at"],
        "", "来源、许可证及更新方法见仓库 README 和 THIRD-PARTY-NOTICES.md。", "",
    ])
    Path("build/release-notes.md").write_text(notes)
    tag = "rules-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + os.environ["GITHUB_RUN_ID"] + "-" + os.environ["GITHUB_RUN_ATTEMPT"]
    subprocess.run(["gh", "release", "create", tag, *map(str, assets), "--draft", "--target", os.environ["GITHUB_SHA"], "--title", tag, "--notes-file", "build/release-notes.md"], check=True)
    release = json.loads(subprocess.check_output(["gh", "release", "view", tag, "--json", "assets"], text=True))
    uploaded = {item["name"]: item["size"] for item in release["assets"]}
    if any(uploaded.get(path.name) != path.stat().st_size for path in assets):
        raise RuntimeError("Draft release assets are incomplete; keeping the previous release")
    subprocess.run(["gh", "release", "edit", tag, "--draft=false", "--latest"], check=True)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as output:
            output.write(notes + "\nPublished: " + tag + "\n")


if __name__ == "__main__":
    main()
