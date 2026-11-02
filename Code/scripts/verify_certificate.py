"""Standalone arithmetic verification. Future execution only."""
import argparse
import json
from pathlib import Path

from witness3d.verify import check_artifact

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact")
    args = parser.parse_args()
    result = check_artifact(json.loads(Path(args.artifact).read_text()))
    print(json.dumps({"accepted": result.accepted, "reason": result.reason, "value": str(result.value)}))
    raise SystemExit(0 if result.accepted else 1)

