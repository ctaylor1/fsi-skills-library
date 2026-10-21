"""Source review -> recipient projection -> separate draft review -> byte readback."""
from copy import deepcopy
import contextlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

import test_wealth_p5_evidence as samples
from sync_wealth_quality import PACKAGES, FILES

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared/wealth-quality"))
import audience_gate  # noqa: E402 - explicitly load the shared standalone component.
import quality_gate  # noqa: E402


def inputs():
    candidate, packet, inventory, review = samples.fixture()
    packet["recipients"].append({"recipient_id": "service-n", "kind": "person"})
    packet["sources"][0]["access"]["allowed_recipient_ids"].append("service-n")
    packet["sources"].append({"source_id": "PRIVATE", "reference": "Private note for advisor-n; 2026-10-04",
                              "content": "Possible inheritance is disputed.",
                              "access": {"allowed_recipient_ids": ["advisor-n"], "effective_date": "2026-10-01", "valid_until": "2026-10-31"}})
    candidate["private_note"] = "Possible inheritance is disputed."
    samples.rebind(candidate, packet, inventory, review)
    review["decisions"].append({"claim_id": "/private_note", "classification": "supported", "verdict": "supported",
                                "subject_check": "matched", "field_check": "matched", "rationale": "Exact separately restricted note.",
                                "evidence": [samples.span(packet, candidate["private_note"], source_id="PRIVATE")]})
    request = {"schema_version": "wealth-audience-request-v1", "request_id": "review-1", "as_of": "2026-10-04", "recipient_ids": ["advisor-n", "service-n"]}
    plan = {"schema_version": "wealth-audience-plan-v1", "blocks": [
        {"block_id": "tax", "heading": "Tax review", "text": "Net proceeds are 2990.00 USD. IRA tax treatment remains unknown.",
         "source_ids": ["S1"], "depends_on_block_ids": [], "claim_ids": ["/proceeds", "/tax_treatment"]},
        {"block_id": "private", "heading": "Advisor-only note", "text": candidate["private_note"],
         "source_ids": ["PRIVATE"], "depends_on_block_ids": [], "claim_ids": ["/private_note"]},
    ]}
    return candidate, packet, inventory, review, request, plan


def draft_review(args):
    pending = quality_gate.assemble(*args)
    assert pending["status"] == "pending-draft-review", pending
    return {"schema_version": "wealth-draft-review-v1", "bindings": pending["review_request"]["bindings"],
            "reviewer": {"reviewer_id": "separate-C", "kind": "model", "independent_from_producer": True},
            "reviewed_at": "2026-10-04T14:00:00Z", "review_reference": "synthetic-independent-draft-review",
            "checks": [{"criterion": c, "status": "pass", "rationale": "Synthetic expected draft checked against raw records and recipients."} for c in quality_gate.CRITERIA]}


