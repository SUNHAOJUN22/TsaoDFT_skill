#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from utils import sha256_file

p = argparse.ArgumentParser()
p.add_argument("files", nargs="+", type=Path)
a = p.parse_args()
print(
    json.dumps(
        [{"path": str(x), "bytes": x.stat().st_size, "sha256": sha256_file(x)} for x in a.files],
        indent=2,
    )
)
