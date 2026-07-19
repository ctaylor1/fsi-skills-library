# Domain Rules — suspicious-activity-report-drafter

Orientation references: BSA/FinCEN SAR rules and the FinCEN SAR **narrative guidance** (a
clear, complete, chronological account answering **who / what / when / where / why / how**);
SAR-confidentiality and tipping-off prohibitions; SAR filing timelines (initial filing
generally within 30 calendar days of initial detection, up to 60 where no subject is
identified). The firm's SAR program standard and its **approved typology library, output
template, and quality checklist** take precedence and are versioned contracts. This skill
drafts a fact-based narrative and packages evidence; it makes **no** regulated determination
and performs **no** filing.

## Required package sections (all fourteen; a missing/uncited section is a gap)

The fourteen sections of [../assets/output-template.md](../assets/output-template.md): filing
header (context only), subjects & parties, accounts & instruments, activity summary,
chronology, amount & chronology tie-out, typology assessment, SAR narrative (5W+H), evidence
index, investigation rationale, recommended review path, approvals, sources & citations, and
the standing note.

## Fact-based narrative (5W + How)

The narrative answers all six elements, each grounded in cited evidence:

| Element | What it states (facts only) |
| ------- | --------------------------- |
| **Who** | The subject(s) and counterparties (masked), roles, relationships |
| **What** | The suspicious activity: instruments, aggregate amount, counts |
| **When** | The activity period (ties to the chronology span) |
| **Where** | Accounts/branches/jurisdictions involved |
| **Why** | Why the activity is suspicious, tied to observed indicators |
| **How** | The modus operandi — how the funds moved |

**Prohibited speculation:** no conclusions of guilt or unfounded certainty ("obviously",
"must be laundering", "the subject is a criminal", "we are certain"). State observed facts and
let them speak; the file/no-file determination is the human's.

## Tie-outs (deterministic, must reconcile)

| Tie-out | Rule |
| ------- | ---- |
| **Amount** | `sum(transactions.amount)` == `activity.aggregate_amount` (± 0.005) |
| **Chronology** | `min/max(transaction.date)` == `activity.period.from/to` |
| **Count** | `len(transactions)` == `activity.transaction_count` |

A break sets `amount_tie_out.status = break` and forces `needs-evidence`. A claimed `pass`
must actually reconcile — `../scripts/validate_output.py` recomputes the equality.

## Party coverage & typology consistency

- **Party coverage:** every party referenced by a transaction (`subject_ref`,
  `counterparty_ref`) must appear in `subjects`. An uncovered party is a gap.
- **Typology consistency:** each declared typology must exist in the approved typology library
  and have **all** its `required_indicators` present in the case's `observed_indicators`. An
  out-of-library or under-evidenced typology is a gap — never asserted as supported.

## Packaging status → recommended review path (advisory)

| Status | `recommended_review_path` |
| ------ | ------------------------- |
| `blocked` (case not approved for SAR) | `hold-pending-investigation` |
| `needs-evidence` (any gap) | `return-for-evidence` |
| `ready-for-quality-review` (complete) | `quality-review-and-compliance-approval` |

The review path is a **recommendation**; the SAR quality reviewer and MLRO/BSA Officer choose
and record the actual disposition, the file/no-file decision, and any approvals.

## Hard boundaries (fail closed)

- No **suspicion / file-no-file determination**, and no communication of one.
- No **SAR filing/e-filing**, **FinCEN submission**, or regulatory submission.
- No **case closure/disposition** and no **filing/case status of record** write.
- No **system-of-record write** and no **send/submit** of the package (draft-only).
- No **speculation or conclusions of guilt** — fact-based narrative only.
- No **drafting from an unadjudicated case** — `blocked`, route to the investigator.
- No **sanctions/adverse-media/UBO conclusion** — route to the specialist.
- No **tipping-off**: never reveal SAR/monitoring activity to the customer.

## SAR package — required contents

Durable `case_id`; the fourteen cited sections above; the fact-based 5W+H narrative; the
amount/chronology tie-out; the typology assessment against the approved library; an advisory
recommended review path and specialist routes; an approval ledger listing every required role
with status; an aggregate sources-and-citations list; and the standing note (draft-only /
no-determination / no-filing limitation).
