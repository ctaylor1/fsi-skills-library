"""Exact legacy continuity parity and independent arithmetic examples."""
import copy,json,os,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CURRENT=ROOT/'skills/investment-research/model-roll-forward-auditor'
ARCHIVE=ROOT/'docs/investment-research/phase2-validation/legacy-auditor'
REVIEWER=ROOT/'skills/investment-research/research-financial-model-reviewer'
def old():return CURRENT if CURRENT.exists() else ARCHIVE
def calculate(package,document):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    proc=subprocess.run([sys.executable,'-B',str(package/'scripts/calculate_or_transform.py')],input=json.dumps(document),text=True,capture_output=True,env=env)
    if proc.returncode:raise ValueError(proc.stdout+proc.stderr)
    return json.loads(proc.stdout)
def example():return json.loads((old()/'evals/files/model_example.json').read_text())

class ReviewerParity(unittest.TestCase):
    def test_exact_legacy_output_and_independent_expected_residuals(self):
        original=example();cases=[(100,100,0,'tied',0),(100,100.4,0.5,'tied',0.4),(100,100.6,0.5,'break',0.6),(100,100.0000001,0,'tied',0),(-10,-9,0,'break',1),(None,10,0,'structural_break',None),(10,None,0,'structural_break',None)]
        for prior,current,tolerance,status,residual in cases:
            with self.subTest(prior=prior,current=current,tolerance=tolerance):
                doc=copy.deepcopy(original);doc['roll_forward']=[{'line_item':'cash','prior_ending':prior,'current_opening':current,'tolerance':tolerance}]
                expected=calculate(old(),doc);reviewed=calculate(REVIEWER,{'mode':'legacy-roll-forward','input':doc})
                self.assertEqual(expected,reviewed['legacy_result'])
                self.assertEqual(status,expected['line_items'][0]['tie_status'])
                self.assertEqual(residual,expected['line_items'][0]['residual'])
                self.assertFalse(reviewed['authority_granted'])
    def test_exact_full_original_inventory_parity(self):
        source=example();self.assertEqual(calculate(old(),source),calculate(REVIEWER,{'mode':'legacy-roll-forward','input':source})['legacy_result'])
    def test_legacy_invalid_shapes_and_financial_booleans_fail(self):
        for source in (None,[],{}, {'model':{}}, {**example(),'roll_forward':[{'line_item':'cash','prior_ending':True,'current_opening':1,'tolerance':0}]}):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):calculate(old(),source)
                with self.assertRaises(ValueError):calculate(REVIEWER,{'mode':'legacy-roll-forward','input':source})
if __name__=='__main__':unittest.main()
