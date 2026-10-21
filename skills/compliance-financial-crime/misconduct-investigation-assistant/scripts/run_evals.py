"""Executable frozen native fixtures and behavioral regressions."""
import json
from pathlib import Path
import subprocess
import sys
from domain import compute
from validate_output import validate
base=Path(__file__).resolve().parents[1]/'evals/files'
source=json.loads((base/'input_complete.json').read_text())
golden=json.loads((base/'output_golden.json').read_text())
assert compute(source)==golden, 'frozen golden differs'
assert validate(golden,source)==[], 'golden invalid'
assert validate(json.loads((base/'output_bad.json').read_text()),source), 'tamper accepted'
assert compute(json.loads((base/'input_professional_gap.json').read_text()))['status']=='needs-evidence', 'professional gap hidden'
try:
    compute(json.loads((base/'input_bad.json').read_text()))
except ValueError:
    pass
else:
    raise AssertionError('invalid intake produced output')
subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('test_phase2.py'))],check=True)
print('5 frozen native evaluations and domain regressions passed')
