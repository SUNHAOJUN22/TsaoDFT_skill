#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("files", nargs="+", type=Path)
a = p.parse_args()
print(
    json.dumps(
        [
            {"path": str(x), "bytes": x.stat().st_size, "sha256": hashlib.sha256(x.read_bytes()).hexdigest()}
            for x in a.files
        ],
        indent=2,
    )
)
