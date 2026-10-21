# Independent business workflow review

On 2026-09-21, reviewer `am_investment` completed **299 current assertions across 54 requests and 126 native commands**, with no current failures. Coverage spans five new packages and the RFP, institutional manager diligence, and three committee modes in three expanded packages. This is bounded synthetic evaluation; it does not establish source truth, authenticated approval, professional acceptance, production readiness, or complete jurisdictional coverage.

The [current review record](current-replay/review.json) contains exact requests/results, commands, assertions, and package file hashes. Reproduce with `python3 -B docs/asset-management/phase2-validation/business-independent/replay_review.py`. The script writes only its evidence directory. Subsequent implementation changes require replay; this record identifies the code observed at its timestamp.

## Independent expectations

The original twelve requests were created from the skill instructions, schemas and domain rules before execution, without copying author fixtures. Expected arithmetic was independently calculated: reconciled AUM and fee contributions; product break-even, merger payback and closure residual; distribution fee and conflict controls; service deadlines; investor capital and relative returns; RFP commercial margin and approval separation; institutional capacity and fees; and committee scenario, allocation and concentration controls. Native output reconstruction is a separate integrity check, not the numerical oracle.

Adversarial requests cover malformed dates, unknown modes, restricted source audiences, future source knowledge, altered source claims, missing independent evidence, blank/self approval actors, and completed events after their knowledge cutoff. Detached output checks reject altered authority, changed originals and missing originals. Restricted content, identifiers and provenance remain absent from outputs in the tested cases.

## Findings and replay

- **Service resolution alerts — repaired.** An unsupported claimed resolution became `resolution-unverified` but incorrectly cleared overdue and SLA flags. The original [service output](service-output.json) remains unchanged. Both flags are retained in [the current replay](current-replay/service-output.json).
- **Completed-event chronology — repaired.** RFP approvals, actual economics/performance periods and client report delivery could postdate the knowledge cutoff despite earlier source-known labels. The [RFP before-repair evidence](chronology-before-repair/review.json) and [four additional observations](additional-chronology/observations.json) remain unchanged. Exact-input replays now reject or withhold those observations; future contractual due and effective dates are distinct from completed events.
- **Input documentation — clarified.** Lifecycle gate source approvals and nested RFP/diligence criteria, operators and actor requirements were initially underspecified. The author expanded their schemas. A separate [approved-gate case](current-replay/lifecycle-approved-gate-evidence-output.json) retains a supplied passed gate and an explicit unknown gate without authorizing a decision.

Original requests supplied a descriptive `mode` to the five single-method packages. The author subsequently made these selectors explicitly unsupported. Current copies remove only that field; original inputs/results remain historical. The expanded packages retain their documented modes. One reviewer expectation was corrected: an incomplete economics book produces unavailable aggregate totals, consistent with its documented completeness rule, while retaining the supported individual product. The initial interrupted attempt and correction are recorded in the replay methodology.

The original historical assertion set retains its two service failures; it is not presented as passing. No business package files were edited by this reviewer. Legacy modes of the three expanded packages are outside this independent forward review.
