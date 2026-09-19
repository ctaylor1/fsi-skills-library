# Handoff contract

The common evidence envelope is shared by discovery, reconciliation, onboarding, risk, recommendation-evidence and protection and all thirteen P1 and four P2 and two P3 workflows. Client-review and follow-up retain existing documented inputs and add engagement/configuration controls. Their full schemas are not interchangeable.

Before each selected target:
1. Load that target's schema and validator.
2. Carry household ID, capacity/jurisdiction, as-of date, source registry, upstream artifact ID, status and unresolved findings in the human-review context. Map individual source IDs without inventing evidence.
3. Prepare the target-specific record structure, preserving unknowns and exclusions. A shared envelope alone is insufficient.
4. Run the target input validator. If evidence is insufficient, request it or return a draft with the target's explicit needs-data state; do not relabel an upstream gap as complete.
5. Run the target output validator before use. Return artifacts for human review; execution and delivery are separate authorized workflows.

This P0/P1/P2/P3 release offers a routing plan and documented handoffs, not an automatic multi-skill execution engine or lossless universal schema adapter.

A complete P1 journey may request planning → IPS → construction → comparison → rebalancing → recommendation evidence → review, but each target needs its own sources and typed input. Preserve `goal-progress` as the planning mode when requested. Map inherited findings into the target issue field as documented by its schema. Sources may need explicit registry merging with collision resolution by source identity; do not rename citations without updating references.

All four P2 packages require `upstream_issues: [{artifact_id, code, message, status, source_ids}]`; resolved issues also need a dated attributed resolution record. Map router unresolved_issues together with the actual originating artifact ID into these rows, merging source identities explicitly. Do not substitute a routing artifact for the financial evidence it references. Book scope must be converted into a distinct, reviewed household/prospect request; private-market per-account obligations and lending alternatives cannot be summed as available cash.

Both P3 targets require the same explicit attributed `upstream_issues` inventory, including source-linked resolutions. Preserve scope_type, family_id/trust_id, exact originating artifact IDs and per-record actual household/member/beneficiary IDs. Family discussion results are attributed evidence, not trust authority or estate-document precedence. A trustee title does not authorize family-wide disclosure. Share only the reviewed audience draft and authorized evidence for the specific target; internal source snapshots are not circulation artifacts.
