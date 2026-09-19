# Payments Phase 2 commercial forward evaluation

Run date: 2026-09-18. Evaluator: independent agent working from three realistic requests, fresh synthetic evidence and the installed skill instructions/input contracts. No package regression tests, evaluation fixtures or golden outputs were inspected. No repository files were edited, no external system was contacted and no real provider or merchant was evaluated.

**Result: the three requests and five variants behaved reasonably within the declared offline scope. No package defect was found in this bounded evaluation.** The final run made 21 native CLI calls: six accepted input/calculate/output workflows (18 calls), two expected rejected input/calculation calls for overlapping economics coverage, and one expected output-validation rejection after tampering. Every accepted output had false authority and action flags. Exact commands, exit codes and stdout/stderr files are retained in `command-results.json`.

A first harness run made nine successful native CLI calls before its own assertion code referenced the wrong output key (`comparisons` instead of documented/generated `provider_comparisons`). That harness-only mistake was corrected. Its command history is preserved separately in `initial-harness-attempt-commands.json`; these repeated calls are not counted as additional scenarios or independent coverage.

## 1. UK recurring merchant acceptance

Request: a UK online merchant wants an acceptance plan for cards and pay-by-bank across desktop and mobile recurring customers. The gateway deck claims universal method/country support; specific contract and inspection coverage is incomplete.

Practical response supported by `s1-acceptance-output.json`:

- Retain the desktop recurring card path as the only scope with supplied inspected entity, currency, recurring and operational evidence. It is ready for human option review, not approved for launch.
- The three other segment/method combinations remain gated. The generic sales deck cannot establish recurring pay-by-bank, mobile support or entity eligibility. The separate bank-payment annex only covers one-off desktop customer authorization and conflicts with the deck's recurring claim.
- Resolve the recurring contract/consent position, mobile inspection, settlement and servicing responsibilities before selecting an option. Next work is provider diligence, economics, integration/refund/dispute inspection and a bounded pilot measured against unique eligible checkout attempts.
- No selected option, conversion uplift or estimated reach was invented. The upstream deck/contract conflict is carried intact into the output.

In `s1b-acceptance-conflict-input.json`, pay-by-bank was explicitly classified unsupported using the inspected one-off-only contract annex. Both pay-by-bank rows remained blocked and their reasons included unsupported recurring support. The option was not promoted because other coverage was favorable.

## 2. Issuer processor diligence

Request: an issuer must compare processor A's attractive optional analytics with B's supported dispute workflow and data export, where fee units differ.

The synthetic requirement owner supplied weights of 20 for mandatory disputes, 20 for mandatory export, and 60 for optional analytics. This deliberately tests the danger of a high optional-feature score overriding essential operating evidence.

| Provider | Evidence | Score | Evidence shortlist | Quoted processing rate |
|---|---|---:|---|---|
| A | Analytics inspected; disputes/export absent | 60–100 interval; point score unknown | Excluded by two mandatory gaps | GBP0.04 per attempt |
| B | Disputes/export inspected; optional advanced analytics unsupported | 40 | Eligible for human diligence | GBP0.08 per success |

Practical response supported by `s2-provider-output.json`: advance B for continued human diligence on the supplied mandatory evidence; request A's dispute lifecycle/case-handoff evidence and complete migration/export tests before A can enter the evidence shortlist. Neither provider is selected or automatically ranked. B's larger nominal rate is in a different fee unit, so a direct total-cost conclusion would be unsound; normalize volumes, success rates, ancillary inclusions and contract terms through an economics model first.

In `s2b-provider-stale-input.json`, B's inspection source became overdue on September 17, one day before the request. B no longer qualified for the evidence shortlist; its mandatory requirements became unknown. Expired evidence was not treated as current support.

## 3. Merchant pay-by-bank economics

Request: model 10,000 unique monthly order attempts at GBP40, baseline card completion 95%, pay-by-bank adoption 30% and completion 90%, with explicit processing, refund, fraud and operating costs.

