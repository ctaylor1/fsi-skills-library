# Appeal Package Template

Fill only from the computed appeal work-product and the cited bundle. Do not add any
statement not backed by a citation. Keep every prohibited category out (no legal advice, no
coverage/eligibility determination, no guaranteed outcome, no "we filed it"). Leave the
standing disclaimer verbatim. Mask member/claim identifiers to the last 4.

---

## Appeal package — claim {{claim_id}}

- **Member:** {{member_id}}   **Plan:** {{plan_id}}
- **Denial date:** {{denial_date}}   **Appeal level:** {{appeal_level}}
- **Appeal deadline:** {{appeal_deadline}} — {{days_remaining}} days remaining as of
  {{as_of}} (status: {{deadline_status}})
- **Evidence readiness:** {{readiness}}
- **Reference:** {{appeal_id}}

### 1. Why the claim was denied
For each denial reason, restate the plan's stated basis neutrally, citing the denial
notice/EOB line and the governing plan provision:
- **{{reason_code}}** — {{explanation}} Governing provision: {{supporting_policy_refs}}.

### 2. Supporting evidence on file (with citations)
For each reason, list `evidence_present` with its citation. Every item here must trace to a
document in the bundle:
- {{doc_type}} — {{citation}}

### 3. Argument the appeal presents
Only include points from `argument_points` (drafted solely where cited evidence backs them).
State them as the record the plan is asked to reconsider — not as a coverage conclusion:
- {{argument_point}}

### 4. Outstanding evidence to strengthen the appeal
List `outstanding_evidence` / per-reason `evidence_gaps`. Be explicit that these are not yet
on file:
- {{evidence_gap}}

### 5. Next steps (administrative)
- Gather the outstanding evidence above before submission.
- A human reviewer must approve this package before it is delivered to the member or sent to
  the plan.
- Submit through the plan's appeal process by the deadline; for questions about legal rights,
  consult a licensed attorney.

---

> {{disclaimer}}

<!-- Standing disclaimer (leave verbatim):
Administrative appeal support only; not legal advice and not a coverage determination. The
insurer or an independent external reviewer decides the appeal; no appeal has been filed on
the member's behalf. -->
