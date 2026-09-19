# Independent Payments Phase 2 governance forward evaluation

Run date: 2026-09-18. Scope: regulatory applicability, hub architecture and case-scoped issuer legal-profile preparation. These were fresh synthetic requests interpreted by an independent model from SKILL.md, schema, source/domain documentation and native helper code. No fixture, golden, regression test, production system or network source was read or used. Repository content was not edited.

**Result:** the requested cases behaved as expected. Twenty-three native CLI invocations exited 0. Seventeen independent behavioral assertions passed. No actionable defect was identified in this bounded run. Zero-exit analytical outputs include deliberately unresolved and unsupported cases; they do not mean legal or architecture acceptance.

## Evidence and reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B /tmp/payments-phase2-forward-governance/run_forward.py
PYTHONDONTWRITEBYTECODE=1 /tmp/fsi-p0-venv/bin/python -B /tmp/payments-phase2-forward-governance/check_results.py
```

- `execution-log.json`: all 23 exact native commands, exit codes, stdout and stderr.
- Named `*-input.json` / `*-output.json`: complete fresh requests and actual outputs.
- `independent-assertions.json`: 17 checks of requested boundaries and evidence retention.
- `source-sha256-before.json` / `source-sha256-after.json`: SHA-256 for 54 package source/document files used or available to the three packages, excluding evals and test files. `source-drift.json` confirms no change across execution and checks.
- `artifact-sha256.json`: input/output and report artifact hashes.

The source inventory and specialist references are explicitly synthetic supplied records. The native tools do not authenticate them. Public legal summaries were inspected locally as test context; no current legal conclusion was independently researched or issued.

## 1. UK EMI proposition, EA variant and unsupported jurisdiction

**Practical response:** the proposed statement that every consumer balance is deposit insured merely because funds are held at a partner bank is unsupported. The recorded customer claim is against the EMI under wallet terms, while the partner bank provides the account to the EMI. That chain requires an assessment of ownership, account structure, insolvency treatment and any applicable protection; bank custody alone is insufficient evidence for the consumer-facing promise. Keep safeguarding and deposit protection analysis separate.

The UK matrix requests four scoped specialist reviews: permissions, safeguarding, consumer protections and authentication. Before the proposition or disclosure can be relied on, obtain the exact entity and permissions/register evidence, the service classification, executed account/partner terms, relevant-funds classification, safeguarding arrangements and reconciliation, insolvency/beneficial-ownership analysis, and reviewed consumer disclosures and error/consent processes. The packet supplies candidate obligations, not an insurance determination or authorization.

| Fresh input | Actual outcome | Boundary observed |
|---|---|---|
| `1a-uk-emi-input.json`: UK EMI, consumers, e-money and credit transfers, customer claim against EMI, partner bank holds funds, deposit-insurance marketing claim | `needs-evidence`; four legal-review findings; `deposit-insured` is an excluded conclusion; safeguarding/permissions scope retained | No inference from bank partnership to permissions, compliance or deposit insurance |
| `1b-ea-no-national-input.json`: French entity and customers under EA profile, no national-transposition evidence | `needs-evidence`; explicit `national-transposition-required` plus candidate obligation reviews | EU framework does not fill absent French/national applicability review; instant-transfer obligations remain conditional |
| `1c-unsupported-input.json`: Canadian jurisdiction | `unsupported`; empty regional result and `unsupported-jurisdiction` finding | No borrowed UK/EA/US operational conclusion |

The UK claim is present in the retained activity evidence; the helper's explicit limitations say safeguarding is not deposit insurance. The practitioner response above applies that boundary to this specific proposition rather than merely repeating the matrix.

## 2. Bank payment-hub modernization

**Practical recommendation:** advance the supplied strangler option as a draft candidate for engineering review, conditional on proving durable idempotency, authoritative outcome resolution and single-writer ownership. The alternative of hardening the legacy executor stays viable if transition complexity cannot be controlled. The evidence does not justify a vendor selection or production cutover.

The current timeout retry needs a different operating rule: preserve the original instruction identity across attempts, atomically bind its idempotency key to its payload, reject changed payloads, and resolve an unknown response through authoritative network status and reconciliation before another money-changing submission. An API timeout is an attempt observation; the operational ledger is authoritative for its own posting, and the rail/network feed is authoritative for the declared rail outcome. Those are distinct facts.

The fresh design retained four models: instruction, attempt, network payment and ledger entry. Four explicit flows connected API, hub, network and journal; money-changing edges included idempotency, uncertain-outcome and reconciliation designs. Operating controls include:

- Reconcile network, instruction and journal records by legal entity, account, currency and linked instruction/network IDs; route exceptions to the named Payments Operations queue.
- Post balanced entries per entity/currency and correct through linked entries rather than rewriting posted records.
- Measure the declared 99.95% availability target and 15-minute uncertain-age escalation. Neither number is a demonstrated result.
- Test timeout ambiguity, duplicate delivery, changed payload, delayed/out-of-order status, crash/restart and writer fencing before accepting the design.

The migration has read-only shadow comparison followed by a 5% canary of disjoint newly accepted instructions. Legacy owns its existing in-flight instructions; an ownership registry assigns one executor to each new instruction. Expansion requires inspected test/NFR evidence and no unexplained financial reconciliation gaps. Rollback stops new intake to the canary while preserving its existing ownership until resolved; reverting software does not reverse settled funds.

| Fresh input | Actual outcome | Boundary observed |
|---|---|---|
| `2a-hub-design-input.json`: coherent supplied design, two alternatives, two migration phases | `draft`, no structural/control findings; four flow assessments `supplied-design`; options remain `selected=false`; NFRs are `declared-target-not-demonstrated`; deployment validation false | Complete declarations are review material, not deployed guarantees or automatic selection |
| `2b-hub-uncertain-input.json`: submission uses `retry-with-new-key`, reconciliation removed | `needs-evidence`, eight `flow-control-gap` findings, submission flow `unresolved` | Blind/new-key retry rejected and reconciliation components, partitions, keys, owner, queue and evidence remain explicit gaps |

Do not accept the unsafe variant for cutover. Resolve its uncertain-outcome design and financial reconciliation first, then obtain independent integration/readiness evidence. These operating recommendations are engineering judgments on the supplied synthetic design, not claims the calculator has tested a live platform.

## 3. Reg E consumer debit profile and attempted cross-case reuse

**Practical response:** the preparation helper can produce a supplied, case-specific profile for issuer review of `case001`. A fresh specialist must assess `case002`; changing the case name or reusing a profile does not transfer the original scope review.

The synthetic specialist selected `error-notice` and `initial-investigation` for the current stage. The fixture supplies separate trigger records, due dates and a named issuer calendar/cutoff reference. It does not invent investigation-completion or error-determination events. Supplied due dates are test data, not dates computed or legally validated by this evaluation.

| Input/output pair | Actual outcome |
|---|---|
| `3a-profile-prepare-*`: source-backed `US-REG-E-CONSUMER-EFT`, `case001`, issuer, US, debit-card/card, valid review interval and hash | `supplied-profile-for-native-review`; prepared profile `active` for supplied review; case_scope retained; `authority_granted=false`, `deadlines_calculated=false` |
| `3b-profile-stale-review-*`: preparation scope changed to `case002`, original review hash retained | `needs-review`, draft profile; explicit requirement to bind exact case/product/rail/jurisdiction scope |
| `3c-issuer-case001-*`: prepared profile plus independently supplied clocks and required evidence/action-review references | `draft-ready-for-review`; submission authorization remains false; no claim decision, credit, filing or closure |
| `3d-issuer-profile-reuse-*`: same prepared case001 profile placed on case002 | `legal-profile-unresolved`; `prepared statutory profile is bound to a different case scope`; no draft response |

The specialist owner/reference and hash are declarations and linkage checks. The result does not authenticate a qualified reviewer, establish legal applicability, or authorize notices or credits.

## Defect report and evaluation limits

**Actionable defects found: none in these requested cases.** Every output was read in addition to running native validators, and the behavior checks use independent expectations: no insurance inference, national/unsupported scope retained, unsafe retry/reconciliation unresolved, no autonomous architecture selection/deployment, and case-bound profile reuse rejected.

This is a limited model forward test plus deterministic artifact validation. It is not broad malformed-input testing, a complete legal review, calibration of model behavior, implementation testing, or professional/deployment acceptance. A future audit could examine further scope transformations and failure cases, but this run does not claim that coverage.
