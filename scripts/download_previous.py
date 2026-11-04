"""读取上一正式 Release 的统计；仅无 Release 的 404 允许首次构建。"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path


def main():
    repository = os.environ["GITHUB_REPOSITORY"]
    headers = {"Authorization": "Bearer " + os.environ["GH_TOKEN"], "User-Agent": "clash-ad-rules"}
    request = urllib.request.Request("https://api.github.com/repos/" + repository + "/releases/latest", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print("No published release yet; applying first-build minimum thresholds.")
            return
        raise
    asset = next(item for item in release["assets"] if item["name"] == "stats.json")
    with urllib.request.urlopen(asset["browser_download_url"], timeout=30) as response:
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError("Previous statistics exceed size limit")
    json.loads(raw)
    Path("previous").mkdir(exist_ok=True)
    Path("previous/stats.json").write_bytes(raw)


if __name__ == "__main__":
    main()
