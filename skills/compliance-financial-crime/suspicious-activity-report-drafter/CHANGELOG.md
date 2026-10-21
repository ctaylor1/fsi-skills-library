## Independent forward-test regressions — 2026-09-21

Activity windows and listed transaction dates must be real, ordered and on/before as_of; future activity produces a chronology break and cannot be ready. Investigation rationale requires evidence_ids resolving to cited evidence facts, exact summary matching, and citations consistent with those facts. Unsupported rationale text is withheld; a nonempty invented citation is insufficient.

Preserved the original failing evidence externally; added package-local regression copies and independently expected positive/negative cases.

# Phase 1 correctness update — 2026-09-21 (0.1.1)

- Added detached original-input reconstruction; native source truth remains unverified.
- Corrected the bounded logic, explicit unknown states, supplied approval evidence and scope documented in SKILL.md.
- Added executable adversarial regressions and corrected synthetic evidence claims.
- Production integrations, issuer authentication and professional/legal acceptance remain pending.

# Changelog — suspicious-activity-report-drafter

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to turn a
concluded, human-adjudicated transaction-monitoring investigation into a controlled,
fact-based **draft SAR package** for compliance quality review and authorized human filing —
distinct from the investigation that concludes suspicion and from the human filing itself.

- **Scope:** assemble the fourteen-section SAR draft (subjects/parties, accounts/instruments,
  activity summary, chronology, amount/chronology tie-out, typology assessment, 5W+H narrative,
  evidence index, investigation rationale, recommendation, approvals, sources, standing note)
  from an approved investigation case. Draft-only; the file/no-file determination and filing
  stay with the human.
- **Controls:** R3; no suspicion/file-no-file determination, no filing/e-filing/FinCEN
  submission, no case closure/disposition, no system-of-record write, no send, no speculation;
  hard boundary — no SAR draft from a case not approved for SAR (`blocked`, route to
  investigator); SAR-confidentiality / tipping-off screen; versioned typology library +
  template + quality checklist.
- **Scripts:** `validate_input` (approved-case schema; tie-out, party-coverage, typology, and
  5W+H gap warnings), `calculate_or_transform` (deterministic assembler: tie-outs, party
  coverage, typology consistency, 5W+H narrative, evidence index, packaging status + advisory
  review path), `validate_output` (allowed draft status, template fidelity, no unsupported
  claims, tie-out reconciliation, no-speculation screen, determination/filing/send language
  screens, approvals recorded, hard-boundary consistency, standing note).
- **Assets:** `assets/output-template.md` — the fourteen required SAR draft sections.
- **Evaluations:** trigger/routing, golden 7-transaction structuring/funnel case exercising
  every tie-out and full party/typology coverage, deterministic script checks, fail-closed
  safety on a non-compliant package (bad status, faked tie-out pass, speculation, filing
  language, missing standing note), plus no-filing / no-speculation / tipping-off / injection
  refusals and hard-boundary + filing-write authorization checks.
- **Handoffs:** upstream from `transaction-monitoring-alert-investigator` (and
  `enhanced-due-diligence-packager`, `aml-alert-triager`); specialist corroboration to
  `sanctions-match-adjudicator`, `adverse-media-investigator`, `beneficial-ownership-verifier`,
  `customer-risk-rating-reviewer`; downstream to human SAR quality review, MLRO/BSA approval,
  and BSA E-Filing (human/operations — no catalog skill files a SAR).

### Pending before release
- FIU/AML control-owner + legal (SAR-confidentiality) blind review; segregation-of-duty review
  (drafting vs. quality review vs. approval vs. filing).
- Confirm the approved typology library, SAR narrative template, and quality checklist source,
  owner, and versioning.
- Wire read-only MCP integrations (case-mgmt, investigation, transactions, KYC, screening,
  records) at deployment.
