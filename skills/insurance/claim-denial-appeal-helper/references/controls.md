# Controls — claim-denial-appeal-helper

- **Risk tier:** R2 — analytical / drafting support. **Action mode:** Read-only analysis
  producing a draft appeal package.
- **Human approval:** `external-delivery` — required before the package is delivered to the
  member/advocate or sent to the plan. No approval is needed for the reviewer's own read.

## Prohibited (fail closed)

- No **legal advice** or litigation strategy — no "you should sue", "file a lawsuit",
  "bad faith", "you are legally entitled", or any assessment of legal rights or damages.
  Refer the member to a licensed attorney for legal questions.
- No **coverage / eligibility determination** — never state that the claim/service **is**
  covered, that coverage applies, that the member is eligible, that the denial is invalid, or
  that the insurer must pay. The insurer or an independent external reviewer decides the
  appeal.
- No **guaranteed outcome** — never state or imply the appeal will win or is certain to be
  overturned.
- No **filing or submission** — the skill drafts a package; it never files, submits, or
  transmits the appeal, and never states that it has.
- No **unsupported claims** — an argument point is drafted only when cited evidence in the
  bundle backs it; missing evidence is reported as a gap, not asserted around.
- No **medical advice** — do not opine on the appropriateness of treatment; present the
  treating clinician's documentation as evidence.

## Required output screens (`scripts/validate_output.py`)

- Every drafted argument point is evidence-backed (≥1 cited `evidence_present` row; all
  evidence rows carry a citation).
- No prohibited language (regex screen: legal advice, coverage/eligibility determination,
  guaranteed outcome, filed-on-behalf).
- `appeal_deadline`, `days_remaining`, and `deadline_status` equal the deterministic
  computation from `denial_date`, `appeal_window_days`, and `as_of`; `readiness` maps
  deterministically from the evidence gaps.
- Standing disclaimer present: *"Administrative appeal support only; not legal advice and not
  a coverage determination. The insurer or an independent external reviewer decides the
  appeal; no appeal has been filed on the member's behalf."*
- `human_review_required` is true (external-delivery approval gate).
- When evidence gaps exist, `outstanding_evidence` prompts are included (gap disclosure).

## Fairness / conduct

- Present the member's evidence and the plan's stated reasons factually and respectfully.
- Do not use protected-class attributes or health-condition stigma in framing.
- Do not overstate the strength of the appeal; state what the evidence supports and what is
  still outstanding.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII + PHI).** Mask member/claim identifiers to the last
  4. Minimize clinical detail to what evidences an argument.
- Retain the appeal work-product + citations + config version per records policy; log the
  read and the external-delivery approval. Never exfiltrate member or clinical data.

## Reproducibility

`appeal_id` binds the output to the exact inputs, the appeal-window config, and the
reason→evidence checklist version; re-running with the same inputs reproduces the evidence
map, deadline, and readiness.
