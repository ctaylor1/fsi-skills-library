"""Build/check a source-bound handoff using explicitly installed native validators."""
import argparse
import json
from pathlib import Path
from cfc_contract import build_handoff, validate_handoff
from native_runner import native_validate, package_name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet')
    parser.add_argument('--source-input', required=True)
    parser.add_argument('--source-package', required=True)
    parser.add_argument('--target-package', required=True)
    parser.add_argument('--supplemental-inputs')
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    try:
        packet = json.loads(Path(args.packet).read_text())
        source = json.loads(Path(args.source_input).read_text())
        supplemental = json.loads(Path(args.supplemental_inputs).read_text()) if args.supplemental_inputs else {}
        kwargs = dict(producer=package_name(args.source_package), target_skill=package_name(args.target_package),
            producer_validator=lambda out, original: native_validate(args.source_package, out, original),
            receiver_validator=lambda doc: native_validate(args.target_package, doc), supplemental_inputs=supplemental)
        if args.build:
            result = build_handoff(packet['source_packet'], source, packet['target_input'],
                                  mappings=packet['mappings'], **kwargs)
        else:
            errors = validate_handoff(packet, source, **kwargs)
            result = {'errors': errors, 'authority_granted': False}
            if errors:
                print(json.dumps(result)); return 1
        print(json.dumps(result, indent=2, allow_nan=False)); return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
