# R3 offline controls

The builder always emits approval pending and execution blocked. Invalid input produces a rejected blocked artifact with no steps and command exit 1. The output validator accepts a correctly rejected artifact as a valid record of rejection.

The plan hash covers the complete plan apart from the hash itself: source request, exact before/after, payment identity, amount/currency, policy/version/role, screening, steps, and limitations. The validator also recomputes the expected proposal from the embedded source. Rehashing an edited output does not make it consistent with its original source.

This is content-integrity checking, not authentication. An attacker able to replace all source data can create a different internally consistent proposal; it still has no execution authority. Every claimed approval token, approved state, approver, or executed step fails this offline output contract.

Idempotency scopes are stable across replanning of the same payment/action, but no execution ledger is present. Do not claim duplicate prevention in a bank system. A future executor would require authenticated exact-plan approval, role/limit/expiry checks, current state and screening, durable deduplication, race/timeout handling, independent outcome evidence, and compensation/finality controls. Those are unimplemented requirements, not existing functionality.

Run `scripts/regression_tests.py`; no live execution tests exist because no executor is shipped.
