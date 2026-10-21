#!/usr/bin/env python3
"""Validate a native handoff against a trusted installed package; no business action."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from insurance_contract import validate_handoff as validate_insurance_handoff

_spec = importlib.util.spec_from_file_location(
    'insurance_router_workflow_contract', Path(__file__).with_name('workflow_contract.py'))
_workflow_contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_workflow_contract)
validate_workflow_handoff = _workflow_contract.validate_handoff


def check(packet, skills_root):
    if not isinstance(packet, dict):
        return ['handoff must be an object']
    target = packet.get('target_skill')
    if not isinstance(target, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', target):
        return ['invalid target skill name']
    root = Path(skills_root).resolve()
    matches = [p.parent for p in root.glob(f'*/{target}/SKILL.md')]
    # Also support a standalone installed collection with no category layer.
    if (root / target / 'SKILL.md').is_file():
        matches.append(root / target)
    if len(matches) != 1:
        return ['target must resolve to exactly one installed package']
    package = matches[0].resolve()
    script = (package / 'scripts/validate_input.py').resolve()
    if not package.is_relative_to(root) or not script.is_relative_to(package) or not script.is_file():
        return ['trusted native receiver input validator unavailable']

    def receiver(native):
        with tempfile.TemporaryDirectory(prefix='insurance-handoff-') as directory:
            source = Path(directory) / 'input.json'
            source.write_text(json.dumps(native, allow_nan=False))
            result = subprocess.run([sys.executable, str(script), str(source)],
                                    cwd=package, capture_output=True, text=True, timeout=30)
        if result.returncode:
            return ['native input rejected: ' + (result.stdout + result.stderr).strip()[:3000]]
        return []

    validator = (validate_workflow_handoff if packet.get('contract_version') == 'workflow-evidence/1.0'
                 else validate_insurance_handoff)
    return validator(packet, target_skill=target, receiver_validator=receiver)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet')
    parser.add_argument('--skills-root', required=True, help='trusted installed skills directory')
    args = parser.parse_args()
    try:
        errors = check(json.loads(Path(args.packet).read_text()), args.skills_root)
    except (ValueError, OSError) as exc:
        errors = [str(exc)]
    print(json.dumps({'native_input_validation': 'failed' if errors else 'passed',
                      'errors': errors, 'authority_granted': False,
                      'professional_acceptance': 'not_established'}, indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
