# Adjacent-Skill Handoffs — credit-terms-covenant-extractor

This skill produces a cited, point-in-time **term extraction** (`extraction_id`) from one
controlled credit document and stops. It does not test covenants, monitor issuers, form a
view, or assemble a review packet. All adjacent skills below exist in
`catalog/skills-catalog.json`.

## Downstream (route the human/analyst to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `covenant-compliance-monitor` | The user wants a covenant **test computed**, headroom tracked, a compliance certificate reconciled, or a potential breach flagged | `extraction_id` + the covenant fields/thresholds (raw, uncomputed) |
| `credit-surveillance-packet` | The user wants **ongoing issuer monitoring/review** (leverage, coverage, liquidity, maturity wall, spreads, ratings, covenant changes) | `extraction_id` + extracted terms + citations |
| `credit-memo-drafter` | The extracted terms feed a commercial **credit memorandum** for underwriter approval | `extraction_id` + fields + citations |
| `credit-risk-portfolio-analyzer` | Terms feed **portfolio-level** quality/concentration/scenario analysis | `extraction_id` + normalized fields |

## Upstream (may call this skill)

`credit-surveillance-packet` hands **covenant/term detail** to this extractor rather than
re-parsing documents itself (see its catalog boundary). Analysts may also invoke this skill
directly against a single document.

## Duplicate-execution prevention

- This skill **extracts and cites** only. It must not compute a covenant test, determine
  compliance, resolve ambiguous language, monitor an issuer, or state an investment view —
  those belong to the skills above and to the human analyst.
- Downstream skills consume the `extraction_id` and its cited fields rather than re-parsing
  the source document, so a term is normalized once and reused.
- `needs_review` items are passed through as-is for human reading; the extractor never
  substitutes a definitive value to make a downstream step easier.