All rates are synthetic supplied assumptions. Card processing costs are 1.8% of successful value plus GBP0.20 per attempt and GBP100 monthly fixed; pay-by-bank costs 0.2% plus GBP0.05 per attempt and GBP500 monthly fixed. Both methods retain their fixed costs when enabled. Fraud costs are 0.2%/0.03% of successful value for cards/pay-by-bank, funding costs 0.02%/0.01%, operational support GBP0.08/0.12 per success, and refund handling GBP0.06 per success. The refund assumption is 3% frequency × GBP2 handling cost, with expected refund merchandise effects already reflected in the separately supplied 30% net merchandise margin. Domestic GBP FX cost is explicitly zero; card incentives are zero and pay-by-bank incentives GBP0.10 per success. No refund principal is charged again, no authorizations are substituted for completed paid orders, and no demand growth is assumed.

| Monthly metric | Card baseline | 30% pay-by-bank adoption |
|---|---:|---:|
| Unique attempts | 10,000 | 10,000 |
| Expected successful orders | 9,500 | 9,350 |
| Net merchandise margin before payment costs | GBP114,000.00 | GBP112,200.00 |
| Modeled payment/operating costs | GBP11,106.00 | GBP9,469.40 |
| Modeled contribution | GBP102,894.00 | GBP102,730.60 |
| Cost per successful order | GBP1.16905 | GBP1.01277 |

Practical response: at 30% adoption the modeled payment costs fall GBP1,636.60, but losing 150 expected completed orders reduces merchandise margin GBP1,800. The net result is **GBP163.40 less contribution per month**. Lower processing costs alone do not establish an economic improvement. These arithmetic results were independently calculated from the authored assumptions in `run_forward.py` without importing package calculations.

The bounded model crosses break-even at **44.5633% adoption**. Incremental contribution is `GBP1,122 × adoption fraction − GBP500` while these assumptions and retained contracts hold. Sensitivity is:

| Adoption | Expected successful orders | Incremental monthly contribution |
|---|---:|---:|
| 0% with new method contract enabled | 9,500 | −GBP500.00 |
| 10% | 9,450 | −GBP387.80 |
| 30% | 9,350 | −GBP163.40 |
| 50% | 9,250 | +GBP61.00 |
| 100% | 9,000 | +GBP622.00 |

This does not forecast adoption or justify launching with lower completion. A pilot should validate the supplied completion, adoption, refund, fraud and operating assumptions; a contract or nonlinear response change requires a different reviewed model.

Variants behaved correctly:

- Removing the pay-by-bank fraud rate produced `needs-evidence`, null scenario contribution, null incremental contribution and no calculable break-even (`s3b-economics-missing-output.json`). Missing losses were not silently zeroed.
- Assigning overlapping economic coverage to two processing terms caused both input validation and calculation to reject the request (`s3c-economics-overlap-*`). No double-counted model was produced.
- Replacing the calculated contribution change with `9999` caused output validation against the separately supplied original input to reject the tampered output (`s3d-economics-tamper-validation.json`).

## Evidence and limits

`run_forward.py` contains the fresh request authoring, exact CLI execution and independent assertions. `source-*.json` files are the synthetic supporting artifacts; their SHA-256 hashes are retained in `source-artifact-hashes.json`. `source-code-hashes-before.json` and `source-code-hashes-after.json` bind this evaluation to the package versions read; there was no source-code hash drift during the final run. `independent-assertions.json` retains the key checked results.

The raw source references are absolute paths to the original `/tmp/payments-phase2-forward-commercial` run directory. Those are historical provenance, not network links. To reproduce from the current checkout, run `PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B /tmp/payments-phase2-forward-commercial/run_forward.py`; it writes new artifacts to that same temporary directory. If archived elsewhere, copy the runner into the original temporary directory first or deliberately adapt its explicit `ROOT`, `OUT` and `PYTHON` constants and retain the changed runner separately.

This is evidence for three bounded commercial workflows and selected incomplete/conflicting inputs. It is not a broad model benchmark, independent verification of real provider attestations, jurisdictional legal analysis, SME acceptance, or production readiness. The packages correctly rely on structured classifications supplied by the practitioner; reading and authenticating actual contracts/inspection records remains outside their deterministic helper.

### Current-foundation replay

At parent-requested closeout, the current package hashes matched the evaluated versions. The full 21-call forward suite was nevertheless rerun; all assertions passed and all prior artifacts were byte-identical. `refresh-command-results.json` preserves the repeated commands and exits, and `refresh-verification.json` records the check. This is a repeat of the same bounded scenarios, not 21 new cases. The evaluated foundation therefore includes the current credential-key rejection and handoff normalization.
