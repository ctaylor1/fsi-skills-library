# Adjacent-Skill Handoffs — audit-evidence-packager

Evidence assembly (this skill) is separated from the skills that **produce** the underlying
evidence and from the **testing / attestation** that consumes the package. This skill maps,
redacts, quality-checks, and drafts a package; it never tests a control, concludes, or attests.

## Upstream / lateral (produce evidence this skill maps)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `gl-reconciler` | A request is really a reconciliation break/tie-out that must be produced before it is evidence | reconciliation + tie-out with lineage |
| `financials-normalizer` | Normalized financials underlie a requested artifact | normalized statements + mapping |
| `month-end-close-orchestrator` | Close-package artifacts (JE logs, sign-offs) feed the request list | close artifacts + approval records |
| `regulatory-reporting-data-validator` | A request needs regulatory-report data-validation evidence | validation results + report references |
| `pci-dss-evidence-assistant` | A PCI DSS evidence package is folded into an internal-audit workpaper | evidence package + source index |

## Downstream (consume this skill's package)

| Skill / role | When | Handoff artifact |
| ------------ | ---- | ---------------- |
| `financial-statement-audit-assistant` | The financial-statement audit workpaper builds on the assembled evidence | evidence package + citation index |
| `management-reporting-packager` | A management-reporting pack references the same evidence | package + custody log |
| `risk-control-self-assessment-assistant` | Open items feed a control self-assessment | open-items register + control mapping |
| `policy-procedure-gap-analyzer` | Policy/procedure gaps surfaced in the register need analysis | open-items list + control references |

## Human / specialist handoffs (no skill performs these)

- **Auditor / engagement team** — performs the testing, disposes exceptions, determines control
  operating effectiveness, and forms the audit opinion. This skill never makes those calls.
- **Control owner / management** — signs any management representation/assertion. This skill never
  signs.
- **Audit coordinator** — reviews the draft and authorizes delivery to the auditor; the delivery
  itself is a human-authorized action outside this skill.
- **Remediation owners** — close the open items recorded in the register; the skill only tracks
  the owner/target-date pointers supplied as input.

## Duplicate-execution prevention

- This skill does **not** re-run reconciliations, re-normalize financials, or re-validate
  regulatory data — it maps the evidence those skills produce.
- It does **not** perform the auditor's testing or the signer's attestation.
- The package is a **draft** keyed by `config_version`; the downstream consumer works the same
  package rather than rebuilding it.
