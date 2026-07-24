# Domain Rules — payment-api-log-diagnostic-pack

The error-taxonomy config governs (versioned). Orientation: classify failures, quantify, and
suggest human-run checks — never remediate.

## Redaction (runs first)
- Any 13–19 digit sequence (candidate PAN) in `message`/free-text is replaced with
  `[REDACTED-PAN]` **before** classification, aggregation, or output.
- Any explicit `pan`/card field is dropped and never echoed.

## Classification (deterministic)
| Step | Rule |
| ---- | ---- |
| Category | `taxonomy.code_map[error_code]`; unknown code → `unclassified` |
| By-category counts | Count of entries per category |
| By-endpoint counts | Count of failing entries per endpoint |
| Top endpoint | Endpoint with the most failures (ties broken by name for determinism) |
| Suspected cause | Category with the most failures (ties broken by name) — a *suspected* cause |
| Next checks | `taxonomy.next_checks[category]` — human-performed checks, never actions taken |

Config (`code_map`, `next_checks`) is a **versioned contract**; the output records the version.

## Hard boundaries (fail closed)
- Never change config, rotate keys, disable rules, or deploy fixes.
- Never guess a category; never emit cardholder data.
- Suspected cause and next checks are advisory evidence for a human, not a remediation.
