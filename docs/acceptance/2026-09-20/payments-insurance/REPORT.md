# Existing Payments and Insurance acceptance review — 2026-09-20

**Bounded review found no new implementation defect.** Payments Phases 1–4 and Insurance Phases 1–3 have retained implementation and local verification evidence. This pass verified historical evidence integrity and selected current behavior. It does not establish qualified professional acceptance, source authenticity, legal applicability, broad model reliability or production readiness. Insurance Phase 4 is being authored concurrently and is excluded from this review.

## Findings requiring current-status housekeeping

1. **Superseded failure remains in the current tracker.** `STATUS.md` Payments Phase 4 section says the insurance-router metadata failure remains and a clean whole-repository pass is not claimed. The later Insurance Phase 3 record reports all 362 passing. This review executed the exact formerly failing method, `test_spec_cards_reproduce_insurance_metadata`, and it passes. Update current status with the later checkpoint; preserve the historical Payments validation README/logs and their truthful recorded failure.
2. **Historical source snapshots are not current release manifests.** The final Payments Phase 4 source manifest matches 1,014/1,017 files; only `README.md`, `STATUS.md` and `docs/SOURCES.md` differ. The Insurance Phase 3 source manifest matches 1,241/1,242 files; only `STATUS.md` differs. The implementation packages and helpers in these snapshots match at the time of inspection. Earlier phase source manifests naturally differ because later phases modified those sources. They should not be regenerated to erase history. A new final checkpoint should capture the new scope and fresh validation.
3. **Insurance Phase 4 queued wording needs closeout updating.** The roadmap and two STATUS entries still say queued/not started. This is expected at the beginning of the active implementation, not a completed Phase 4 defect. Update after its own verified closeout.

No other unresolved actual implementation defect was demonstrated in this bounded pass. Historical wrong outputs are intentionally retained alongside explicit repairs and retests; their presence does not by itself mean the defect remains. Insurance Phase 1 correctly discloses that three evaluators also authored repairs and their later replays were author verification, not a second independent acceptance review.

## Evidence integrity and executable confidence

- **4,187 historical manifest entries match exactly:** Payments P2 1,140; P3 741; P4 651; Insurance P2 633; P3 1,022. All five artifact manifests have zero missing or changed artifacts.
- **728 additional Phase 1 records match:** 617 Insurance retained forward files and 111 Payments records/Phase 1 implementation files captured in the Phase 4 pre-turn baseline. Total checked historical evidence entries: **4,915**.
- Current Payment bundles pass: **39 contract packages; 23 foundation packages plus two dispute extensions**, zero drift.
- Insurance Phase 2 preserved-input replay: **20 cases, 60 native checks, zero failures**, unchanged input hashes.
- Insurance Phase 3 preserved-input replay: **46 cases, 138 native checks, zero unexpected failures**, unchanged input hashes and all 46 results equal the independently reviewed JSON, including the intentional malformed-input rejection. Replays reproduce existing evidence; they are not new independent professional judgments.
- The formerly failing metadata regression passes. A whole-repository suite was not rerun by this bounded reviewer; root owns the new final checkpoint.

`historical-manifest-audit.json`, `phase1-evidence-audit.json`, `checkpoint-commands.json`, and the two replay directories retain exact checks. Hashes demonstrate local content identity only.

## Three fresh native requests

The reviewer authored all three fictional cases from public SKILL instructions, input schemas and domain rules without opening target test fixtures or goldens. Expectations and inputs were frozen before CLI execution. No native request needed schema adaptation or repair. Historical phase reports were separately read for the acceptance audit; the review therefore does not claim blindness to all earlier audit conclusions.

| Scenario | Independent expected business result | Observed |
| --- | --- | --- |
| FedNow master-account funding with holds, a reservation, later firm credit and forecast receipts | USD600 opening available; base earlier shortfall USD200 despite ending USD100; failed-funding end -200; 25% outgoing stress peak shortfall USD475 and end -175; forecast USD500 does not fund the path | All expected chronology and amounts match. Gaps visible; no authority or transfers. |
| Settled USD7,500 claim obligation reviewed for closure and repeat payment | Same settled transaction blocks repeat-payment review while zero reserve, complete obligation reconciliation and assigned reopening owner permit draft closure review | Payment blocked; closure ready for authorized review; payment/closure/reopening all unexecuted. |
| Insurer internal capital bridge with stressed zero denominator | 100+20-10=110 available, requirement50, base ratio220%; normal stress80/60=133.333…%; invalid stress retains negative available -40 and zero requirement, withholds ratio and reports an issue | All expectations match; denominator name preserved; no regulatory action or solvency certification. |

**9 native CLI calls and 40 independent assertions passed.** `commands.json` contains argv/exits/stdout/stderr; `independent-assertions.json` maps expected to observed values. All 4 frozen input/expectation files and 57 inspected public/source files remain unchanged in `freeze-readback.json`. Source hashes were captured without reading target domain implementation to construct expectations.

## Acceptance work that remains separate

| Gate | Existing evidence | Still required for reliance |
| --- | --- | --- |
| Structural and deterministic | Dated phase sweeps, native examples, standalone/package checks, reproducible targeted replays | New final checkpoint after Insurance Phase 4 and any other current repairs |
| Model behavior and extraction | Bounded agent routing and synthetic native cases; planned natural-language cases are distinguished from executed runs | Broader source-to-input and report interpretation evaluation, representative holdouts and actual target-agent behavior |
| Professional and institutional sources | Primary orientation maps, explicit method limits and supplied owner/source fields | Named qualified payment/country/rail/legal/treasury and insurance/actuarial/claims/control owners reviewing realistic institutional cases; current licensed rules/contracts/profiles and permitted source integration |
| Distribution and deployment | Bundled offline helpers, draft/no-action fields, explicit native-input handoff examples | Source-workbook reconciliation as applicable; target-host acceptance; connector/source identity, permissions, authentication, revocation, idempotency, recovery, monitoring and change control where operational deployment is proposed |

These skills perform offline analysis. No payment, claim action, regulatory submission, connector deployment, source authentication, branch merge, release or version bump was performed by this review. The inspected branch is `feature/financial-services-expansion`.

Evaluator tooling corrections are disclosed in `reviewer-corrections.md`; none changed a case, expectation or repository source.
