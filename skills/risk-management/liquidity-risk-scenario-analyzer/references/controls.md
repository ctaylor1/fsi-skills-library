# Controls — liquidity-risk-scenario-analyzer

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Read-only analysis.
- **Human approval:** `required` — Treasury/ALCO adjudication before any regulated liquidity
  decision, limit-breach disposition, funding/collateral action, regulatory filing, or write to a
  case/system of record; and before external delivery of the pack.

## Prohibited (fail closed)

- No **regulated liquidity determination** or statement that the institution **is** (non-)compliant,
  in breach, or adequately funded as a matter of record.
- No **funding, collateral, or limit action** or execution: drawing facilities, repo/monetizing
  HQLA, pledging/selling collateral, raising/reducing/waiving a limit, or clearing a breach.
- No **regulatory filing** (LCR, NSFR, FR 2052a, internal-liquidity-adequacy submission) — route to
  the appropriate packager/human.
- No **case closure** or suppression of a finding/breach outside approved deterministic logic.
- No **assumption tuning to pass** a limit; use only the versioned scenario/limit config.
- No **opaque scoring** presented as decisive; metrics and findings are explainable and evidenced.

## Required output screens (`scripts/validate_output.py`)

- Every fired finding (per-scenario + structural) has ≥1 cited evidence row.
- `overall_assessment` equals the deterministic severity → band mapping.
- Findings tie out to the numbers: `survival_horizon_days < min` ⇒ `survival_horizon_breach`;
  `coverage_ratio < min` ⇒ `coverage_ratio_breach`, per scenario.
- No regulated-decision / closure / filing / commitment language (regex screen: "we will
  draw/monetize/file/submit", "ALCO has approved", "activate the contingency funding plan",
  "file the 2052a", "breach is closed", "limit has been waived", "final determination",
  "we are compliant", "certify the institution", etc.).
- Standing disclaimer present.
- Proposed contingency options supplied whenever the band is not "Within appetite", framed as
  adjudication-required proposals — never execution statements.

## Model risk / conduct

- Behavioral assumptions (runoff, rollover, inflow realization, haircuts) are model inputs governed
  by the config owner; changes are versioned and, where material, subject to model validation.
- Describe concentrations and gaps factually; do not characterize counterparties.

## Data classification, privacy, records

- **Confidential** treasury/risk data; keep customer NPI out of the analysis. Mask counterparty
  identifiers not needed for a finding.
- Retain analysis + citations + `config_version` per records policy; log read + adjudication/delivery
  approval.

## Reproducibility

`analysis_id` binds the output to the exact position inputs, scenario set, and **config version**;
re-running with the same inputs and config reproduces the metrics, findings, and band. The compute
script's `--selftest` asserts determinism (two runs identical) and evidence completeness.
