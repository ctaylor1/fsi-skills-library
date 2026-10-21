# Native output schema — transaction_monitoring_scenario_design

The immutable native object uses `contract_version: compliance-foundation/2.0` and `method: risk-lineage-logic-change-proposal/1.0`. It retains request/object identity, as-of/cutoff, institution context, role, audience/classification, source refs/claim bindings, unresolved issues and integrity envelope. `status` is draft-for-human-review or needs-evidence, never an approval or operational decision. `draft` and `human_review_required` are true; `action_taken` is false; approval is not_requested and execution is not_performed.

The `results` object has exactly these method-owned fields:

`risk_to_scenario_design`, `data_requirements`, `parameter_proposal`, `evaluation_plan`, `controlled_change_proposal`, `technology_control_requirements`, `engine_observations`, `benchmark_references`, `material_blockers`, `unknown_metrics`, `proposal_prerequisites_consistent`, `proposed_engine_configuration`, `backtest_executed`, `holdout_executed`, `identity_resolution`, `risk_or_legal_approval`, `activation`.

Null is a withheld/unknown measure or proposal, never zero, pass, negative or approved. Material blockers explain unresolved prerequisites; unknown metrics retain separately unmeasured dependent quantities. Counts and fractions retain exact integer numerator/denominator; decimal display is 12-place half-even and does not drive institutional threshold comparison. Precision-bound input amounts remain exact strings.

Retain the detached original. `validate_output.py OUTPUT --input INPUT` reconstructs and compares the entire native object, rejecting edits, added narratives, changed versions/IDs and self-rehashed replacement results. A synthetic golden is a software expectation, not professional evidence. Read [domain rules](domain-rules.md) for the specific meaning and withholding of each measure.
