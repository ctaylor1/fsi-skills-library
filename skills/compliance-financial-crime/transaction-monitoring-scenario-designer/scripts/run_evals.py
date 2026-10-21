"""Frozen executable native expectations, separate from behavioral regression counts."""
import json
from pathlib import Path
from domain import compute
from validate_output import validate
base=Path(__file__).resolve().parents[1]/'evals/files'
def read(name): return json.loads((base/name).read_text())
source=read('input_complete.json'); golden=read('output_golden.json')
assert compute(source)==golden,'frozen complete golden differs'
assert validate(golden,source)==[],'complete golden invalid'
partial=read('input_partial.json'); partial_output=read('output_partial.json')
assert compute(partial)==partial_output and partial_output['status']=='needs-evidence','partial golden differs or unknown hidden'
assert validate(partial_output,partial)==[],'partial golden invalid'
assert validate(read('output_bad.json'),source),'tamper accepted'
try: compute(read('input_bad.json'))
except ValueError: pass
else: raise AssertionError('invalid input produced native result')
print('6 frozen native evaluations passed')
