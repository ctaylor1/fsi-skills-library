# Scope and handoff mapping

Preserve scope_type=trust, trust_id and household_id=trust:<trust_id> in the result and handoff
context. The collection marker must never be passed as an actual beneficiary household. Each
beneficiary link and distribution result retains the separately reviewed actual household ID.
Every trust register row must match the same trust_id; do not combine trust ledgers or infer common
ownership from related beneficiaries.

| Adjacent workflow | Boundary and exact evidence |
| --- | --- |
| estate-wealth-transfer-reviewer | Estate intentions/titling/beneficiary coordination remain separate. Share only authorized source-bound discrepancies, exact trust clauses and unknowns; no legal precedence determination. |
| family-wealth-governance-preparer | Governance meeting roles are not trustee authority. Share minimum authorized issue summaries only after recipient/purpose review; no beneficiary-specific records from a family relationship label. |
| household-financial-planning-assistant | A separately authorized beneficiary-household adapter may use documented cash scenarios. Requested or discretionary distributions are not guaranteed income or household-owned trust assets. |
| investment-recommendation-evidence-reviewer | Carry material trust authority, classification, ownership and liquidity concerns into recommendation evidence if an independently proposed investment requires them. No recommendation originates here. |
| wealth-account-service-packager | Separately requested operations may use reconciled evidence through certified controls. This draft never authorizes payment, filing, changing a trust or changing beneficiaries. |
| wealth-performance-report-builder | Settled dated movements and valuations can be inputs after independently mapping the reporting perimeter; cash-ledger scope is not performance external-flow classification. |
| Trust counsel / fiduciary accountant | Exact clause, document, amount, date, conflicting source and unresolved question, with current applicability profile; professional interpretation stays with them. |

Import originating concerns into explicit upstream_issues records with artifact_id/code/message,
status and exact source_ids, retaining original source provenance. A resolved record requires an
attributed dated resolution and citations; a ready label alone cannot resolve it. Map other
schemas explicitly before use. No hash or named professional authenticates a resolution.

Outbound handoffs preserve full relevant values, unknowns, request/artifact/input hash, source
registry, capacity/as_of, policy and trust subject fields. Existing upstream issues retain their
original identities. Map each new finding to an unresolved issue with this artifact's ID, code,
message and the source IDs of contributing records located by its path. A missing source is a gap,
not permission to invent a citation. The recipient must preserve concerns in its native issue schema.
For recommendation evidence use origin upstream-artifact and this skill/artifact_id/input_hash,
with exact code/message/source_ids. Do not replace the trust subject with a household silently.
