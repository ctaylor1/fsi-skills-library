# Independent forward evaluation — product, rate and claims group

Six fresh practitioner requests were designed from the actual SKILL, native method, source-map, control, handoff and output documents plus native interfaces. No `tests`, `evals`, fixture/golden examples or prior audit findings were inspected. The generated synthetic packets were locked in `design-lock.json` before native execution. No package source was edited by this evaluator and no external action was taken.

The review found **one concrete defect class**, with **two accepted-but-wrong closure results** (the baseline and a blank-trigger variant). The parent agent repaired it, and independent replay of all three unchanged closure inputs confirms the identified cases now behave appropriately. All six baseline scenarios passed input, calculate and output checks. Independent rate and claim-finance arithmetic matched the outputs. Passing native checks is software self-consistency evidence, not independent validation of the readiness meaning, evidence truth, model performance or professional acceptance.

## Baseline results

| Skill | Fresh practitioner task | Native result | Independent assessment |
|---|---|---|---|
| insurance-product-design-reviewer | Water add-on promise exceeds wording; training and filing evidence absent | needs-data; failed simulation and required review gaps preserved | Appropriate. Human response explains the actual pipe-repair contradiction, not merely the encoded failed status. |
| pc-rate-adequacy-analyzer | Aligned 2025 property cohort with reviewed prospective assumptions | ready-for-review; indication ratio 0.080330 | Appropriate. Five native outputs agree with independent decimal arithmetic; exact implied percentage about 8.0330245163%. |
| claim-coverage-reviewer | Recent discovery versus plumber's possible long-duration leak evidence | needs-data; both competing hypotheses preserved | Appropriate. Reported date is within the supplied period; onset remains unproven. No coverage decision. |
| claim-handling-plan-builder | Completed acknowledgement, overdue evidence and blocked update, unassigned recovery task | needs-data; two overdue tasks and missing recovery owner/date visible | Appropriate within supplied-plan scope. Human response questions whether the status-update dependency should delay service. |
| claim-financial-evaluation-assistant | Repair and contested-damage scenarios with unknown contested recovery | needs-data; REPAIR evaluable, CONTESTED not evaluable | All current-position and REPAIR arithmetic correct. No unknown recovery converted to zero. Native helper suppresses known gross figures as well as unknown net in the incomplete scenario; human response supplies independently labeled known gross comparisons. |
| claim-payment-closure-reviewer | Already-settled final payment; closure otherwise reconciled but reopening unassigned | needs-data overall; repeat payment blocked; closure substatus ready | **Accepted-but-wrong closure substatus.** Missing reopening ownership/routing should block closure under the documented method. |

Every skill directory contains request.md, raw_sources/, mapping.md, input.json, output.json, validate_input.json, validate_output.json, execution-log.json, practitioner-response.md, an original implementation snapshot, and source hashes. `independent-checks.json` records numerical expectations and comparisons. Native command stdout is preserved, not rephrased.

## Confirmed defect: closure readiness ignores reopening content/ownership

The original `claim-payment-closure-reviewer` domain only checks that `reopen_triggers` is a nonempty list and later uses `bool(triggers)` as a closure condition. The method document explicitly requires reopening triggers with ownership. A nonempty row with owner/routing null — or even a list containing a blank string — passes that check.

Original evidence anchors in the saved snapshot:

- `snapshot/scripts/domain.py`, lines 146–148: only list/nonempty check for reopening evidence.
- `snapshot/scripts/domain.py`, lines 176–189: closure readiness tests `bool(triggers)` then emits ready status.
- `snapshot/references/domain-rules.md`, line 7: ownership requirement.

Baseline input retains the raw CLOSURE statement that the reopening owner/routing is unassigned, maps it to null native fields, and includes the open issue explicitly. Input validation exits 0; calculation exits 0 with `closure_review_status=ready_for_authorized_review`; output validation exits 0. Top-level `needs-data` is a mitigating visible warning, but does not make the contradictory native closure flag correct. A consumer or reviewer reading the domain-specific status would receive the wrong readiness signal.

Exact baseline repro (from repository root):

```sh
/tmp/fsi-p0-venv/bin/python /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance/claim-payment-closure-reviewer/scripts/validate_input.py /tmp/insurance-p2-forward-claims/claim-payment-closure-reviewer/input.json
/tmp/fsi-p0-venv/bin/python /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance/claim-payment-closure-reviewer/scripts/calculate_or_transform.py /tmp/insurance-p2-forward-claims/claim-payment-closure-reviewer/input.json
/tmp/fsi-p0-venv/bin/python /Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance/claim-payment-closure-reviewer/scripts/validate_output.py /tmp/insurance-p2-forward-claims/claim-payment-closure-reviewer/output.json
```

The snapshot scripts preserve exact original behavior if the repository is repaired. Two bounded variants run against that snapshot: `complete_reopening` provides a source-backed trigger, owner and route and correctly permits closure review; `blank_reopening` preserves a blank migrated reopening entry and wrongly permits closure review. Both variants pass all three checks; see their unmodified native outputs and logs. This is one defect class, not two unrelated failures.

## Limits and source identity

The source packets are invented practitioner records and reviewed case conventions. Their identifiers, quotations, balances and profiles are explicitly synthetic. No actual customer evidence, legal determination, jurisdiction research, actuarial assumption selection, payment or external delivery took place. Primary references linked in the source maps were treated as descriptions of method scope; no claim is made that their substantive current content or applicability was independently recertified here.

The parent agent intentionally added common-evidence-contract links to the six SKILL.md files after the design snapshot. The run hashes show only those documentation files changed; native executable files were unchanged during the original baseline runs. The original snapshots remain preserved. That documentation-only drift is distinguished from the later defect repair and any separate replay evidence.

Six cases plus two bounded variants yielded 24 successful CLI checks before repair. That count is a bounded execution record. It is not a production-readiness score, model benchmark, systematic adversarial coverage estimate or professional acceptance claim.

## Repair and independent unchanged-input replay

The parent agent updated the native reopening check to require each trigger row to contain a nonblank trigger, owner and routing plus registered source references. This evaluator then replayed the original baseline input and both characterization variants without changing a byte. Before/after SHA-256 values match for every replayed input. Original wrong outputs and original code remain intact.

| Unchanged input | Original closure result | Repaired result | Independent expectation |
|---|---|---|---|
| Baseline owner/routing null | ready_for_authorized_review | blocked, with owner and routing gaps | blocked |
| Complete source-backed trigger/owner/routing | ready_for_authorized_review | ready_for_authorized_review | ready_for_authorized_review |
| Blank migrated trigger entry | ready_for_authorized_review | blocked, with structured reopening-evidence gap | blocked |

The nine replay CLI checks all exit 0; usable incomplete inputs continue to produce partial review outputs rather than being silently filled. Payment remains blocked in all three because the final payment is already settled. No action is executed. The identified defect is resolved for these independently authored cases; this is not a claim that every possible input or workflow has been reviewed.

Replay commands, exact outputs, findings, input hashes and repaired implementation hashes are saved in `claim-payment-closure-reviewer/after-repair/`. `practitioner-response-after-repair.md` gives the current practitioner-facing result; the original response remains as part of the pre-repair evidence trail. Total observed CLI executions are 33: 24 before repair and 9 replay checks after repair.
