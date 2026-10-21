"""Build/verify the two registered review projections using installed validators."""
import argparse
import json
from pathlib import Path
from native_runner import package_name, native_validate
from review_projection import build_review_projection, validate_review_projection
from foundation_contract import _read
from native_integrity import canonical_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-package', required=True, type=Path)
    parser.add_argument('--receiver-package', required=True, type=Path)
    parser.add_argument('--source-input', required=True, type=Path)
    parser.add_argument('--source-packet', required=True, type=Path)
    parser.add_argument('--target-input', required=True, type=Path)
    parser.add_argument('--mappings', required=True, type=Path)
    parser.add_argument('--projection-basis', required=True, type=Path)
    parser.add_argument('--supplemental', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    def read(path):
        return _read(path)
    producer = package_name(args.source_package)
    target = package_name(args.receiver_package)
    original = read(args.source_input)
    packet = read(args.source_packet)
    target_input = read(args.target_input)
    mappings = read(args.mappings)
    basis = read(args.projection_basis)
    supplemental = read(args.supplemental) if args.supplemental else {}
    kwargs = dict(producer=producer, target_skill=target,
                  producer_validator=lambda output, doc: native_validate(args.source_package, output, doc),
                  receiver_validator=lambda doc: native_validate(args.receiver_package, doc),
                  supplemental_inputs=supplemental)
    expected = build_review_projection(packet, original, target_input,
                                      mappings=mappings, projection_basis=basis, **kwargs)
    if args.verify:
        supplied = read(args.verify)
        errors = validate_review_projection(supplied, original, **kwargs)
        # Verify against the separately supplied target/mappings/basis as well.
        if canonical_hash(supplied) != canonical_hash(expected):
            errors.append('projection differs from separately supplied review inputs')
        print(json.dumps({'errors': errors, 'authority_granted': False}, indent=2))
        return int(bool(errors))
    print(json.dumps(expected, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({'errors': [str(exc)], 'authority_granted': False}))
        raise SystemExit(1)
