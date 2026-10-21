"""Run explicitly installed native validators in separate processes (MIT)."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def package_name(package):
    root = Path(package).resolve()
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", text, re.M)
    if not match or match.group(1) != root.name:
        raise ValueError("installed package name must match SKILL.md")
    return root.name


def native_validate(package, document, original_input=None):
    root = Path(package).resolve()
    package_name(root)
    validator = root / "scripts" / ("validate_input.py" if original_input is None else "validate_output.py")
    if not validator.is_file():
        return ["installed native validator unavailable"]
    if original_input is not None:
        source_errors = native_validate(root, original_input)
        if source_errors:
            return ["producer original input: " + error for error in source_errors]
    with tempfile.TemporaryDirectory(prefix="cfc-native-") as temp:
        path = Path(temp) / "document.json"
        path.write_text(json.dumps(document, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        command = [sys.executable, "-B", str(validator), str(path)]
        if original_input is not None:
            original = Path(temp) / "original.json"
            original.write_text(json.dumps(original_input, ensure_ascii=False, allow_nan=False), encoding="utf-8")
            command += ["--input", str(original)]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30)
    if result.returncode:
        return ["native validator rejected document: " + (result.stdout + result.stderr).strip()]
    return []
