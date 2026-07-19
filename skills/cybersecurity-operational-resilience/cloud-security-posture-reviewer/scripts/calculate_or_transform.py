#!/usr/bin/env python3
"""Deterministic cloud-security posture review engine for cloud-security-posture-reviewer.

Reads a de-identified cloud posture export (see validate_input.py) and evaluates a fixed
set of documented policy checks across identity, network, encryption, data exposure,
logging, and tagging/region policy. Each fired check produces a finding with a severity,
cited evidence, and a recommended remediation for a human owner. A deterministic mapping
turns the finding set into a remediation-priority disposition.

IMPORTANT: This produces *review findings, evidence, and remediation recommendations only*.
It never makes a compliance attestation, accepts risk, closes/suppresses/waives a finding,
grants an exception, applies or deploys a remediation, changes any cloud configuration, or
writes a system of record. Those remain human, authorized actions. The disposition and every
finding are decision-support for a human cloud/control owner, not a decision.

Severity -> disposition (see references/domain-rules.md):
  any 'critical'          -> remediate_now
  any 'high'   (no crit)  -> remediation_required
  any 'medium'/'low'      -> review_recommended
  else                    -> posture_acceptable

Usage:
  python calculate_or_transform.py posture.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "max_access_key_age_days": 90,
    "critical_ports": [22, 3389],
    "sensitive_ports": [3306, 5432, 1433, 6379, 27017, 9200, 5984],
    "world_cidrs": ["0.0.0.0/0", "::/0"],
    "encryptable_types": ["s3_bucket", "ebs_volume", "rds_instance", "dynamodb_table",
                          "efs_filesystem", "redshift_cluster"],
    "storage_types": ["s3_bucket", "ebs_snapshot", "rds_snapshot", "ami"],
    "allowed_regions": ["us-east-1", "us-west-2", "eu-west-1"],
    "required_tags": ["data-owner", "environment", "cost-center"],
}
DISCLAIMER = ("Posture findings and remediation evidence only; not a compliance attestation "
              "or risk-acceptance decision. No finding closure, suppression, waiver, or risk "
              "acceptance has been made, no exception has been granted, and no cloud "
              "configuration change or remediation has been applied.")

SEV_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _is_sensitive(r: dict) -> bool:
    return bool(r.get("contains_sensitive_data")) or \
        str(r.get("data_classification", "")).lower() in ("restricted", "confidential")


def _covers(rule: dict, port: int) -> bool:
    proto = str(rule.get("protocol", "")).lower()
    if proto in ("-1", "all", "any"):
        return True
    fp, tp = rule.get("from_port"), rule.get("to_port")
    if fp in (None, "") or tp in (None, ""):
        return True  # unbounded range == all ports
    try:
        return int(fp) <= int(port) <= int(tp)
    except (TypeError, ValueError):
        return False


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = str(doc["as_of"])
    version = doc.get("config_version")
    resources = doc.get("resources") or []

    findings: list[dict] = []
    not_evaluable: list[dict] = []
    n = {"c": 0}

    def res_cite(r: dict) -> str:
        return f"cspm:{r.get('source_ref', '?')}@{as_of}"

    def rule_cite(rule: str) -> str:
        return f"config:{version};rule={rule}"

    def add(category, severity, rule, summary, r, remediation):
        n["c"] += 1
        findings.append({
            "finding_id": f"F{n['c']:03d}",
            "category": category,
            "severity": severity,
            "rule": rule,
            "resource_id": r.get("resource_id"),
            "resource_type": r.get("type"),
            "summary": summary,
            "recommended_remediation": remediation,
            "evidence": [
                {"ref": r.get("resource_id", "?"), "citation": res_cite(r)},
                {"ref": f"rule:{rule}", "citation": rule_cite(rule)},
            ],
        })

    world = set(cfg["world_cidrs"])

    for r in resources:
        rtype = str(r.get("type", "")).lower()
        region = str(r.get("region", "")).lower()

        # ---- identity: root access key ------------------------------------
        if rtype in ("account", "aws_account") and r.get("root_access_key_present") is True:
            add("identity", "critical", "identity.root_access_key",
                "Root/organization account has an active access key; root credentials should carry no long-lived key.",
                r, "Delete the root access key and use short-lived, federated credentials for administrative tasks.")

        # ---- identity: MFA disabled on console user -----------------------
        if rtype == "iam_user" and r.get("console_access") is True and r.get("mfa_enabled") is False:
            add("identity", "high", "identity.mfa_disabled",
                "IAM user with console access has no MFA enabled.",
                r, "Enforce MFA for all console-enabled identities via an account-wide policy.")

        # ---- identity: stale access key -----------------------------------
        if rtype == "iam_user":
            age = _num(r.get("access_key_age_days"))
            if age is not None and age > cfg["max_access_key_age_days"]:
                add("identity", "medium", "identity.stale_access_key",
                    f"IAM user access key age {int(age)}d exceeds the maximum {cfg['max_access_key_age_days']}d.",
                    r, "Rotate the access key on the standard schedule and prefer short-lived credentials.")

        # ---- identity: privileged wildcard --------------------------------
        if rtype in ("iam_role", "iam_policy", "iam_user") and r.get("admin_wildcard") is True \
                and r.get("attached", True):
            add("identity", "high", "identity.privileged_wildcard",
                "Attached identity grants wildcard administrative permissions (Action:* on Resource:*).",
                r, "Replace the wildcard grant with least-privilege, scoped permissions.")

        # ---- network: unrestricted ingress --------------------------------
        if rtype == "security_group":
            ingress = r.get("ingress")
            if ingress is None:
                not_evaluable.append({"resource_id": r.get("resource_id"), "rule": "network.unrestricted_ingress",
                                      "why": "no ingress rules on record"})
            else:
                worst = None  # (severity, port)
                for rule in ingress:
                    if str(rule.get("cidr", "")).strip() not in world:
                        continue
                    for p in cfg["critical_ports"]:
                        if _covers(rule, p):
                            worst = ("critical", p)
                    if worst is None or worst[0] != "critical":
                        for p in cfg["sensitive_ports"]:
                            if _covers(rule, p):
                                worst = ("high", p)
                if worst is not None:
                    sev, port = worst
                    add("network", sev, "network.unrestricted_ingress",
                        f"Security group allows ingress from the public internet (0.0.0.0/0) to sensitive port {port}.",
                        r, f"Restrict ingress on port {port} to known CIDRs / a bastion or private path.")

        # ---- data exposure: public access ---------------------------------
        acl = str(r.get("acl", "")).lower()
        if r.get("public_access") is True or acl in ("public-read", "public-read-write"):
            sev = "critical" if _is_sensitive(r) else "high"
            add("data_exposure", sev, "data_exposure.public_access",
                f"Resource is publicly accessible ({'sensitive data classification' if sev == 'critical' else 'no sensitive-data flag'}).",
                r, "Remove public access grants and front the resource with an authenticated, least-privilege access path.")

        # ---- encryption: at rest disabled ---------------------------------
        if rtype in cfg["encryptable_types"]:
            if "encrypted" not in r:
                not_evaluable.append({"resource_id": r.get("resource_id"), "rule": "encryption.at_rest_disabled",
                                      "why": "no 'encrypted' attribute on record"})
            elif r.get("encrypted") is False:
                sev = "critical" if _is_sensitive(r) else "high"
                add("encryption", sev, "encryption.at_rest_disabled",
                    f"Encryption at rest is disabled on a {rtype}"
                    f"{' holding sensitive data' if sev == 'critical' else ''}.",
                    r, "Enable default encryption at rest with a managed key and re-encrypt existing data.")

        # ---- logging: audit log / flow log --------------------------------
        if rtype in ("cloudtrail", "audit_log") and r.get("logging_enabled") is False:
            add("logging", "high", "logging.audit_log_disabled",
                "Account/organization audit logging is disabled; administrative activity is not recorded.",
                r, "Enable a multi-region audit trail with log-file validation and central retention.")
        if rtype in ("cloudtrail", "audit_log") and r.get("logging_enabled") is True \
                and r.get("log_file_validation") is False:
            add("logging", "medium", "logging.log_validation_disabled",
                "Audit log-file integrity validation is disabled.",
                r, "Enable log-file validation so tampering can be detected.")
        if rtype == "vpc" and r.get("flow_logs_enabled") is False:
            add("logging", "medium", "logging.flow_logs_disabled",
                "VPC flow logs are disabled; network telemetry for investigation is unavailable.",
                r, "Enable flow logs to a central logging destination.")

        # ---- policy: disallowed region ------------------------------------
        allowed = [x.lower() for x in (cfg.get("allowed_regions") or [])]
        if allowed and region and region not in ("global", "none") \
                and rtype not in ("account", "aws_account", "iam_user", "iam_role", "iam_policy") \
                and region not in allowed:
            add("policy", "medium", "policy.disallowed_region",
                f"Resource is deployed in region '{region}', which is outside the approved region set.",
                r, "Confirm the deployment is authorized or migrate the resource to an approved region.")

        # ---- policy: missing required tag ---------------------------------
        if isinstance(r.get("tags"), dict):
            present = {str(k).lower() for k in r["tags"].keys()}
            missing = [t for t in cfg.get("required_tags", []) if t.lower() not in present]
            if missing:
                add("policy", "low", "policy.missing_required_tag",
                    f"Resource is missing required governance tag(s): {', '.join(missing)}.",
                    r, "Apply the required governance tags so ownership and cost/data attribution are traceable.")

    # ---- deterministic disposition mapping --------------------------------
    sev_present = {f["severity"] for f in findings}
    if "critical" in sev_present:
        disposition = "remediate_now"
    elif "high" in sev_present:
        disposition = "remediation_required"
    elif sev_present & {"medium", "low"}:
        disposition = "review_recommended"
    else:
        disposition = "posture_acceptable"

    by_sev = {s: sum(1 for f in findings if f["severity"] == s)
              for s in ("critical", "high", "medium", "low")}
    by_cat = sorted({f["category"] for f in findings})

    considerations = []
    if findings:
        considerations = [
            "Remediation deployment, risk acceptance, and exception/waiver approval are the cloud and control owner's decisions; findings only surface evidence.",
            "A finding may be mitigated by a compensating control outside this export (WAF, SCP/guardrail, private network path); confirm before treating it as unmitigated.",
            "Severity is driven by the resource criticality and data-classification labels in the export; verify those labels are accurate for the resource.",
            "Framework mappings (PCI DSS, SOC 2, FFIEC, NIST) may change how a finding is weighted; this skill does not attest to any framework.",
        ]

    handoffs = []
    if any(f["category"] == "identity" for f in findings):
        handoffs.append("identity-access-reviewer (deep IAM entitlement, privileged-access, and certification review; stages revocations for human approval)")
    if any(f["category"] == "data_exposure" for f in findings):
        handoffs.append("data-loss-prevention-incident-assistant (if a public exposure may already have led to data loss and needs incident investigation)")
    handoffs.append("vulnerability-prioritization-assistant (if a finding intersects a known exploitable vulnerability on the same resource)")

    return {
        "review_id": f"cspr-{doc.get('assessment_id', 'assessment')}-{as_of}-0001",
        "assessment_id": doc.get("assessment_id"),
        "as_of": as_of,
        "config_version": version,
        "cloud_provider": doc.get("cloud_provider"),
        "scope": doc.get("scope"),
        "resource_count": len(resources),
        "findings": findings,
        "findings_by_severity": by_sev,
        "fired_categories": by_cat,
        "not_evaluable": not_evaluable,
        "posture_disposition": disposition,
        "reviewer_considerations": considerations,
        "recommended_handoffs": handoffs,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "posture_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
