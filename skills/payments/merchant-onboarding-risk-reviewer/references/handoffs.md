# Adjacent-Skill Handoffs — merchant-onboarding-risk-reviewer

This skill produces a cited **onboarding risk evidence package** (`review_id`) with a
recommendation band and required conditions, then stops. It does not adjudicate specialist
screens, decide, board, decline, file, or close the case — those are the human adjudicator's
and the specialist skills' responsibilities.

## Upstream / specialist screens (consume their result; route open items back to them)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `sanctions-match-adjudicator` | Sanctions status is `hit`/`pending`; a potential match must be adjudicated (never cleared here) | entity/owner + screening `source_ref` |
| `adverse-media-investigator` | Unresolved adverse media must be investigated and dispositioned | `review_id` + adverse-media `source_ref` |
| `beneficial-ownership-verifier` | Ownership coverage below requirement or a material owner unverified | ownership tree + gap list |
| `kyc-customer-due-diligence-screener` | CDD elements incomplete for the entity/owners | `case_id` + evidence gaps |
| `enhanced-due-diligence-packager` | High-risk geography / PEP / outsized activity requires an EDD package | `review_id` + fired findings |
| `credit-memo-drafter` | Requested processing limit drives material credit exposure needing a credit write-up | merchant + requested limit |

## Downstream (route the human/reviewer to)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `payment-fraud-case-investigator` | Application evidence suggests a fraud ring / prior-processing fraud needing investigation | `review_id` + findings |
| `real-time-payment-risk-monitor` | After a human boards the merchant, post-onboarding transaction monitoring | boarded merchant id (set by the boarding system, not here) |
| `stablecoin-payment-controls-reviewer` | Business model involves stablecoin/crypto settlement controls | merchant + business model |
| `dispute-operations-assistant` | Chargeback/dispute posture is part of the risk picture | merchant + history |

## Human / operations handoff (no catalog skill)

The **onboarding decision itself** — approve, approve-with-conditions, decline, or request
more information — belongs to the merchant-risk adjudicator or the delegated authority /
risk committee, recorded through the permission/approval broker. This skill hands them the
evidence package and recommendation; it never makes or records the decision.

## Duplicate-execution prevention

- This skill computes and evidences **findings and a recommendation only**; it must not
  adjudicate a sanctions/adverse-media hit, decide, board, decline, file, or close — those
  belong to the specialist skills and the human adjudicator.
- Specialist and downstream skills reuse the `review_id` evidence rather than recomputing
  the onboarding findings.
