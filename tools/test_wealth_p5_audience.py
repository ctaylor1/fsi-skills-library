"""Independent expectations for the declared-audience gate; no model truth claim."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "shared/wealth-quality/audience_gate.py"
spec = importlib.util.spec_from_file_location("wealth_p5_audience_gate", MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def inputs():
    people = ["Mira", "Lane", "H-A", "H-B"]
    request = {"schema_version": "wealth-audience-request-v1", "request_id": "review-heath",
               "as_of": "2026-10-04", "recipient_ids": ["H-A", "H-B"]}
    packet = {"schema_version": "wealth-source-packet-v1", "packet_id": "source-heath",
              "recipients": [{"recipient_id": p, "kind": "person"} for p in people],
              "sources": [
                  {"source_id": "PUB", "reference": "Meeting minutes dated October 3",
                   "content": "No portfolio decision. Lane obtains performance October 8.",
                   "access": {"allowed_recipient_ids": people, "effective_date": "2026-10-01", "valid_until": "2026-10-31"}},
                  {"source_id": "PRIVATE", "reference": "Mira-only personal note",
                   "content": "Possible inheritance and sibling dispute; amount unknown.",
                   "access": {"allowed_recipient_ids": ["Mira"], "effective_date": "2026-10-01", "valid_until": "2026-10-31"}}]}
    plan = {"schema_version": "wealth-audience-plan-v1", "blocks": [
        {"block_id": "public-meeting", "heading": "Meeting outcome",
         "text": "No portfolio decision. Lane obtains performance October 8.",
         "source_ids": ["PUB"], "depends_on_block_ids": [], "claim_ids": ["/meeting/outcome", "/actions/0"]},
        {"block_id": "private-note", "heading": "Private inheritance",
         "text": "Possible inheritance and sibling dispute; amount unknown.",
         "source_ids": ["PRIVATE"], "depends_on_block_ids": [], "claim_ids": ["/private/0"]},
        {"block_id": "derived-summary", "heading": "Internal planning consequence",
         "text": "Additional planning scope requires review.", "source_ids": ["PUB"],
         "depends_on_block_ids": ["private-note"], "claim_ids": ["/internal/summary"]}]}
    return request, packet, plan


class AudienceGateTests(unittest.TestCase):
    def test_joint_draft_excludes_private_metadata_and_derived_block(self):
        request, packet, plan = inputs()
        result = gate.project(request, packet, plan)
        public = json.dumps(result["projection"]) + result["rendered_markdown"]
        for forbidden in ["PRIVATE", "Mira-only", "inheritance", "sibling", "private-note",
                          "derived-summary", "Additional planning", "/private", "excluded", "count",
                          "source_packet_sha256"]:
            self.assertNotIn(forbidden, public)
        self.assertEqual(result["projection"]["sources"], [{"source_id": "PUB", "reference": "Meeting minutes dated October 3"}])
        self.assertEqual(result["receipt"]["included_block_ids"], ["public-meeting"])
        self.assertEqual(result["receipt"]["claim_ids"], ["/actions/0", "/meeting/outcome"])

    def test_internal_service_manager_is_not_implicitly_private(self):
        request, packet, plan = inputs()
        request["recipient_ids"] = ["Mira", "Lane"]
        result = gate.project(request, packet, plan)
        self.assertEqual(len(result["projection"]["blocks"]), 1)
        self.assertNotIn("inheritance", result["rendered_markdown"])

    def test_exact_private_recipient_can_receive_dependency_closed_content(self):
        request, packet, plan = inputs()
        request["recipient_ids"] = ["Mira"]
        result = gate.project(request, packet, plan)
        self.assertEqual(len(result["projection"]["blocks"]), 3)
        self.assertEqual(result["projection"]["blocks"][2]["source_ids"], ["PRIVATE", "PUB"])
        self.assertIn("sibling dispute", result["rendered_markdown"])

    def test_adding_inaccessible_evidence_never_changes_public_bytes(self):
        request, packet, plan = inputs()
        packet["sources"] = packet["sources"][:1]
        plan["blocks"] = plan["blocks"][:1]
        before = gate.project(request, packet, plan)
        for i in range(24):
            private = {"source_id": f"SECRET-{i}", "reference": f"Secret record {i}", "content": f"Private fact {i}",
                       "access": {"allowed_recipient_ids": ["Mira"], "effective_date": "2026-10-01", "valid_until": "2026-10-31"}}
            packet["sources"].insert(0, private)
            plan["blocks"].insert(0, {"block_id": f"hidden-{i}", "heading": f"Hidden label {i}",
                                      "text": f"Hidden content {i}", "source_ids": [f"SECRET-{i}"],
                                      "depends_on_block_ids": [], "claim_ids": [f"/hidden/{i}"]})
            after = gate.project(request, packet, plan)
            self.assertEqual(before["projection"], after["projection"])
            self.assertEqual(before["rendered_markdown"], after["rendered_markdown"])
            self.assertEqual(before["receipt"]["rendered_sha256"], after["receipt"]["rendered_sha256"])
            self.assertNotEqual(before["receipt"]["source_packet_sha256"], after["receipt"]["source_packet_sha256"])

    def test_modifying_or_removing_private_content_preserves_public_bytes(self):
        request, packet, plan = inputs()
        before = gate.project(request, packet, plan)
        packet["sources"][1]["reference"] = "Entirely different private source"
        packet["sources"][1]["content"] = "A different private subject"
        plan["blocks"][1]["heading"] = "Changed restricted subject"
        plan["blocks"][1]["text"] = "No shared meaning"
        after = gate.project(request, packet, plan)
        self.assertEqual(before["rendered_markdown"], after["rendered_markdown"])
        packet["sources"] = packet["sources"][:1]
        plan["blocks"] = plan["blocks"][:1]
        self.assertEqual(before["rendered_markdown"], gate.project(request, packet, plan)["rendered_markdown"])

    def test_visible_text_change_changes_binding(self):
        request, packet, plan = inputs()
        first = gate.project(request, packet, plan)
        plan["blocks"][0]["text"] += " Draft only."
        second = gate.project(request, packet, plan)
        self.assertNotEqual(first["receipt"]["content_plan_sha256"], second["receipt"]["content_plan_sha256"])
        self.assertNotEqual(first["receipt"]["rendered_sha256"], second["receipt"]["rendered_sha256"])

    def test_transitive_dependency_cannot_be_laundered_as_public(self):
        request, packet, plan = inputs()
        plan["blocks"].append({"block_id": "twice-derived", "heading": "Safe-looking label",
                               "text": "One planning issue remains.", "source_ids": ["PUB"],
                               "depends_on_block_ids": ["derived-summary"], "claim_ids": ["/count"]})
        result = gate.project(request, packet, plan)
        self.assertEqual(len(result["projection"]["blocks"]), 1)
        self.assertNotIn("One planning issue", result["rendered_markdown"])

    def test_multiple_sources_require_every_recipient_on_every_source(self):
        request, packet, plan = inputs()
        plan["blocks"][0]["source_ids"] = ["PUB", "PRIVATE"]
        with self.assertRaises(gate.GateError):
            gate.project(request, packet, plan)

    def test_expired_future_and_empty_grants_do_not_authorize(self):
        for change in [{"valid_until": "2026-10-03"}, {"effective_date": "2026-10-05"}, {"allowed_recipient_ids": []}]:
            with self.subTest(change=change):
                request, packet, plan = inputs()
                packet["sources"][0]["access"].update(change)
                with self.assertRaises(gate.GateError) as ctx:
                    gate.project(request, packet, plan)
                self.assertEqual(ctx.exception.public_message, gate.PUBLIC_FAILURE)

    def test_permission_boundaries_are_inclusive(self):
        request, packet, plan = inputs()
        for as_of in ["2026-10-01", "2026-10-31"]:
            request["as_of"] = as_of
            self.assertEqual(len(gate.project(request, packet, plan)["projection"]["blocks"]), 1)

    def test_no_registry_grant_from_source_owner(self):
        request, packet, plan = inputs()
        packet["sources"][0]["owner"] = "H-A"
        del packet["sources"][0]["access"]
        with self.assertRaises(gate.GateError):
            gate.project(request, packet, plan)

    def test_missing_permission_even_unused_source_blocks(self):
        request, packet, plan = inputs()
        del packet["sources"][1]["access"]
        with self.assertRaises(gate.GateError):
            gate.project(request, packet, plan)

    def test_unknown_and_generic_recipients_block(self):
        for recipient in ["UnknownPerson", "internal", "all", "*", "reviewers"]:
            with self.subTest(recipient=recipient):
                request, packet, plan = inputs()
                request["recipient_ids"] = [recipient]
                with self.assertRaises(gate.GateError):
                    gate.project(request, packet, plan)

    def test_group_record_cannot_be_registered_as_a_person(self):
        request, packet, plan = inputs()
        packet["recipients"][0]["kind"] = "group"
        with self.assertRaises(gate.GateError):
            gate.project(request, packet, plan)

    def test_unknown_recipient_in_permission_blocks(self):
        request, packet, plan = inputs()
        packet["sources"][0]["access"]["allowed_recipient_ids"].append("Ghost")
        with self.assertRaises(gate.GateError):
            gate.project(request, packet, plan)

    def test_missing_claims_and_bad_pointer_block(self):
        for value in [[], ["some-claim"], ["/bad~2escape"], ["/same", "/same"], None]:
            with self.subTest(value=value):
                request, packet, plan = inputs()
                plan["blocks"][0]["claim_ids"] = value
                with self.assertRaises(gate.GateError):
                    gate.project(request, packet, plan)

    def test_escaped_json_pointers_are_retained_only_in_internal_receipt(self):
        request, packet, plan = inputs()
        plan["blocks"][0]["claim_ids"] = ["/facts/a~1b/~0label"]
        result = gate.project(request, packet, plan)
        self.assertEqual(result["receipt"]["claim_ids"], ["/facts/a~1b/~0label"])
        self.assertNotIn("~1", json.dumps(result["projection"]))

    def test_cyclic_and_unknown_dependencies_block(self):
        for deps in [["missing"], ["public-meeting"], ["derived-summary"]]:
            request, packet, plan = inputs()
            plan["blocks"][1]["depends_on_block_ids"] = deps
            if deps == ["public-meeting"]:
                plan["blocks"][0]["depends_on_block_ids"] = ["private-note"]
            with self.subTest(deps=deps), self.assertRaises(gate.GateError):
                gate.project(request, packet, plan)

    def test_duplicate_identifiers_block(self):
        for target in ["sources", "recipients", "blocks"]:
            request, packet, plan = inputs()
            doc = plan if target == "blocks" else packet
            doc[target].append(deepcopy(doc[target][0]))
            with self.subTest(target=target), self.assertRaises(gate.GateError):
                gate.project(request, packet, plan)

    def test_malformed_json_shapes_are_structured_failures(self):
        for index in range(3):
            for bad in [None, [], "not an object", 2, True]:
                docs = list(inputs()); docs[index] = bad
                with self.subTest(index=index, bad=bad), self.assertRaises(gate.GateError):
                    gate.project(*docs)
        request, packet, plan = inputs()
        packet["recipients"] = [{"recipient_id": [], "kind": "person"}]
        with self.assertRaises(gate.GateError):
            gate.project(request, packet, plan)

    def test_python_only_values_and_invalid_unicode_fail_structurally(self):
        for value in [{1: "one", "two": 2}, {"value": ("tuple",)}, {"value": b"bytes"}, {"value": "\ud800"}]:
            request, packet, plan = inputs()
            packet["extra_metadata"] = value
            with self.subTest(value=repr(value)), self.assertRaises(gate.GateError):
                gate.project(request, packet, plan)

    def test_long_dependency_chain_is_closed_without_recursion(self):
        request, packet, plan = inputs()
        previous = "private-note"
        for i in range(1200):
            bid = f"derived-{i}"
            plan["blocks"].append({"block_id": bid, "heading": "Derived note", "text": "A private consequence.",
                                   "source_ids": ["PUB"], "depends_on_block_ids": [previous],
                                   "claim_ids": [f"/derived/{i}"]})
            previous = bid
        result = gate.project(request, packet, plan)
        self.assertEqual(len(result["projection"]["blocks"]), 1)
        plan["blocks"][1]["depends_on_block_ids"] = [previous]
        with self.assertRaises(gate.GateError):
            gate.project(request, packet, plan)

    def test_raw_html_markdown_images_and_comments_render_literally(self):
        request, packet, plan = inputs()
        plan["blocks"][0]["text"] = '<!-- hidden --><img src="https://example.invalid/pixel">\n![image](https://example.invalid)\n<script>alert(1)</script>'
        result = gate.project(request, packet, plan)
        rendered = result["rendered_markdown"]
        self.assertNotIn("<img", rendered)
        self.assertNotIn("<!--", rendered)
        self.assertNotIn("![", rendered)
        self.assertNotIn("<script", rendered)
        self.assertIn("&lt;img", rendered)

    def test_extra_raw_markdown_sidecar_fields_rejected(self):
        for target, key in [("plan", "markdown"), ("block", "audience"), ("request", "all_audiences")]:
            request, packet, plan = inputs()
            doc = {"plan": plan, "block": plan["blocks"][0], "request": request}[target]
            doc[key] = "secret"
            with self.subTest(target=target), self.assertRaises(gate.GateError):
                gate.project(request, packet, plan)

    def test_control_characters_and_nonfinite_values_block(self):
        for bad in ["Text\x00hidden", "Text\u202ehidden"]:
            request, packet, plan = inputs()
            plan["blocks"][0]["text"] = bad
            with self.assertRaises(gate.GateError):
                gate.project(request, packet, plan)
        request, packet, plan = inputs(); packet["raw_number"] = float("nan")
        with self.assertRaises(gate.GateError):
            gate.project(request, packet, plan)

    def test_reconstructed_bundle_and_actual_bytes_validate(self):
        request, packet, plan = inputs(); result = gate.project(request, packet, plan)
        self.assertEqual(gate.validate_projection(request, packet, plan, result), [])
        self.assertEqual(gate.validate_rendered(request, packet, plan, result["rendered_markdown"].encode(), result["receipt"]), [])

    def test_forged_render_hash_cannot_bless_appended_restricted_text(self):
        import hashlib
        request, packet, plan = inputs(); result = gate.project(request, packet, plan)
        edited = result["rendered_markdown"].encode() + b"Private inheritance\n"
        forged = deepcopy(result["receipt"]); forged["rendered_sha256"] = hashlib.sha256(edited).hexdigest()
        self.assertTrue(gate.validate_rendered(request, packet, plan, edited, forged))

    def test_receipt_cannot_be_reused_for_another_audience(self):
        request, packet, plan = inputs(); request["recipient_ids"] = ["Mira"]
        private = gate.project(request, packet, plan)
        request["recipient_ids"] = ["Lane"]
        self.assertTrue(gate.validate_rendered(request, packet, plan, private["rendered_markdown"].encode(), private["receipt"]))

    def test_expanded_claims_or_registry_and_copied_receipt_fail(self):
        request, packet, plan = inputs(); result = gate.project(request, packet, plan)
        changed = deepcopy(result); changed["projection"]["sources"].append({"source_id": "PRIVATE", "reference": "private note"})
        self.assertTrue(gate.validate_projection(request, packet, plan, changed))
        changed = deepcopy(result); changed["receipt"]["claim_ids"] = []
        self.assertTrue(gate.validate_projection(request, packet, plan, changed))

    def test_complete_input_hashes_bind_metadata_without_public_metadata_leaks(self):
        request, packet, plan = inputs(); first = gate.project(request, packet, plan)
        packet["operator_review_id"] = "evidence-log-42"
        second = gate.project(request, packet, plan)
        self.assertEqual(first["projection"], second["projection"])
        self.assertNotEqual(first["receipt"]["source_packet_sha256"], second["receipt"]["source_packet_sha256"])
        self.assertTrue(gate.validate_rendered(request, packet, plan, first["rendered_markdown"].encode(), first["receipt"]))

    def test_declared_grants_never_claim_semantic_or_access_authentication(self):
        result = gate.project(*inputs())
        for field in ["permission_authentication", "semantic_dependency_completeness", "deployment_access_enforcement"]:
            self.assertEqual(result["receipt"][field], "not-established")
        self.assertTrue(result["receipt"]["human_review_required"])
        self.assertFalse(result["receipt"]["action_taken"])

    def test_cli_separate_destinations_validate_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="wealth-p5-audience-") as tmp:
            paths = {k: Path(tmp) / (k + ".json") for k in ["request", "packet", "plan", "receipt"]}
            paths["rendered"] = Path(tmp) / "recipient.md"
            for k, value in zip(["request", "packet", "plan"], inputs()):
                paths[k].write_text(json.dumps(value))
            args = ["--request", str(paths["request"]), "--source-packet", str(paths["packet"]),
                    "--plan", str(paths["plan"]), "--receipt", str(paths["receipt"]), "--rendered", str(paths["rendered"])]
            def run(mode):
                return subprocess.run([sys.executable, "-B", str(MODULE), mode, *args], capture_output=True, text=True)
            self.assertEqual(run("render").returncode, 0)
            self.assertEqual(paths["receipt"].stat().st_mode & 0o777, 0o600)
            self.assertEqual(paths["rendered"].stat().st_mode & 0o777, 0o600)
            self.assertEqual(run("validate").returncode, 0)
            self.assertEqual(run("render").returncode, 1)
            paths["rendered"].write_text(paths["rendered"].read_text() + "private data")
            failed = run("validate")
            self.assertEqual(failed.returncode, 1)
            self.assertEqual(failed.stderr.strip(), gate.PUBLIC_FAILURE)
            self.assertNotIn("PRIVATE", failed.stdout + failed.stderr)

    def test_cli_denial_does_not_write_either_file_or_expose_private_errors(self):
        with tempfile.TemporaryDirectory(prefix="wealth-p5-audience-") as tmp:
            request, packet, plan = inputs(); request["recipient_ids"] = ["UnregisteredSecretPerson"]
            p = Path(tmp)
            for name, value in [("request", request), ("packet", packet), ("plan", plan)]:
                (p / f"{name}.json").write_text(json.dumps(value))
            result = subprocess.run([sys.executable, "-B", str(MODULE), "render", "--request", str(p / "request.json"),
                                     "--source-packet", str(p / "packet.json"), "--plan", str(p / "plan.json"),
                                     "--rendered", str(p / "out.md"), "--receipt", str(p / "receipt.json")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stderr.strip(), gate.PUBLIC_FAILURE)
            self.assertFalse((p / "out.md").exists()); self.assertFalse((p / "receipt.json").exists())

    def test_cli_rejects_same_paths_and_symlink_aliases_without_changing_inputs(self):
        for collision in ["receipt-output", "input-output", "symlink-output"]:
            with self.subTest(collision=collision), tempfile.TemporaryDirectory(prefix="wealth-p5-audience-") as tmp:
                p = Path(tmp)
                for name, value in zip(["request", "packet", "plan"], inputs()):
                    (p / f"{name}.json").write_text(json.dumps(value))
                original = (p / "request.json").read_bytes()
                rendered, receipt = p / "draft.md", p / "receipt.json"
                if collision == "receipt-output":
                    receipt = rendered
                elif collision == "input-output":
                    rendered = p / "request.json"
                else:
                    rendered.symlink_to(p / "request.json")
                result = subprocess.run([sys.executable, "-B", str(MODULE), "render", "--request", str(p / "request.json"),
                                         "--source-packet", str(p / "packet.json"), "--plan", str(p / "plan.json"),
                                         "--rendered", str(rendered), "--receipt", str(receipt)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stderr.strip(), gate.PUBLIC_FAILURE)
                self.assertEqual((p / "request.json").read_bytes(), original)

    def test_cli_rejects_hard_link_aliases_during_validation(self):
        with tempfile.TemporaryDirectory(prefix="wealth-p5-audience-") as tmp:
            p = Path(tmp)
            for name, value in zip(["request", "packet", "plan"], inputs()):
                (p / f"{name}.json").write_text(json.dumps(value))
            os.link(p / "request.json", p / "receipt.json")
            (p / "draft.md").write_text("This deliberately is not a gate output.")
            result = subprocess.run([sys.executable, "-B", str(MODULE), "validate", "--request", str(p / "request.json"),
                                     "--source-packet", str(p / "packet.json"), "--plan", str(p / "plan.json"),
                                     "--rendered", str(p / "draft.md"), "--receipt", str(p / "receipt.json")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stderr.strip(), gate.PUBLIC_FAILURE)


if __name__ == "__main__":
    unittest.main()
