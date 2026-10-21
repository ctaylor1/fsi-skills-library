---
name: tokenized-fund-operations-reviewer
description: "Reconcile a tokenized fund share class across its legal investor register, token supply, wallets and custodial beneficial records, retaining transfer restrictions and adverse finality evidence. Use for an operational exception review; no network, key, mint, burn or transfer actions."
license: MIT
compatibility: Python 3.10+ standard-library offline supplied JSON; source authentication and institutional/legal acceptance remain external.
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 8 - asset management specialized extensions"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Explicit supplied reviewed mandate and legal scope; no universal jurisdiction pack"
  aws-fsi-owner: "Asset Management investment and operations"
  aws-fsi-primary-user: "Fund administrator / transfer agent / custody control reviewer"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-10-04"
---

# Tokenized fund register and custody review

This optional specialized skill serves a distinct recurring control: reconcile one tokenized fund share class's authoritative investor register to its token ledger and custodial subregisters. It is useful where wallet balances, omnibus beneficial holdings and finality states introduce additional recordkeeping questions beyond a conventional investor-operations review. It does not substitute a token balance for the fund's legal register or assume which record has legal authority.

Establish the fund/share class, constitutional register basis, snapshot date, legal-unit precision, token precision and explicit conversion ratio. Read the [schema](references/schema.md) and [method](references/domain-rules.md). Obtain the fund administrator's issued-unit total, legal register, complete wallet-to-account mapping, ledger supply/finality record, custodial beneficial records and dated transfer-restriction evidence. Preserve unknowns and independently confirm each source's completeness with its owner.

Reconcile official units, legal-account units, per-account token atoms and total ledger supply separately. Reconcile beneficial balances beneath each omnibus account; never add those balances again to the fund's issued total. Review pending/reversed/reorganized transfers separately from the snapshot; the calculator never applies them to balances. Adverse or incomplete finality evidence prevents a confirmed reconciliation even when numbers agree.

Run `python3 -B scripts/validate_input.py REQUEST.json` and `python3 -B scripts/calculate_or_transform.py REQUEST.json`. Validate the saved output against the retained original with `python3 -B scripts/validate_output.py OUTPUT.json --input REQUEST.json`. Draft the [exception packet](assets/output-template.md), retaining exact atomic differences and each unresolved custody, eligibility or finality question.

Read [controls](references/controls.md), [source map](references/source-map.md) and [handoffs](references/handoffs.md) for authority boundaries. Legal title, register authority, custodian control, transfer eligibility and network finality remain institution-owned determinations. No keys, seeds, signing material or credentials belong in the request. The package never queries a network or signs, mints, burns, freezes, reverses or transfers anything.
