# Adjacent-Skill Handoffs — coverage-initiation-researcher

This skill orchestrates a **multi-step initiating-coverage draft** and stops at a
draft-complete state (`coverage_id`). It does not build the underlying models itself, and it
never issues an approved rating, price target, or published note. It consumes model outputs
and evidence, assembles the draft, and routes onward.

## Upstream / component skills (call these to produce inputs, then cite their outputs)

| Component skill | Provides | Handoff artifact |
| --------------- | -------- | ---------------- |
| `three-statement-model-builder` | Integrated operating model behind the forecast | model artifact id + `as_of` |
| `dcf-modeler` | Intrinsic DCF value per share for the valuation triangulation | per-share value + citation |
| `comps-analysis-builder` | Trading-comps cross-check and peer multiples | per-share value + citation |
| `scenario-sensitivity-generator` | Scenario / sensitivity ranges around key drivers | scenario table + citation |
| `market-sizing-builder` | TAM/SAM/SOM for the industry section | sized ranges + method |
| `market-landscape-researcher` | Value-chain, competitor, and regulatory map | landscape memo |
| `company-profile-builder` | Company overview / strip page for the business-model section | profile artifact |
| `earnings-results-analyzer` | Latest beat/miss and thesis impact | results memo |

The dossier `sections`, `forecast`, and `valuation` blocks cite these artifacts; this skill
does **not** recompute a DCF, comps set, or operating model — it references them so work is
not duplicated.

## Downstream (route the human/reviewer to)

| Destination | When | Handoff artifact |
| ----------- | ---- | ---------------- |
| `coverage-meeting-preparer` | Preparing to discuss the initiated name with a client/prospect | `coverage_id` + thesis |
| Supervisory analyst (human) | Rating, price target, and Reg AC certification decision | full draft + `coverage_id` |
| Research committee (human) | Approval to publish / initiate coverage | approved draft |
| Compliance / control owner (human) | Independence, disclosure, and MNPI-wall review | draft + source map |

Rating approval, price-target sign-off, publication, and client delivery are **human /
committee actions**, not skills — never invent a skill name for them.

## Duplicate-execution prevention

- This skill assembles and evidences a **draft** only; it must not issue an approved rating
  or price target, publish, or deliver — those belong to the supervisory analyst, the
  research committee, and the delivery/system-of-record step.
- Model skills own their calculations; this skill cites their outputs rather than rebuilding
  them under a different `coverage_id`.
