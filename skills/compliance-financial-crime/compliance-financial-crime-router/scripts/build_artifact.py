"""Wrap a producer-validated native result for internal review; writes only stdout."""
import argparse
import json
from pathlib import Path
from cfc_contract import build_packet
from native_runner import native_validate, package_name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--native-output', required=True)
    parser.add_argument('--producer-package', required=True)
    args = parser.parse_args()
    try:
        source = json.loads(Path(args.input).read_text())
        output = json.loads(Path(args.native_output).read_text())
        result = build_packet(source, output, producer=package_name(args.producer_package),
            native_validator=lambda out, original: native_validate(args.producer_package, out, original))
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
