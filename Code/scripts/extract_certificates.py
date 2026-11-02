"""Export nested self-contained point, contradiction and bound artifacts."""
import argparse
import json
from pathlib import Path

from witness3d.io import atomic_json


def walk(value):
    if isinstance(value, dict):
        if "system" in value and "certificate" in value:
            yield value
        else:
            for child in value.values():
                yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("records")
    p.add_argument("output")
    args = p.parse_args()
    count = 0
    for line in Path(args.records).read_text().splitlines():
        for artifact in walk(json.loads(line)):
            atomic_json(Path(args.output) / f"{count:06d}.json", artifact)
            count += 1
    print(f"Exported {count} artifacts")

