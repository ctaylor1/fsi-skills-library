# Payments Phase 1 limited forward evaluation

Scope: five realistic requests interpreted by an independent model, using freshly authored synthetic inputs and the actual router/native validators/calculators. No network, production systems or repository writes. This evaluates the observed supplied-evidence behavior, not production acceptance or compliance certification.

Reproduce the five main cases from repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B /tmp/payments-forward-cases/run_cases.py
```

`execution-log.json` retains every exact command, exit code, stdout and stderr. Five route generations and validations and five input/calculation/output sequences all exited 0. Issuer and phone-scam input validators emitted the expected missing-evidence warnings.

## Practical outcomes

| Request | Selected workflow and observed result | Response supported by the evidence |
|---|---|---|
| Approval fell 89% to 82%, rejected logs only | Router returned `capability-gap`, planned `payment-acceptance-performance-analyzer`; separate supporting API-log packet counted 3 supplied failures (2 issuer declines, 1 network) and `success_denominator_verified=false`, `suspected_cause=null`. | The reported change is 7 percentage points, but rejected-only records cannot independently validate either rate or determine the cause. Request complete attempt outcomes for both periods, stable definitions and deduplication/retry identity, segment data and relevant changes. Do not present the log distribution as the missing performance analysis. |
| Issuer unauthorized debit-card claim, scheme deadline present, legal profile/calendar absent | `issuer-payment-dispute-reviewer`: `legal-profile-unresolved`; missing named calendar/cutoff is explicitly retained; no draft or outcome. In initial synthetic case an independently supplied scheme profile retained its recovery deadline, separately. In the more minimal variant without optional scheme profile, the supplied scheme clock disappeared (finding below). | Keep issuer ownership; urgently obtain applicable reviewed legal profile and calendar/clock evidence. The scheme recovery deadline does not determine consumer redress deadlines. No denial, credit, filing or closure is warranted. Preserve the supplied recovery date as unresolved operational evidence. |
| Phone scam; customer authorized instant transfer, no email artifacts | `payment-fraud-and-scam-investigator`: score 0 / Low is explicitly illustrative, yet `needs-evidence`; payment investigator remains owner; `consultations=[]`; no cyber-email referral or email requirement. Missing beneficiary/reimbursement evidence and human scam review remain visible. | Preserve authorization and deception as distinct facts; obtain victim, beneficiary, recovery and reimbursement evidence. Do not infer legitimacy from technical score or require nonexistent emails. |
| USD 10.00 settled sale; 0.10 interchange + 0.20 assessments + 0 processor; fixed fees unknown | `merchant-payment-cost-analyzer`: exact Decimal strings `10.00`, `0.10`, `0.20`, `0.00`; `monthly_fixed=null`, `total_fees=null`, `effective_rate_bps=null`; missing data level remains unknown; no savings output. | Observed transaction charges total USD 0.30 (3% of this sale), with zero supplied processor markup. All-in cost/rate remain unknown pending fixed-fee evidence. This does not verify contract rates or qualification. |
| Go-live checklist has links only; reconciliation N/A because manual | `payment-integration-readiness-reviewer`: 0 of 9 satisfied, score 0.0, 9 gaps, `gaps-for-review`. All eight links remain `supplied pointer; not inspected`; reconciliation says manual alternatives are not exemptions. | Obtain inspection records and result evidence per required item and document/review the manual reconciliation control. No go-live approval follows from this packet or any score. |

## Initial reproducible findings — repaired and independently verified

1. **API diagnostic loses documented time fields while validation passes.** The documented contract (`payment-api-log-diagnostic-pack/scripts/validate_input.py:4-5`, also SKILL.md input section) uses `integration.window` and `log_entries[].ts`. The calculator reads `doc.get("window")` at line 66 and `e.get("timestamp")` at line 46. Input `1-rejected-logs-input.json` contains a complete August window and three offset-aware `ts` values; output `1-rejected-logs-output.json` has null window and every classified timestamp null. All native validators pass. This silently discards chronology and period provenance needed even for bounded log review. Correct the field mapping or explicitly normalize supported aliases and validate retention.

2. **Issuer discards supplied scheme recovery clock if its optional profile is absent.** In `2b-issuer-deadline-only-input.json`, scheme recovery due date 2026-10-15 remains supplied, but the scheme profile is absent. Output `2b-issuer-deadline-only-output.json` reduces `scheme_review` to `{"status":"not-assessed"}` and does not preserve that clock or request its missing profile. Input and output validation pass; statutory treatment remains appropriately unresolved. The `if scheme is not None` block in `issuer-payment-dispute-reviewer/scripts/calculate_or_transform.py:91-95` only processes clocks when a profile exists. Retain the supplied clocks with unresolved applicability/profile evidence instead. Exact variant commands and outputs are retained in `2b-execution-log.json`.

No unsafe completion claim was observed in these five task responses. The two findings concern evidence loss that the current output validators do not detect. The API SKILL.md also contained an old readiness target name and causal workflow wording, already reported to the parent agent for integration; those documentation corrections are separate from this read-only evaluation.

## Independent verification after parent fixes

Re-ran the **exact unchanged** `1-rejected-logs-input.json` and `2b-issuer-deadline-only-input.json` against the updated repository. All six native CLI invocations (input validator, calculator, output validator for each case) exited 0. Issuer intake retained its expected missing-legal-profile warning. `fix-verification-execution-log.json` preserves exact commands, stdout, stderr and exit codes; the original failing outputs remain unchanged for comparison.

- `1-rejected-logs-verified-output.json` now retains the supplied August `integration.window` and all three input `ts` values in output `timestamp`. Independent equality assertions passed. `success_denominator_verified=false` and `suspected_cause=null` remain intact.
- `2b-issuer-deadline-only-verified-output.json` now retains the supplied scheme clock, recovery due date and scheme source citation. Scheme review is `unresolved` with missing-profile issues. Independent assertions verified these fields and confirmed the overall statutory disposition remains `legal-profile-unresolved` with no draft response.
- Readback of API SKILL.md and handoff documentation confirms its readiness route now names `payment-integration-readiness-reviewer`. A residual documentation phrase remains at SKILL.md:74-75 (`pick top endpoint and suspected` / `cause`), despite the correct noncausal behavior; reported to parent for correction.

**Current result for this bounded forward evaluation: both observed evidence-loss defects are resolved in the tested cases; one residual causal documentation phrase remains to correct.** This verification does not expand the original limited scope or establish general production/compliance acceptance.
