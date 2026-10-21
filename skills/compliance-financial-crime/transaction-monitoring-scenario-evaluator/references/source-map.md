# Source map and native contract

Supply run/as-of/configuration, scenario parameters, explicit escalation intake, data-as-of, staleness policy, a complete-ledger assertion, observation period, a single currency and currency on each transaction. Require unique transaction IDs, nonnegative finite amounts, valid dates within observation and assessment dates, and flow direction. Cash scenarios need instruments; geography needs countries; velocity needs a positive baseline for the same period. Missing data or unknown/future/stale freshness creates NOT_EVALUABLE results and cannot yield a clean monitor recommendation.

Every subject receives `rule_results` for every configured scenario, `evaluation_complete`, and any observed indicators. PASS only means that supplied data did not cross that scenario threshold. It is not a clean AML finding. Fingerprints include evidence, period/as-of and configuration; changed evidence is new.

The synthetic intake example is `../evals/files/run_example.json`. It is not a real customer, approval or regulatory event. Native results carry a hash of every supplied input field and source_truth=unverified. Retain original input outside the output; validate with --input. Authenticated source retrieval, entitlements and producer identity must be supplied by deployment systems.


### Evidence-bound replay identity

Velocity uses the same inclusive maximum-limit classification as the ratio scenarios: observed >= baseline × multiplier is BREACH; an observed value at the configured warning boundary is WARN only when below the breach limit.

Fingerprint version `scenario-evidence-v2` binds the complete supplied subject record (including every transaction ID, date, source reference, currency, profile, freshness and observation/baseline period), the actual evaluated rule content, all other supplied assessment context (including as_of, config_version and freshness policy), and the emitted evidence. It uses a full canonical SHA-256 digest. Changing a ledger while preserving aggregate totals is new evidence and cannot be suppressed by the prior fingerprint.

Only invocation `run_id`, prior `open_cases`, and unrelated subjects/rules are excluded from an indicator's evidence identity. This permits the exact same evidence and policy to deduplicate on a later invocation without circularly hashing the dedup baseline. The separate native input_hash still binds the complete original input. Fingerprints are versioned; old aggregate-only fingerprints cannot suppress v2 evidence. There is no persisted case state, source authentication or live alert suppression.
