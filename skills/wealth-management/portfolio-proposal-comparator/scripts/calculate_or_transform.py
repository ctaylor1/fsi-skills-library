#!/usr/bin/env python3
"""Local structured draft workflow; no live integration or external action."""
import json
import sys
from pathlib import Path
from domain import compute


def main(argv):
    path = Path(__file__).resolve().parents[1] / 'evals/files/request_example.json' if '--selftest' in argv else None
    try:
        doc = json.loads(path.read_text() if path else Path(argv[0]).read_text() if argv else sys.stdin.read())
        result = compute(doc)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print('ERROR', exc)
        return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
