# Adjacent-Skill Handoffs — pci-dss-evidence-assistant

Evidence assembly (this skill) is separated from the specialist reviews that **produce** the
underlying evidence and from the **assessment/attestation** that consumes the package. This
skill maps, flags gaps, and drafts a package; it never determines compliance or attests.

## Upstream / lateral (produce evidence this skill maps)

| Skill | When | Handoff artifact |
| ----- | ---- | ---------------- |
| `vulnerability-prioritization-assistant` | Req 6/11 scan and pen-test findings need triage/prioritization before they are evidence | prioritized findings + scan dates |
| `cloud-security-posture-reviewer` | Req 1/2/6 cloud configuration evidence for CDE systems | posture findings + config references |
| `identity-access-reviewer` | Req 7/8 access-review evidence (least privilege, periodic review) | access-review results + dates |
| `third-party-cyber-risk-reviewer` | Req 12.8 third-party service-provider (TPSP) evidence | TPSP responsibility/assurance records |
| `network-rules-change-tracker` | Card-network rule changes affecting scope/evidence | change log references |

## Downstream (consume this skill's package)

| Skill / role | When | Handoff artifact |
| ------------ | ---- | ---------------- |
| `policy-procedure-gap-analyzer` | Req 12 policy/procedure gaps surfaced in the register | gap list + policy references |
| `risk-control-self-assessment-assistant` | Gaps feed the control self-assessment | gap register + control mapping |
| `regulatory-exam-response-packager` | A QSA RFI / external assessment needs a written response pack | evidence package + citation index |
| `audit-evidence-packager` | Internal audit wants the same evidence organized for an audit workpaper | evidence package + source index |

## Human / specialist handoffs (no skill performs these)

- **QSA or authorized ISA** — performs the formal assessment and the *In Place / Not In
  Place* determinations. This skill never makes those calls.
- **Authorized signer (e.g., CISO/officer)** — signs the AOC/ROC/SAQ. This skill never
  signs or submits.
- **Remediation owners** — close the gaps recorded in the register; the skill only tracks
  owner/target-date pointers supplied as input.

## Duplicate-execution prevention

- This skill does **not** re-run scans, re-review access, or re-assess posture — it maps the
  evidence those specialists produce.
- It does **not** perform the QSA's assessment or the signer's attestation.
- The package is a **draft**; the downstream consumer works the same `config_version`
  package rather than rebuilding it.
