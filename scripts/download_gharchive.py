"""Download and decompress a single GH Archive hourly dataset file.

Defaults to this project's fixed dataset hour (see README.md), but any
date/hour can be requested for exploration.

Usage:
    python scripts/download_gharchive.py
    python scripts/download_gharchive.py --date 2026-08-27 --hour 15
"""

import argparse
import gzip
import shutil
import urllib.request
from pathlib import Path

DEFAULT_DATE = "2026-08-27"
DEFAULT_HOUR = 15

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def download(date: str, hour: int, data_dir: Path = DATA_DIR) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{date}-{hour}.json.gz"
    url = f"https://data.gharchive.org/{filename}"
    gz_path = data_dir / filename

    print(f"Downloading {url} ...")
    # GH Archive's server rejects requests whose User-Agent header looks
    # like a script (urllib's default is "Python-urllib/x.y"), so we set
    # a browser-like one explicitly. urlretrieve() doesn't allow custom
    # headers, so we build the request manually with urlopen() instead.
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request) as response, open(gz_path, "wb") as f_out:
        shutil.copyfileobj(response, f_out)
    print(f"Saved to {gz_path}")

    json_path = gz_path.with_suffix("")
    print(f"Decompressing to {json_path} ...")
    with gzip.open(gz_path, "rb") as f_in, open(json_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    print(f"Done: {json_path}")

    return json_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        default=DEFAULT_DATE,
        help=f"Date in YYYY-MM-DD format (default: {DEFAULT_DATE})",
    )
    parser.add_argument(
        "--hour",
        type=int,
        default=DEFAULT_HOUR,
        choices=range(0, 24),
        metavar="[0-23]",
        help=f"UTC hour, 0-23 (default: {DEFAULT_HOUR})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    download(args.date, args.hour)


if __name__ == "__main__":
    main()
