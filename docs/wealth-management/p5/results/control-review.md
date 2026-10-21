# P5 independent control repair replay

Reviewer: `/root/governance_map`. Recorded October 5, 2026, 02:10:24 UTC
(October 4 in America/New_York). This reviewer authored the audience component,
but did not author the evidence or combined quality components. This is a bounded
code review and fresh synthetic replay, not professional or production acceptance.

Reviewed canonical files:

| File | SHA-256 |
| --- | --- |
| `shared/wealth-quality/evidence_gate.py` | `6ce7cc08f3020eb0ae44fe184b8a38024187081ea38929d11a7b3e76beff1801` |
| `shared/wealth-quality/quality_gate.py` | `21d3163cfb7c694fa2536ebd223834c90c3c9abe4291751e94f4a29c31e82b93` |

The initial independent probes reproduced two defects. A receipt with
`identity_authenticated: false` changed to integer `0` passed validation under
Python equality despite retaining its old digest. Separately, fresh source-bound
derivation requests obtained `reviewed-for-draft` for mathematically incorrect
zero results: the product of `1e-1000100`, and the sum
`1e30 + 1e-30 - 1e30`. Neither finding was inferred solely from authored tests.

After the author's repair signal, fresh independent execution confirmed:

- Typed receipt substitution `false` to `0` is rejected with the old digest.
- Both complete extreme-arithmetic requests now produce blocked receipts.
- Nonterminating ratio `1/3` is blocked under the documented exact-arithmetic
  contract; exact ratio `3/8 = 0.375` and sum
  `18250.25 - 250.15 = 18000.10` remain accepted.
- Explicit two-place rounding `1.235` to `1.24` remains accepted.
- A combined quality request without a separate draft review remains
  `pending-draft-review` with no recipient draft.
- A synthetically supplied separate review allows the exact recipient bytes to
  reconstruct. Replacing `action_taken: false` with `0`, or appending a new
  assertion to those bytes, causes validation failure.
- A fresh 1,401-block dependency chain reaches the pending review state without
  a recursion failure and retains all included blocks.
- Malformed combined validation inputs return errors rather than throwing.

These probes used `/private/tmp/fsi-p5-venv/bin/python -B` with bytecode writing
disabled. The separate authored handoff suite also passed 20 tests after the
independent replay. The audience component passed 35 tests and scoped Ruff;
these are author checks, not independent audience acceptance.

Both independently demonstrated evidence defects are closed for the inspected
hashes. Exact hashes and arithmetic do not establish source authenticity,
semantic entailment, complete disclosure dependencies, reviewer identity,
permission authority, or deployment access. Those boundaries remain explicit.
The subsequent P5 real-model case assessment must inspect actual files and traces;
this control replay supplies no model-quality pass and changes no frozen rubric.
