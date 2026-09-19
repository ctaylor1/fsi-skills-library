# Insurance forward-execution product review — 2026-09-18

Scope: independent practitioner-request execution of four captured packages. All inputs are synthetic. The package instructions, native schemas, transformation code, relevant domain/source references and reserving output template were read. No phase plan, previous audit, test expected answer or repository fixture was used to build these cases. No repository edits were made. No external factual research was needed for the synthetic calculations.

Stable package snapshot: `/tmp/insurance-product-forward-20260918`. `snapshot-sha256.json` records the original 69 package files, including existing Python caches. `snapshot-source-sha256.json` isolates the 68 immutable non-cache files. One copied Python bytecode cache was regenerated during execution; readback verified that every source file remained unchanged. Old package directory names are retained even if the working repository renames them. Every case includes raw request, native input, adaptation notes, native output, command/stdout/stderr/exit-code logs and final output. The four main cases include authored, source-referenced practitioner responses. Authored narrative was bound into each artifact with the package's `build_artifact` before output validation. These results demonstrate deterministic behavior and reviewer reasoning on bounded inputs; they are not professional acceptance or a full actuarial review.

## Primary practitioner cases

| Case | Independently checked result | Native input / calculation / final-output checks | Assessment |
| --- | --- | --- | --- |
| 01 paid reserving | 160/100=1.6; current paid250 ×1.6 = ultimate400; total unpaid400−250=150. Case80 gives reported incurred330 and residual70 if the separately supplied context has aligned basis. | All exit0 | Native paid reserve measure is correctly total_unpaid. Separate case/selected context is not consumed by this schema; final response labels the70 as supplemental reconciliation. Missing large-loss schedule is mishandled as described below. |
| 02 mixed-currency quotes | A annual total USD1,000; B CAD900; FX/equivalence unavailable. | All exit0 | Currency flag, null lowest-cost ID, null spread and partial artifact correctly preserve comparability limits. Final comparison explicitly also currencies the limits and deductibles. |
| 03 historical earned loss ratio | Three in-window losses total USD300,000. Exact inclusive window is2023-09-19 through2026-09-18. Current annual premium100,000 is not the historical earned denominator. | All exit0 | Correctly not_evaluable; no loss-ratio finding or inferred denominator. A separate large-claim finding causes Review and overall partial status. |
| 04 eligible ceded loss | min(12m−5m,10m)=7m; aggregate remaining20m−7m=13m; reinstated7m; premium7/10×2m=1.4m. | Input/calculation exit0; raw output exit1 for the deliberately blank authoring slots; final output exit0 after clause summaries and narrative. | Correct arithmetic and bounded interpretation. The initial output rejection is the documented authoring workflow, not a defect. |

## Confirmed defects and reproductions

### P2 — Missing building limits can still receive an overall comparable quote ranking

Case05 is a natural followup to the currency example: both currencies USD, same period/date, premiums1,000 and900, both building limits explicitly null, both deductibles1,000. The calculator emits `cost_comparison_status: comparable`, `lowest_annualized_total_cost_quote_id: B`, spread100, no comparability flags, and a complete artifact. Both input and final-output validators pass. A broker can compare the supplied premium amounts, but cannot establish equivalent coverage from two missing limits; the package's overall comparability statement and complete status overstate the supplied evidence.

Cause in captured `premium-quote-comparator/scripts/calculate_or_transform.py:198-200`: `coverage_unknown` is raised only if both limit AND deductible are null. Equal null limits otherwise produce no mismatch, and a numeric deductible suppresses the unknown flag. The output validator recomputes the same logic (`scripts/validate_output.py:81-84`), so the defect reproduces and passes.

Replay: run the captured native input validator, calculator and output validator using `cases/05-unavailable-quote-limits/input.json` and `final-output.json`; exact commands and exit codes are in that case's `run-log.json`. Preserve individual premiums, surface each material unknown dimension, and withhold the overall comparable/ranking conclusion until the missing limits are established.

### P2 — Large-loss source absence becomes a clean zero result

Case07 explicitly asks whether large losses distort the paid triangle, sets the threshold to100 in USD thousands, and supplies no claim-level large-loss schedule or completeness declaration. The native output returns `large_loss: {threshold:100,count:0,total:0,claims:[],flagged:false}`, `reserve_analysis.large_loss_flagged:false`, a packageable draft and `artifact.completeness: complete`. Both input and final-output validators pass. The same absence-to-zero behavior also occurred in case01.

Cause in captured `reserving-analysis-assistant/scripts/calculate_or_transform.py:156-164`: omitted `large_losses` becomes `[]`; count, total and flagged state are then asserted from that empty list. The native schema carries no explicit large-loss completeness distinction. The legitimate triangle indication can remain available while large-loss analysis is marked not_evaluable or partial. A missing claim schedule cannot establish no large losses or no distortion. This matters when the analysis is consumed as machine-readable data even if a careful author repairs the prose; case01's authored response expressly avoids the unsupported zero conclusion.

Replay is recorded in `cases/07-no-large-loss-schedule/run-log.json`; the original input and outputs are preserved in that directory.

### P2 — Zero premium incorrectly prevents contractual limit restoration

Case06 changes the optional treaty illustration to an explicitly supplied zero base layer premium, with matching supplied clause text, one reinstatement, 20m aggregate and the otherwise supported pro-rata-on-erosion method. Zero is accepted by the input validator's nonnegative-premium rule. The engine correctly produces7m ceded and zero premium charge, but incorrectly reports `reinstated_amount:0`. The documented overlap formula produces restored amount7m independently of the premium charge: overlap of cumulative erosion(0,7m] with the first reinstatement band[0,10m] is7m; its charge is7m/10m×100%×0=0. Final output validation passes.

Cause in captured `reinsurance-treaty-interpreter/scripts/calculate_or_transform.py:45-48`: `not layer_premium` returns both restoration and premium as zero before calculating the overlap. The output validator's source recomputation reproduces that same result. This is a narrower edge case than the common positive-premium case04, which is correct. The contract's restoration mechanics need to remain independent of whether the premium charge happens to be zero, or the input must explicitly be rejected as unsupported.

Replay is recorded in `cases/06-zero-premium-reinstatement/run-log.json`. The final narrative flags the arithmetic defect; the native calculation values were preserved rather than silently corrected.

## Documentation inconsistency encountered during ordinary authoring

The captured reserving output template still uses a generic `Reported` / `Indicated IBNR` table and `reported` / `ibnr` placeholders at `assets/output-template.md:49-57`, despite the actual paid engine and top-level SKILL scope requiring `paid` / `total_unpaid`. Following the template literally would mislabel case01's150 as IBNR even though separately supplied case outstanding is80. The authored response used basis-specific labels as required by the top-level scope. The template's severity and frequency labels also call the supplied counts ultimate counts at lines65-66; this contradicts the migration reference's explicit supplied-count limitation. These are observed documentation defects, not claims that the numeric engine currently returns paid reserve as IBNR.

The `uncertainty.selected_ultimate` field at calculator lines229-234 denotes the method-indicated aggregate, not a human selection. This naming is potentially confusing but did not alter the bounded calculation; the final practitioner response explains it.

## Limits of conclusions

All four requested core behaviors worked on the documented supported inputs; this does not prove all practitioner inputs work. The three defects above arise from small synthetic followups and are supported by actual outputs plus native pass results, not only code inspection. No external systems, live policies, bookings, notifications or human approvals were performed. The snapshot is independent of later edits; rerun the cases against any revised packages before claiming remediation.
