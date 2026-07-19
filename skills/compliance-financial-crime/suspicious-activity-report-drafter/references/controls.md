# Controls — suspicious-activity-report-drafter

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The package is a *fact-based draft with evidence and an advisory
  review path* for a human.
- **Human approval:** `required` — before the file/no-file determination, any SAR filing or
  e-filing, any case closure/disposition, and any system-of-record write. Assembling the draft
  is not itself an approval or a determination.

## Prohibited (fail closed)

- **The suspicion / file-no-file determination** (that belongs to the human compliance
  decision on a human-adjudicated investigation).
- **Filing or e-filing a SAR**, **submitting anything to FinCEN**, or any regulatory submission.
- **Case closure or disposition**, or writing any filing/case status of record.
- **Sending or submitting** the package (draft-only) and **writing a system of record**.
- **Speculation or conclusions of guilt** — the narrative is fact-based; no "obviously",
  "must be laundering", "the subject is a criminal", or guaranteed determinations.
- **Drafting from an unadjudicated case** — if the case is not approved for SAR drafting, the
  package is `blocked` and routed to the investigator (hard boundary).
- **Tipping-off**: any customer-facing content revealing SAR or monitoring activity.
- **Sanctions/adverse-media/UBO conclusions** — route to the specialist; package the evidence.

## Packaging states (this skill may set only these)

`blocked` (hard boundary — case not approved for SAR) | `needs-evidence` (any gap: tie-out
break, uncovered party, unsupported typology, incomplete/uncited 5W+H, uncited fact) |
`ready-for-quality-review` (complete, tie-outs reconcile, no hard boundary). It may **not** set
`filed`, `submitted`, `closed`, `dispositioned`, `no-sar`, or any determination/filing state.

## Required output screens (`../scripts/validate_output.py`)

- `packaging_status` is one of the three allowed draft states.
- **Template fidelity:** all fourteen required sections present (see
  [../assets/output-template.md](../assets/output-template.md)).
- **No unsupported claims:** every chronology event, the narrative, the evidence index, the
  investigation rationale, and every supported typology carry citations.
- **Tie-outs reconcile:** a `ready-for-quality-review` package has a passing amount/chronology
  tie-out, full party coverage, a complete 5W+H narrative, and supported typologies; a claimed
  `pass` must actually reconcile (computed vs. declared total, period, and count).
- **No speculation:** conclusions of guilt / unfounded certainty are blocked.
- **Language screens:** no determination/closure language (`no SAR required`, `case closed`,
  `cleared`, …); no filing language (`filed the SAR`, `e-filed`, `submitted to FinCEN`, …); no
  send/submit language.
- **Required approvals recorded:** the ledger covers every required role; any `obtained` entry
  names an approver **and** date (no fabricated sign-off).
- **Hard-boundary consistency:** a hard boundary forces `blocked`.
- **Standing note present** (draft-only / no-determination / no-filing limitation).

## Segregation of duties

Drafting entitlements are distinct from the investigation that concludes suspicion, from SAR
quality review, from MLRO/BSA compliance approval, and from filing. The same person/skill must
not both draft the SAR and approve or file it.

## Data classification, privacy, records

- **Restricted (AML/BSA).** SAR-confidentiality and tipping-off controls apply — the draft and
  its existence stay within the authorized SAR workflow.
- Mask subject/account identifiers to what the narrative requires (names and identifiers are
  masked in the package).
- Retain the draft, citations, tie-outs, and config/template versions per BSA recordkeeping;
  log the drafter identity on every read and every package assembly.
