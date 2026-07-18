# Changelog — pci-dss-evidence-assistant

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to help a PCI
program manager or security/compliance analyst assemble an assessor-ready **draft** evidence
package without crossing into assessment or attestation.

- **Scope:** map PCI DSS v4.0.1 requirements to controls and cited evidence, compute
  evidence-readiness (complete / gap / stale / needs-data / not-applicable) against versioned
  freshness windows, build a gap/remediation register, and render the package from the
  controlled template. Draft-only; no system-of-record change; never sends or submits.
- **Controls:** R2 / `external-delivery`. Hard boundary — no compliance attestation, no
  *In Place* / *Not In Place* determination, no AOC/ROC/SAQ signing or submission, no external
  transmission, no cardholder data (PAN/SAD) in the package, no scope validation.
- **Scripts:** `validate_input` (requirements/controls/evidence schema, freshness/date checks,
  needs-data/gap warnings), `calculate_or_transform` (requirement-to-control-to-evidence
  mapping, freshness-based staleness, gap register, template rendering, `attestation_made:
  false`), `validate_output` (template fidelity, no unsupported claims / dangling citations,
  attestation-language screen, approvals recorded, standing note). Each supports `--selftest`
  against a bundled fixture and prints a line ending "N error(s)".
- **Assets:** `assets/output-template.md` — the eight required package sections, headers
  enforced by `validate_output`.
- **Evaluations:** trigger/routing (to `vulnerability-prioritization-assistant`,
  `regulatory-exam-response-packager`), a golden 9-requirement task exercising every readiness
  status, deterministic script checks, and a safety check running `validate_output` on a
  non-compliant package (attestation language + unsupported claims + missing sections) that
  must fail closed with exit 1.
- **Handoffs:** upstream/lateral to `vulnerability-prioritization-assistant`,
  `cloud-security-posture-reviewer`, `identity-access-reviewer`, `third-party-cyber-risk-reviewer`,
  `network-rules-change-tracker`; downstream to `policy-procedure-gap-analyzer`,
  `risk-control-self-assessment-assistant`, `regulatory-exam-response-packager`,
  `audit-evidence-packager`. QSA/authorized-ISA assessment and authorized-signer attestation
  are human-only.

### Pending before release
- PCI QSA/ISA + payments-risk control-owner blind review of the readiness taxonomy and the
  attestation-boundary guardrails.
- Confirm the freshness-window and remediation config source, owner, and versioning; align
  windows to the organization's PCI program standard and the pinned DSS version.
- Wire read-only MCP integrations (PCI-standard/SAQ retrieval, GRC/evidence repository,
  scanners, CMDB, IAM, ticketing) at deployment.
