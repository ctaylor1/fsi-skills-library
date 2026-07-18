# Controls — corporate-action-interpreter

- **Risk tier:** R2 — analytical / informational. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the interpretation is delivered
  to a client or written to a system of record; not required for the user's own read.

## Prohibited (fail closed rather than do these)

- No **investment advice, recommendation, or opinion** on which option to elect, whether to
  participate, tender, subscribe, accept, or reject.
- No **personalized tax advice or result** ("tax-free to you", "you will owe", cost-basis
  restatement, lot/wash-sale treatment). Tax *categories* may be named neutrally; the
  personalized determination routes to a licensed tax professional.
- No **election, tender, subscription, or instruction** — the skill never submits or records
  a response; that is the R4 `corporate-action-election-assistant`.
- No **inventing** missing terms (ratios, per-share rates, cash-in-lieu rates) — flag them
  for operations review.
- No **overriding** the official notice with a user assertion; no **merging** of multiple
  events or securities without explicit confirmation.

## Required prohibited-language screen

`scripts/validate_output.py` scans the narrative, `action_required`, option descriptions,
ambiguities, and notes for (a) advice / recommendation-on-election phrasing, (b) personalized
tax advice, and (c) binding-election / instruction language. Any hit **fails closed**. The
screen deliberately allows the neutral disclaimer wording ("not investment or tax advice",
"may elect"). A standing disclaimer must be present:
"Informational interpretation only; not investment or tax advice, and not an election or
instruction; verify against the official notice and confirm any election through your
custodian or operations team."

## Deterministic tie-outs

- Each stated entitlement must **recompute** from its terms and the eligible quantity
  (`value == quantity * ratio_new / ratio_old` for shares, `quantity * rate_per_share` for
  cash) within tolerance; whole and fractional shares are reported separately.
- Voluntary / mandatory-with-options interpretations must carry an election deadline echoed
  in `action_required`, non-empty options, exactly one default, and **no** option flagged
  `elected` / `chosen` / `submitted`.

## Data classification, privacy, records

- Classification: **Highly Confidential (customer NPI/PII)** — the eligible position/account.
- Mask account numbers to last 4 in all output. Keep notices and positions within the
  approved environment; never exfiltrate.
- Retain the interpretation + citations per records policy. Log: source read, interpretation
  creation, and any external-delivery approval (who/when).

## Reproducibility

Given the same official notice version and eligible position/as-of, the interpretation must
be reproducible: the `interpretation_id` binds the output to the exact notice, terms,
position, and citations used.
