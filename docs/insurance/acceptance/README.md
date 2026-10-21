# Insurance acceptance evidence preparation

Use these tools to assemble a version-bound local review dossier for the existing
Insurance portfolio. They inventory evidence and execute package software checks;
they do not grant professional approval, source access, release or deployment authority.
The nine gates come from [repository build standards](../../BUILD-STANDARDS.md#release-gates-acceptance-criteria),
with roles and evidence described in [requirements.json](requirements.json).

## Prepare a current software checkpoint

Run from the repository root with the repository's normal Python environment:

```sh
python3 tools/run_insurance_portable.py --output /tmp/insurance-portable-review.json
python3 tools/check_insurance_readiness.py --as-of 2026-10-04 \
  --portable-report /tmp/insurance-portable-review.json \
  --output-directory /tmp/insurance-review-dossier
```

Choose new output names for each run. Existing files/directories are refused rather
than overwritten. The runner's output parent must exist. Use the actual assessment
date for a new run. The native programs and these tools use Python's standard library;
other repository-wide checks may need PyYAML and Ruff.

The snapshot includes all current Insurance packages and the four shared owners
introduced in Phase 4, their catalog rows, exact file inventories, evaluation
contracts, governance references and readiness tooling. Only this selected catalog
scope is bound, so unrelated new catalog rows do not invalidate an Insurance review.
Adding/removing/changing a selected package or relevant policy/tool file does.

The runner copies each package into a separate temporary directory and runs its
declared commands through the current Python interpreter, without a shell or
repository siblings. It strips PYTHONPATH/PYTHONHOME, disables bytecode writes,
checks source/install hashes before and after each command, and limits each command
to 60 seconds by default. Use `--workers 1` through `--workers 8` if needed.
These are trusted local repository programs; a temporary directory is not a security
sandbox and does not establish live connector isolation or institutional permissions.

A declared negative fixture passes only when its actual exit matches the expected
nonzero exit. Missing commands, malformed manifests, unsupported launch syntax,
timeouts, missing expected output, changed files and source drift prevent a passing
software report. Natural-language and planned evaluations remain explicitly unexecuted.
They are never counted as successful agent, practitioner or deployment evaluations.

## Supply real review records

Start with [scope-template.json](scope-template.json) and
[review-records-template.json](review-records-template.json). They intentionally
contain unknown scope and no review records. Do not invent an institution, source
owner or approval merely to fill them. The exact record contract is
[receipt-schema.json](receipt-schema.json); the native checker also enforces package
identity, file containment, semantic dates, scope equality and conflicting records.

One dossier has one exact institution/environment/market/program/product/jurisdiction/
method scope. For a method-specific review, select the appropriate package and use
its actual scope. Keep other packages/scopes in separate dossiers:

```sh
python3 tools/check_insurance_readiness.py --as-of 2026-10-04 \
  --package health-plan-pricing-reviewer \
  --scope /path/to/review/scope.json \
  --records /path/to/review/records.json \
  --portable-report /tmp/insurance-portable-review.json \
  --output-directory /tmp/health-pricing-review-dossier
```

For each record supply all of the following:

- A unique record ID, exact package name and one fixed gate ID.
- The package `content_sha256` from the current dossier's `snapshot.json`.
- All seven scope fields, identical to the selected assessment scope.
- Reviewer name, role and source-backed authority basis; these remain unverified assertions.
- Review date, effective-from date and expiry date. Reviews must be recorded by the
  assessment day and effective on it; future and expired records remain unresolved.
- `accepted`, `rejected`, `needs-work` or `not-applicable`, with a concrete rationale.
  A not-applicable assertion still requires reviewer and supporting evidence.
- Evidence kind (`institutional`, `synthetic` or `unknown`), and at least one local
  evidence file's relative path, SHA-256 and precise source locator.
- An explicit unresolved-issues array. Open issues prevent an unqualified evidence record.

Evidence paths resolve beneath the records file's directory. Absolute paths, parent
traversal, symlinks, missing/nonregular files and changed content are rejected or
reported unresolved. Evidence bodies are hashed locally and are not copied into the
dossier. The supplied record packet, source locators, scope and reviewer assertions
are retained, so apply the institution's access/retention rules to the output.
No evidence file is executed, sent externally or fetched over a network.

Multiple records for one package/gate require owner reconciliation; the checker does
not discard an old negative review just because a newer record says accepted. Preserve
prior dossiers and original receipts when a reviewer prepares a reconciled packet.

## Interpret the dossier

`readiness.json` retains the assessment, supplied records, software evidence and
snapshot bindings. `snapshot.json` identifies every reviewed package byte and
command contract. `report.md` is the human-readable evidence inventory.

| Gate state | Meaning |
| --- | --- |
| `not-supplied` | No review record is provided for this fixed gate. |
| `invalid-or-unresolved` | Scope, dates, package/evidence identity, required fields, open issues, synthetic/unknown evidence kind or duplicate records need resolution. |
| `recorded-negative` | A current, internally consistent supplied record says rejected or needs-work. |
| `supplied-unverified` | A structurally complete, current, scope-matched accepted/not-applicable assertion labeled institutional was supplied. Reviewer identity, authority and source truth have not been authenticated. |

Even nine `supplied-unverified` records do not establish acceptance. The tool always
retains `institution_acceptance: not-established` and `deployment_authorized: false`.
A matching software report is also supplied evidence, not an authenticated attestation;
the checker rejects missing command coverage and internally inconsistent success claims.
Dossier exit zero means the report was saved and read back, not that its review gates
passed. Inspect the actual states and unresolved issues.

The domain SME, control/privacy/access owners, applicable legal/model specialists and
operations/product owners retain their existing responsibilities. Reuse their native
workflows and real source contracts. There is no new professional approval skill.
External source-workbook reconciliation remains separate: regenerating the catalog
from its current rows does not read or reconcile the external workbook. This phase
adds neither regional rule defaults nor comprehensive health-payer functionality.
