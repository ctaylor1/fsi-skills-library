# Resilience and modernization review criteria

The module inspects supplied test artifacts; it does not run a distributed system or
retrieve the reference. A declared pass must include steps, observations, inspection
identity/date and exact-content binding. Report source authentication separately.
No summary score suppresses a failed invariant or missing scenario.

- Duplicate events and crash-after-commit: one financial effect; retrieve durable result.
- Changed payload under an old key: reject rather than overwrite a previous instruction.
- Lost events: detect a gap and open a reconciliation break; silence is not success.
- Delayed/out-of-order: preserve original identity and prevent state regression.
- Network partition: fence the isolated writer; do not infer two independent writers are safe.
- Uncertain money: authoritative status and reconciliation, zero blind resends, retained unknowns.
- Cutover: tie the in-flight inventory to exactly one financial owner.
- Rollback: preserve settled effects and pending ownership; reroute new intake only.
- Recovery: owned reconciliation exceptions, exercised support handoff and observed monitoring.

These are local baseline engineering criteria, not a complete certification standard.
Tailor mode-specific tradeoffs in the narrative: hub routing authority; orchestration
provider ambiguity; cloud/mainframe ordering and commit boundaries; ledger balancing;
active-active fencing/consensus and partition behavior. Design proposals remain distinct
from observed tests. No no-gap result grants production approval.
