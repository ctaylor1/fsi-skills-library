# Controls — retirement-income-scenario-modeler

- **Risk tier:** R3 — regulated / control decision support. **Action mode:** Draft-only; no
  system-of-record change.
- **Human approval:** `required` — a licensed advisor and the client must adjudicate any
  recommendation or decision (with a suitability / Reg BI review where a recommendation
  follows) before any plan change, claiming election, product purchase, trade, or write to the
  CRM / book of record. The model is **evidence for a human decision, never the decision.**

## Prohibited (fail closed)

- No **recommendation** to retire, claim Social Security, delay, annuitize, convert, buy a
  product, or adopt a specific withdrawal rate / claiming age / strategy — and no implication
  of one.
- No **guarantee** of income, return, or that assets will last; no "your money will not run
  out"; no **probability of success presented as a promise**. Results are a **range**.
- No **personalized investment, tax, insurance, or legal advice**.
- No **regulated decision, case closure, suitability sign-off, filing, trade, posting, or
  system-of-record write** — these are licensed-human / client actions.
- No **assumption without provenance**; no return, inflation, tax rate, tolerance, or scenario
  delta bent to make a plan "succeed" or to reach a wanted answer.
- No **hiding a depletion / shortfall** — a plan that runs short is a valid, required finding.

## Required output screens (`scripts/validate_output.py`)

- Every scenario ties out, re-derived independently (not trusted from the pack):
  per-account `end == (begin - gross_withdrawal) * (1 + return)`; year-to-year balance
  continuity; funding identity `guaranteed_net + net_withdrawal + shortfall - surplus ==
  spending`; tax identity `net_withdrawal == gross_total - tax_portfolio` and
  `tax_total == tax_portfolio + tax_guaranteed`; portfolio totals equal the sum of accounts;
  no negative balance and no withdrawal exceeding the begin balance. The engine computes the
  same tie-outs the same way (an independent re-derivation from the emitted rows, not a
  self-comparison) and reports them per scenario in `tieouts` and in
  `model_checks.all_tieouts_ok`; on top of its own re-derivation, `validate_output` also
  **fails closed if the pack self-reports a tie-out failure** (`all_tieouts_ok` false, or any
  scenario `tieouts.*_ok` false) — a model that flags its own formula tie-outs as broken is
  never presented.
- `base`, `favorable`, `adverse` present and monotonic: terminal portfolio value
  `adverse <= base <= favorable`; total shortfall `favorable <= base <= adverse`.
- Every `assumptions_register` entry has a non-empty `provenance` **and** `citation`.
- `model_id` and `inputs_hash` present (reproducibility).
- No advice / guarantee / regulated-decision / closure / filing language in the author
  narrative (regex screen).
- Standing disclaimer present (see SKILL.md output contract).

A **non-compliant pack fails closed** (`evals/files/retirement_pack_noncompliant.json`,
`expect_exit 1`): it trips the roll-forward tie-out, non-monotonic scenarios, an unsourced
assumption, advice/guarantee/decision language, and the missing disclaimer. A second fixture
(`evals/files/retirement_pack_selfreport_tieout_fail.json`, `expect_exit 1`) is numerically
sound and monotonic in every respect but **self-reports a tie-out failure**
(`model_checks.all_tieouts_ok` false and an adverse-scenario `roll_forward_ok` false); it
must fail closed on that self-reported integrity failure alone.

## Data classification, privacy, records

- **Highly Confidential (customer NPI/PII).** A retirement plan embeds financial, longevity,
  and family data. Treat the model, its inputs, and `model_id` as need-to-know; use
  de-identified household identifiers in artifacts.
- Retain the model, its assumptions register, and `config_version` per records policy; log the
  read and any advisor adjudication.

## Reproducibility & change control

`inputs_hash` binds the model to the exact numeric assumptions; the `config_version` binds the
returns, inflation, tax rates, and scenario deltas. Re-running the same inputs and config
reproduces the same `model_id` and the same numbers. Changing an assumption changes the hash —
the audit trail shows what moved.

## Separation of duties

Building the model (this skill) is separate from independently reviewing it, from the
suitability / Reg BI review, and from advising or deciding with the client. The model is a
draft input to a human's judgment, never a substitute for it.