class QualityHandoffTests(unittest.TestCase):
    def setUp(self):
        self.args = inputs()

    def test_missing_semantic_review_emits_no_recipient_file(self):
        output = quality_gate.assemble(*self.args)
        self.assertEqual(output["status"], "pending-draft-review")
        self.assertIsNone(output["recipient_draft"])

    def test_complete_chain_and_exact_byte_readback(self):
        review = draft_review(self.args)
        output = quality_gate.assemble(*self.args, review)
        self.assertEqual(output["status"], "reviewed-draft")
        self.assertIn(r'2990\.00', output["recipient_draft"])
        self.assertNotIn('inheritance', output["recipient_draft"])
        self.assertNotIn('PRIVATE', output["recipient_draft"])
        self.assertEqual([], quality_gate.validate(output, *self.args, review, output["recipient_draft"].encode()))
        self.assertFalse(output["action_taken"])
        self.assertEqual(output["professional_approval"], "not-established")

    def test_private_advisor_gets_separate_projection_and_review(self):
        broad_review = draft_review(self.args)
        self.args[4]["recipient_ids"] = ["advisor-n"]
        self.assertEqual(quality_gate.assemble(*self.args, broad_review)["status"], "blocked")
        private_review = draft_review(self.args)
        output = quality_gate.assemble(*self.args, private_review)
        self.assertIn('inheritance', output["recipient_draft"])

    def test_changed_final_bytes_fail_even_when_receipt_is_unchanged(self):
        review = draft_review(self.args)
        output = quality_gate.assemble(*self.args, review)
        changed = output["recipient_draft"].encode() + b'\nPossible inheritance is disputed.\n'
        self.assertTrue(quality_gate.validate(output, *self.args, review, changed))

    def test_large_valid_dependency_chain_remains_reviewable(self):
        self.args[5]["blocks"] = [
            {"block_id": f"b{n}", "heading": "Review", "text": "Supported proceeds.",
             "source_ids": ["S1"], "depends_on_block_ids": [] if n == 0 else [f"b{n-1}"],
             "claim_ids": ["/proceeds"]} for n in range(1200)]
        output = quality_gate.assemble(*self.args)
        self.assertEqual("pending-draft-review", output["status"], output["findings"])

    def test_transitive_source_dependency_is_checked_before_projection(self):
        block = self.args[5]["blocks"][0]
        block["claim_ids"].append("/private_note")
        # Direct source list omits PRIVATE; the declared upstream block carries it.
        block["depends_on_block_ids"] = ["private"]
        self.args[5]["blocks"].append({"block_id": "neutral", "heading": "Cash", "text": "Cash is 1000.00 USD.",
                                      "source_ids": ["S1"], "depends_on_block_ids": [], "claim_ids": ["/cash"]})
        review = draft_review(self.args)
        output = quality_gate.assemble(*self.args, review)
        self.assertEqual("reviewed-draft", output["status"])
        self.assertNotIn("Tax review", output["recipient_draft"])
        self.assertNotIn("PRIVATE", output["recipient_draft"])
        self.assertEqual(["neutral"], output["audience_receipt"]["included_block_ids"])

    def test_malformed_receipt_returns_errors_instead_of_exception(self):
        review = draft_review(self.args)
        output = quality_gate.assemble(*self.args, review)
        for malformed in ({"bad": float("nan")}, {"bad": object()}, {1: "bad"}):
            self.assertTrue(quality_gate.validate(malformed, *self.args, review, output["recipient_draft"].encode()))

    def test_false_status_or_nonbytes_cannot_validate(self):
        review = draft_review(self.args)
        output = quality_gate.assemble(*self.args, review)
        changed = deepcopy(output); changed["status"] = "approved"
        self.assertTrue(quality_gate.validate(changed, *self.args, review, output["recipient_draft"].encode()))
        self.assertTrue(quality_gate.validate(output, *self.args, review, bytearray(output["recipient_draft"].encode())))

    def test_source_mutation_invalidates_both_reviews(self):
        review = draft_review(self.args)
        self.args[1]["sources"][0]["content"] += ' Amended.'
        self.assertEqual(quality_gate.assemble(*self.args, review)["status"], "blocked")

    def test_candidate_fabrication_cannot_pass_native_handoff(self):
        self.args[0]["tax_treatment"] = 'tax-deferred'
        output = quality_gate.assemble(*self.args)
        self.assertEqual(output["status"], "blocked")
        self.assertIsNone(output["recipient_draft"])

    def test_unsupported_reviewed_field_blocks_every_recipient(self):
        samples.decision(self.args[3], '/private_note')["verdict"] = "unsupported"
        self.assertEqual(quality_gate.assemble(*self.args)["status"], "blocked")

    def test_claim_cannot_hide_its_private_source_dependency(self):
        self.args[5]["blocks"][1]["source_ids"] = ['S1']
        self.assertEqual(quality_gate.assemble(*self.args)["status"], "blocked")

    def test_unknown_claim_is_blocked(self):
        self.args[5]["blocks"][0]["claim_ids"].append('/invented')
        self.assertEqual(quality_gate.assemble(*self.args)["status"], "blocked")

    def test_empty_claim_list_is_blocked(self):
        self.args[5]["blocks"][0]["claim_ids"] = []
        self.assertEqual(quality_gate.assemble(*self.args)["status"], "blocked")

    def test_draft_producer_cannot_self_review(self):
        review = draft_review(self.args)
        review["reviewer"]["reviewer_id"] = '  EXTRACTOR-a '
        self.assertEqual(quality_gate.assemble(*self.args, review)["status"], "blocked")

    def test_missing_failed_or_duplicate_semantic_check_blocks(self):
        for change in ('missing', 'failed', 'duplicate'):
            with self.subTest(change=change):
                review = draft_review(self.args)
                if change == 'missing':
                    review['checks'].pop()
                elif change == 'failed':
                    review['checks'][0]['status'] = 'fail'
                else:
                    review['checks'][0] = deepcopy(review['checks'][1])
                self.assertEqual(quality_gate.assemble(*self.args, review)["status"], "blocked")

    def test_review_bound_to_actual_wording(self):
        review = draft_review(self.args)
        self.args[5]['blocks'][0]['text'] = 'All accounts are tax deferred.'
        self.assertEqual(quality_gate.assemble(*self.args, review)["status"], "blocked")

    def test_cli_creates_distinct_files_then_verifies_and_refuses_overwrite(self):
        review = draft_review(self.args)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            command = []
            for name, value in zip(('candidate', 'sources', 'inventory', 'field-review', 'request', 'plan', 'draft-review'), (*self.args, review)):
                path = folder / (name + '.json')
                path.write_text(json.dumps(value))
                command.extend(['--' + name, str(path)])
            command += ['--receipt', str(folder / 'internal.json'), '--rendered', str(folder / 'recipient.md')]
            old_umask = os.umask(0o022)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(0, quality_gate.main(command))
                    self.assertEqual(0, quality_gate.main(command + ['--verify']))
                    self.assertEqual(1, quality_gate.main(command))
            finally:
                os.umask(old_umask)
            self.assertEqual(0o600, stat.S_IMODE((folder / 'internal.json').stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE((folder / 'recipient.md').stat().st_mode))
            (folder / 'recipient.md').write_text('Changed')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(1, quality_gate.main(command + ['--verify']))
            (folder / 'candidate.json').write_text('[' * 3000 + '0' + ']' * 3000)
            public = io.StringIO()
            with contextlib.redirect_stdout(public):
                self.assertEqual(1, quality_gate.main(command + ['--verify']))
            self.assertEqual(audience_gate.PUBLIC_FAILURE + '\n', public.getvalue())

    def test_cli_refuses_receipt_and_rendered_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp) / 'same')
            argv = [item for name in ('candidate', 'sources', 'inventory', 'field-review', 'request', 'plan') for item in ('--' + name, path)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(1, quality_gate.main(argv + ['--receipt', path, '--rendered', path]))
            self.assertFalse(Path(path).exists())

    def test_portable_bundle_is_identical_and_imports_without_repository(self):
        for package in PACKAGES:
            with self.subTest(package=package), tempfile.TemporaryDirectory() as temp:
                folder = Path(temp)
                for source, relative in FILES.items():
                    bundled = ROOT / 'skills/wealth-management' / package / relative
                    self.assertEqual((ROOT / 'shared/wealth-quality' / source).read_bytes(), bundled.read_bytes())
                    if source.endswith('.py'):
                        (folder / source).write_bytes(bundled.read_bytes())
                result = subprocess.run([sys.executable, str(folder / 'quality_gate.py'), '--help'], cwd=folder, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
