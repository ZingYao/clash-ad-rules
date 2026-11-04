"""获取固定版本的官方 Linux 编译器，校验压缩包后解压。"""
import gzip
import hashlib
import os
import time
import urllib.request
from pathlib import Path

URL = "https://github.com/MetaCubeX/mihomo/releases/download/v1.19.32/mihomo-linux-amd64-v1-v1.19.32.gz"
SHA256 = "306f81e723e60ce6b828899a6fe83e1d00e9ecefb2dc8d4d849312a5bc00efdc"


def main():
    for attempt in range(3):
        try:
            with urllib.request.urlopen(URL, timeout=60) as response:
                archive = response.read(40 * 1024 * 1024 + 1)
            break
        except (OSError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))
    if len(archive) > 40 * 1024 * 1024 or hashlib.sha256(archive).hexdigest() != SHA256:
        raise ValueError("Mihomo compiler archive SHA-256 mismatch")
    Path("bin").mkdir(exist_ok=True)
    destination = Path("bin/mihomo")
    destination.write_bytes(gzip.decompress(archive))
    os.chmod(destination, 0o755)


if __name__ == "__main__":
    main()
