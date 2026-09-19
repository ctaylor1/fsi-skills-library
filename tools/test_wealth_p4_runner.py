"""P4 runtime evidence checks using a local fake process; no model/API calls."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from run_wealth_p4_models import execute, import_record


class ModelRunEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='p4-runner-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.condition = self.root / 'CASE--with-skill'
        self.condition.mkdir()
        (self.condition / 'prompt.txt').write_text('SYNTHETIC TEST')
        self.binary = self.root / 'fake-codex'
        self.binary.write_text(f'''#!{sys.executable}
import json, pathlib, sys, time
args = sys.argv
prompt = sys.stdin.read()
print(json.dumps({{"type":"thread.started","thread_id":"fresh-session"}}), flush=True)
if prompt == 'TIMEOUT':
    time.sleep(10)
if prompt != 'NO_RESPONSE':
    pathlib.Path(args[args.index('-o')+1]).write_text('Retained initial draft.\\n')
if prompt == 'FAILED':
    print(json.dumps({{"type":"turn.failed","error":{{"message":"runtime failure"}}}}))
    sys.exit(1)
if prompt == 'MALFORMED':
    print('broken event')
pathlib.Path('working-note.txt').write_text('Synthetic local work')
print(json.dumps({{"type":"turn.completed","usage":{{"input_tokens":9,"output_tokens":5}}}}))
''')
        self.binary.chmod(0o700)

    def run_condition(self, prompt='SYNTHETIC TEST', timeout=3):
        (self.condition / 'prompt.txt').write_text(prompt)
        return execute(self.condition, self.root / 'out', str(self.binary), 'fake-model', 'high', timeout, 'fake-runtime')

    def test_completed_turn_retains_ungraded_initial_evidence_and_generated_files(self):
        result = self.run_condition()
        self.assertEqual(result['status'], 'completed-ungraded')
        self.assertTrue(result['initial_response_only'])
        self.assertEqual(result['session_ids'], ['fresh-session'])
        self.assertEqual(result['usage'][0]['output_tokens'], 5)
        saved = self.root / 'out' / self.condition.name
        self.assertEqual((saved / 'response.md').read_text(), 'Retained initial draft.\n')
        self.assertEqual((saved / 'generated/working-note.txt').read_text(), 'Synthetic local work')
        self.assertEqual(json.loads((saved / 'runtime.json').read_text())['status'], 'completed-ungraded')
        self.assertFalse((self.condition / 'working-note.txt').exists())

    def test_failed_runtime_cannot_pass_even_with_response(self):
        result = self.run_condition('FAILED')
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(result['turn_failed'])
        self.assertGreater(result['response_bytes'], 0)

    def test_missing_response_cannot_pass_completed_event(self):
        result = self.run_condition('NO_RESPONSE')
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(result['turn_completed'])

    def test_malformed_event_cannot_pass(self):
        result = self.run_condition('MALFORMED')
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(result['event_parse_errors'])

    def test_timeout_is_retained_as_failure(self):
        result = self.run_condition('TIMEOUT', timeout=0.1)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(result['timed_out'])

    def test_initial_run_cannot_be_overwritten(self):
        self.run_condition()
        with self.assertRaises(FileExistsError):
            self.run_condition('FAILED')

    def prepared_runtime(self):
        from wealth_p4_eval import prepare, snapshot
        repo = Path(__file__).resolve().parents[1]
        frozen = self.root / 'snapshot'
        snapshot(repo, frozen)
        for kind in ['cases', 'rubrics']:
            (self.root / kind).mkdir()
            shutil.copy2(repo / 'docs/wealth-management/p4' / kind / 'P4-01.json', self.root / kind / 'P4-01.json')
        experiment = self.root / 'experiment'
        prepare(frozen, self.root / 'cases', self.root / 'rubrics', experiment, 'runner-test')
        condition = experiment / 'conditions/P4-01--without-skill'
        execute(condition, experiment / 'artifacts', str(self.binary), 'fake-model', 'high', 3, 'fake-runtime')
        return experiment, experiment / 'artifacts/P4-01--without-skill/runtime.json'

    def test_import_retains_requested_model_and_unverified_tool_policy_separately(self):
        experiment, runtime = self.prepared_runtime()
        import_record(experiment, runtime)
        record = json.loads((experiment / 'runs/P4-01--without-skill.json').read_text())
        self.assertEqual(record['generator']['model']['availability'], 'unknown')
        self.assertEqual(record['generator']['requested_model']['model_id'], 'fake-model')
        self.assertFalse(record['execution']['isolation']['tool_policy_matched'])
        self.assertEqual(record['attempts'][0]['stage'], 'first-pass')

    def test_import_rejects_response_changed_since_runtime_capture(self):
        experiment, runtime = self.prepared_runtime()
        (runtime.parent / 'response.md').write_text('A substituted answer')
        with self.assertRaisesRegex(ValueError, 'changed after capture'):
            import_record(experiment, runtime)


if __name__ == '__main__':
    unittest.main()
