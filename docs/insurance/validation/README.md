# Insurance Phase 1 validation — 2026-09-18

The local implementation exit checks passed. This record covers bounded offline
software and agent behavior; it does not establish source authenticity, actuarial,
claims, medical or legal acceptance, or institutional deployment readiness.

## Final integrated checks

Exact command arrays, start times, return codes and log paths are in
[checks.json](checks.json). The environment used Python 3.14 with PyYAML 6.0.3 and
Ruff through `/tmp/fsi-p0-venv`; use an equivalent environment to rerun the commands.

| Check | Result | Evidence |
| --- | --- | --- |
| Whole-library executable package checks | 1,179 passed; 0 failed | [Package log](package-evaluations.log) |
| Insurance subset of those checks | 118 passed, covering all 23 packages | [Inventory](inventory.json) and insurance sections of package log |
| Repository integration/behavior tests | 319 methods passed, including 15 insurance methods | [Repository log](repository-tests.log) |
| Structure and metadata | 248 packages; 0 errors, 0 warnings | [Structure log](structure.log) |
| Catalog handoff destinations | 0 dangling references across 248 packages | [Handoff log](handoffs.log) |
| Insurance routes and migrations | 0 errors; all 24 original packages accounted for | [Route/migration log](insurance-routes-migrations.log) |
| Shared bundle consistency | 23 references and 23 helpers match canonical sources | [Bundle log](shared-contract.log) |
| Focused code checks | Ruff E9/F passed | [Lint log](insurance-lint.log) |
| Scoped whitespace | Passed | [Whitespace log](insurance-whitespace.log) |

Insurance executable commands include **154 unit-test methods**, recorded by file
in the inventory. Some commands run multiple methods, and some assert expected
rejection of an invalid output. These counts are not interchangeable or additive.
The 15 repository insurance methods comprise seven contract and eight integration
checks, including native receiver invocation, a real intake-to-triage handoff,
identity mapping, issue preservation, installed-package portability and catalog
regeneration/idempotence. The repository total includes concurrent non-insurance
work and is not attributable solely to this phase.

The installed skill-creator quick validator was attempted and rejects the existing
`compatibility` frontmatter field in the inspected packages. It is not counted as
a pass. The repository validator supports that field and passed. Broader strict
lint is not the phase gate; the claims repair report records unchanged pre-existing
strict-style diagnostics separately from the passing E9/F scope.

## Independent initial forward evaluations and repairs

Separate agents first read native skills/interfaces and designed or interpreted
synthetic requests without consulting existing expected fixtures. They retained
requests, adaptations, actual outputs, authored practitioner responses and command
results. The router script consumes an explicit intent selected by the agent; it
is not a natural-language classifier. These were bounded agent exercises, not a
blind professional review or a paired multi-model benchmark.

| Stream | Cases and result | Reports |
| --- | --- | --- |
| Routing | Four practitioner requests: pricing adequacy, homeowners dispute, treaty comparison and portfolio fraud. Correct ownership/gaps; final installed-inventory replay validates the live treaty target. | [Initial evaluation](forward/router/forward-evaluation.md); [final inventory replay](forward/claims/forward-evaluation.md) |
| Product/actuarial/reinsurance | Four principal requests plus three adverse followups. Paid reserve basis, mixed currency, historical earned premium and ordinary treaty arithmetic worked. Missing quote dimensions, absent large-loss data, zero-premium restoration and template terminology were repaired. | [Initial findings](forward/product/findings.md); [repairs and replay](forward/product/repairs/repair-results.md) |
| CAT and data | Eight fresh inputs; 32 total native stages per run, before and after. Repaired absent-exposure zero metrics, unknown-alert summary overstatement, missing duplicate provenance and hidden independent basis conflicts. | [Initial review](forward/cat-data/practitioner-review.md); [repairs and replay](forward/cat-data/after/fix-verification.md) |
| Claims | Four fresh requests plus explicit-null and generated-assertion variants. Preserved urgent routing, contrary evidence and receipt. Repaired explicit-null monetary rejection and unsupported fraud/fault wording. Five unchanged native inputs pass four stages each after repair. | [Evaluation and repairs](forward/claims/forward-evaluation.md) |

Initial native validators accepted several defective outputs. Their agreement
therefore did not prove correctness. Fresh-case review and independent arithmetic
exposed those defects; regression cases and unchanged-input replay checked the
repairs. In three streams, the initial evaluator subsequently authored the repairs.
Those later replays are author verification, not a second independent review.
The parent subsequently ran the full integrated checks above.

The original initial outputs remain intact, alongside repaired results. Source
hashes identify the evaluated implementations. Historical command logs retain
their original temporary paths; copied package snapshots and Python caches are
excluded from this repository evidence set. The final native scripts,
retained inputs and package regression cases reproduce current behavior. Do not
rerun a historical `before` harness and overwrite its evidence with current outputs.
[Retained file hashes](retained-forward-files.json) identify the copied artifacts;
[final source hashes](source-manifest.json) identify the completed implementation.
Hashes detect content change, not source authenticity or reviewer independence.

## Remaining acceptance boundaries

The six natural-language router cases declared in its evaluation manifest remain
unexecuted as that specific benchmark; four separate forward cases overlap their
themes but do not fulfill the whole manifest. No broader model pass rate is claimed.
Native source-to-input mapping remains practitioner/agent-authored and requires
review. No production policies, personal records, live source connectors, external
communications or financial actions were used.

CAT monitoring conservatively retains a modeled-loss alert as unknown when no
supported model observation exists, even when a complete exposure snapshot permits
a measured zero zone-exposure clear. Reconciliation does not choose the authoritative
duplicate or translate financial bases. Other method limits and Phase 2 work are
listed in [the implementation record](../PHASE1-IMPLEMENTATION.md).
