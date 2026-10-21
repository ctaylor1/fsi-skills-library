# Insurance Phase 6 — offline acceptance evidence preparation

The existing roadmap ended at Phase 5. Following the user's request to implement
the next phase, this follow-on was scoped to acceptance/readiness tooling, the
recommended continuation while the user was offered alternative health-payer and
regional expansion directions. It implements the repository's existing release
criteria as a local evidence preparation workflow. It adds no new skill packages.
Insurance remains at 69 packages, with four shared Phase 4 dependencies included in
portable verification and the review inventory.

## Deliverables and purpose

- `tools/insurance_readiness_lib.py` snapshots complete package content, selected
  catalog rows, evaluation contracts, relevant policy and readiness tooling. It
  assesses supplied records against nine fixed release gates without authenticating
  approvals or allowing input records to remove required gates.
- `tools/run_insurance_portable.py` runs the existing declared checks in isolated
  package copies, preserves expected failures and planned/unexecuted cases, records
  bounded command output and timing, and detects source or installed-copy mutation.
  Commands use explicit Python argument lists, with no shell and no hidden retry.
- `tools/check_insurance_readiness.py` creates a new dossier with exact file hashes,
  scope, supplied review records, observed gaps and software-report consistency.
  Output files are read back and existing evidence is not overwritten.
- [The review guide](acceptance/README.md), fixed requirements, exact record schema
  and empty templates support institution-specific review. Missing, expired,
  conflicting, mismatched and synthetic evidence remain explicit.
- New regression tests exercise actual command failure/mutation/timeout and record
  identity, source paths, dates, scope, conflicting reviews and unsupported authority.
  New validation evidence is saved separately from earlier phase archives.

## Scope and boundaries

The work prepares a concrete review package for the existing domain, method, data,
privacy/access, model-evaluation and operational owners. It does not appoint those
owners, supply their decisions, execute adjacent professional skills with invented
inputs, authenticate evidence, connect production systems or authorize deployment.
A package presence count is not readiness; a successful fixture is not source truth;
a complete supplied approval record is not an authenticated professional signoff.

The actual institution, source profiles, reviewer receipts and external workbook
were not supplied. The generated current dossier therefore retains missing scope
and review records. Software validation can be complete while institutional
acceptance remains unestablished. Future reviews must bind the actual institution,
environment, market, program, product, jurisdiction, method and package digest.

No changes to existing skill instructions, native calculations, catalog counts,
shared runtime contracts or historical validation archives are needed for this
phase. No regional rules, real-world clinical/coding data, live connectors,
external messages, payments, release or deployment are introduced.

See [Phase 6 verification](phase6-validation/README.md) for actual results,
independent tool-use review and preservation evidence. Human/institutional acceptance,
source-workbook reconciliation, broader health-payer coverage and additional regional
methods remain distinct follow-up work.
