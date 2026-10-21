"""Invoke explicitly selected installed native validators; no workflow execution."""
from __future__ import annotations
import json,re,subprocess,sys,tempfile
from pathlib import Path


def package_name(package):
    package=Path(package).resolve()
    match=re.search(r'^name:\s*([a-z0-9-]+)\s*$',(package/'SKILL.md').read_text(),re.M)
    if not match or match.group(1)!=package.name:raise ValueError('invalid installed package identity')
    return match.group(1)


def native_validate(package, data, original_input=None):
    package=Path(package).resolve();package_name(package)
    script=package/'scripts'/('validate_output.py' if original_input is not None else 'validate_input.py')
    if not script.is_file():return ['installed package has no native validator']
    with tempfile.TemporaryDirectory(prefix='investment-native-review-') as tmp:
        root=Path(tmp);value=root/'value.json';value.write_text(json.dumps(data,allow_nan=False))
        args=[sys.executable,'-B',str(script),str(value)]
        if original_input is not None:
            source=root/'input.json';source.write_text(json.dumps(original_input,allow_nan=False))
            args += ['--input',str(source)]
        try:result=subprocess.run(args,cwd=package,capture_output=True,text=True,timeout=30)
        except subprocess.TimeoutExpired:return ['native validator timeout; no retry or fallback']
        if result.returncode:return ['native validator rejected artifact: '+(result.stdout+result.stderr)[:2000]]
    return []
