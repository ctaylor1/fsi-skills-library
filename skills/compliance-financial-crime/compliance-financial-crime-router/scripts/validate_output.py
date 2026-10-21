"""Verify the complete route plan against its detached original request."""
import argparse
import json
from pathlib import Path
from calculate_or_transform import compute
from native_integrity import validate_reconstruction


def validate(doc, original_input=None):
    errors = []
    validate_reconstruction(doc, compute, errors, original_input=original_input)
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output'); parser.add_argument('--input', required=True)
    args = parser.parse_args()
    try:
        errors = validate(json.loads(Path(args.output).read_text()), json.loads(Path(args.input).read_text()))
    except (ValueError, OSError) as exc:
        errors = [str(exc)]
    for e in errors:
        print('ERROR', e)
    print(f'output validation: {len(errors)} error(s)')
    raise SystemExit(bool(errors))
