# Controls — credit-surveillance-packet

- **Risk tier:** R2 — analytical / drafting support (no binding decision). **Action mode:**
  Draft-only; no system-of-record change.
- **Human approval:** `external-delivery` — human approval is required before the packet is
  delivered (to a PM/desk/committee) or written to any system of record. Internal analytical
  iterations may be reviewer-sampled.

## Prohibited (fail closed)

- **Assigning, deriving, implying, or opining on a credit rating.** Agency ratings are
  **reported** only; `rating_action` stays `reported-only` and `validate_output` fails on any
  other value or on assigned-rating language.
- **Forming, altering, or restating an investment thesis.** `thesis_action` stays `unchanged`.
- **Recommending or changing a position or trade** (buy/sell/add/trim/exit/overweight), or any
  personalized investment advice / guarantee ("risk-free", "can't-lose"). `position_action`
  stays `none`.
- **Determining covenant compliance or headroom, or extracting covenant terms.** Flag the
  change; hand detail to `credit-terms-covenant-extractor` and compliance determination to a
  human.
- **Sending, circulating, emailing, submitting, or marking the packet final.** Draft only.
- **Fabricating** any figure, spread, comp, rating, or covenant conclusion; **restating** a
  ratio the computation does not support (tie-out break).
- **Unsupported / unapproved claims** — any assertion without a resolvable `source_id`, or a
  `market` / `rating-agency` source not marked approved.

## Draft states (this skill may set only these)

`drafting` → `needs-data` (missing/unapproved inputs) | `draft-ready` (validated, approvals
recorded, awaiting human delivery). It may **not** set `rated`, `thesis-updated`, `positioned`,
`delivered`, or `filed`.

## Required output screens (`scripts/validate_output.py`)

1. All nine required template sections present and non-empty (template fidelity).
2. Every assertion resolves to a source; external (market/rating-agency) sources are approved.
3. Metric tie-outs hold (no leverage/coverage tie-out break); no open block-severity flag.
4. `rating_action == reported-only`, `position_action == none`, `thesis_action == unchanged`.
5. `preparer` and `reviewer` approvals are **recorded**.
6. No prohibited language (rating assignment, thesis change, position/trade recommendation,
   covenant compliance interpretation, advice/guarantee, or premature delivery).
7. Standing draft-only note present.

## Segregation of duties

Drafting the surveillance packet (this skill) is distinct from **review**, from the **rating**
process, from any **thesis** change, and from any **position/trade** decision. The same person
must not both prepare and record the reviewer sign-off; ratings, thesis, and positions are set
by humans/committees, never by the drafter or the skill.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Issuer research frequently touches MNPI;
  restrict access to the entitled research/deal team, honor information-barrier / wall-crossing
  controls, and never disclose surveillance findings outside the entitled group.
- Retain the draft, its traceability appendix, source citations, and the template/metric-config
  versions with the issuer record. Log every source read and every packet generation with the
  preparer identity for recertification and audit. Reference the shared observability and
  data-governance services rather than duplicating them (see docs/SHARED-SERVICES.md).
