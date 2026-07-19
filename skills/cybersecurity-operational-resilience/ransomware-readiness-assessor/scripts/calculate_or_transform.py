#!/usr/bin/env python3
"""Deterministic, explainable ransomware-readiness findings for ransomware-readiness-assessor.

Reads a readiness-posture extract (see validate_input.py), evaluates the configured control
gaps across the ransomware-readiness domains (identity, segmentation, backups, recovery,
detection, third parties, exercises, communications, critical-service dependencies), attaches
evidence + citations to each fired gap, stages remediation *recommendations* for human
adjudication, and maps the fired set to a suggested remediation-review priority band.

IMPORTANT: This produces explainable *findings, cited evidence, and staged recommendations*
only. It NEVER issues a readiness decision, certifies/attests readiness, accepts risk,
executes or completes a remediation, files a report, or closes the assessment. Every staged
remediation is a candidate marked "staged_for_approval"; a human control owner (CISO office /
operational resilience) adjudicates. The priority mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py readiness.json | --selftest
Prints the readiness JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "restore_test_interval_days": 180,
    "exercise_interval_days": 365,
    "comms_test_interval_days": 365,
    "min_detection_coverage": 0.9,
    "min_privileged_mfa_ratio": 1.0,
    "relevant_exercise_types": ["ransomware_tabletop", "ir", "backup_restore"],
}
DISCLAIMER = ("Ransomware-readiness assessment: evidence and staged remediation "
              "recommendations only; not a readiness decision or attestation. No remediation "
              "has been executed and no assessment has been filed or closed.")
# Gaps that on their own justify elevating the remediation-review priority for a human.
ESCALATORS = {"privileged_mfa_gap", "segmentation_gap", "backup_coverage_gap",
              "backup_immutability_gap", "restore_test_stale", "exercise_overdue"}
# Fired gaps for which the engine stages a remediation candidate.
ACTIONABLE = ESCALATORS
STAGED = "staged_for_approval"


def _parse_date(s):
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _cite(source_ref, date=None):
    return f"rra:{source_ref}" + (f"@{date}" if date else "")


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = _parse_date(doc["as_of"])
    services = doc.get("critical_services") or []
    identity = doc.get("identity")
    third_parties = doc.get("third_parties")
    exercises = doc.get("exercises")
    comms = doc.get("communications")

    findings: list[dict] = []
    not_evaluable: list[dict] = []
    staged: dict[str, dict] = {}  # remediation key -> candidate (deduped)

    def add(name, domain, fired, reason, evidence, criteria):
        findings.append({"finding": name, "domain": domain, "fired": bool(fired),
                         "reason": reason, "evidence": evidence, "criteria": criteria,
                         "contribution": len(evidence) if fired else 0})

    def stage(target_id, related_finding, action, citation):
        key = f"{related_finding}:{target_id}"
        if key not in staged:
            staged[key] = {"remediation_id": key, "target": target_id,
                           "related_finding": related_finding, "action": action,
                           "citation": citation, "status": STAGED}

    # ---------------- identity: privileged MFA + admin tiering ----------------
    if identity:
        total = identity.get("privileged_total")
        with_mfa = identity.get("privileged_with_mfa")
        src = identity.get("source_ref", "identity")
        if isinstance(total, (int, float)) and total > 0 and isinstance(with_mfa, (int, float)):
            ratio = with_mfa / total
            fired = ratio < cfg["min_privileged_mfa_ratio"]
            add("privileged_mfa_gap", "identity", fired,
                f"privileged MFA coverage {ratio:.2f} < required {cfg['min_privileged_mfa_ratio']:.2f}"
                if fired else f"privileged MFA coverage {ratio:.2f} meets requirement",
                [{"privileged_total": total, "privileged_with_mfa": with_mfa,
                  "ratio": round(ratio, 2), "citation": _cite(src)}] if fired else [],
                {"min_privileged_mfa_ratio": cfg["min_privileged_mfa_ratio"]})
            if fired:
                stage("privileged-accounts", "privileged_mfa_gap",
                      "enforce phishing-resistant MFA on all privileged accounts", _cite(src))
        else:
            not_evaluable.append({"finding": "privileged_mfa_gap",
                                  "why": "identity.privileged_total/privileged_with_mfa missing or non-numeric"})
        if "admin_tiering" in identity:
            fired = identity.get("admin_tiering") is not True
            add("admin_tiering_gap", "identity", fired,
                "no administrative tiering / privileged-access workstation model in place"
                if fired else "administrative tiering in place",
                [{"admin_tiering": identity.get("admin_tiering"), "citation": _cite(src)}] if fired else [],
                {"requires": "admin_tiering == true"})
        else:
            not_evaluable.append({"finding": "admin_tiering_gap", "why": "identity.admin_tiering not provided"})
    else:
        not_evaluable.append({"finding": "privileged_mfa_gap", "why": "no identity posture provided"})
        not_evaluable.append({"finding": "admin_tiering_gap", "why": "no identity posture provided"})

    # ---------------- critical-service-linked domains ----------------
    if services:
        seg_ev, cov_ev, imm_ev, rst_ev, det_ev, dep_ev = [], [], [], [], [], []
        det_unknown = 0
        for s in services:
            sid = s.get("service_id", "?")
            src = s.get("source_ref", f"svc={sid}")
            tier = s.get("tier")
            backup = s.get("backup") or {}

            # segmentation (conservative: absence of evidence == gap)
            if s.get("segmented") is not True:
                seg_ev.append({"service_id": sid, "tier": tier, "segmented": s.get("segmented"),
                               "citation": _cite(src)})
                stage(sid, "segmentation_gap",
                      "isolate/segment the critical service to contain lateral movement", _cite(src))

            # backups: coverage vs immutability
            if backup.get("exists") is not True:
                cov_ev.append({"service_id": sid, "tier": tier, "citation": _cite(src)})
                stage(sid, "backup_coverage_gap",
                      "establish a backup for the critical service", _cite(src))
            elif backup.get("immutable") is not True and backup.get("offline_copy") is not True:
                imm_ev.append({"service_id": sid, "tier": tier,
                               "immutable": backup.get("immutable"),
                               "offline_copy": backup.get("offline_copy"), "citation": _cite(src)})
                stage(sid, "backup_immutability_gap",
                      "add an immutable or offline (air-gapped) backup copy", _cite(src))

            # recovery: restore-test freshness (conservative: missing test == stale)
            lrt = s.get("last_restore_test")
            stale = (not lrt) or ((as_of - _parse_date(lrt)).days > cfg["restore_test_interval_days"])
            if stale:
                age = None if not lrt else (as_of - _parse_date(lrt)).days
                rst_ev.append({"service_id": sid, "tier": tier, "last_restore_test": lrt,
                               "days_since": age, "citation": _cite(src, lrt)})
                stage(sid, "restore_test_stale",
                      "perform and evidence a full restore test within the interval", _cite(src, lrt))

            # detection coverage (missing number == not evaluable for this row)
            dc = s.get("detection_coverage")
            if dc is None:
                det_unknown += 1
            elif dc < cfg["min_detection_coverage"]:
                det_ev.append({"service_id": sid, "tier": tier, "detection_coverage": dc,
                               "citation": _cite(src)})

            # dependency mapping (conservative: absence of evidence == gap)
            if s.get("dependency_map") is not True:
                dep_ev.append({"service_id": sid, "tier": tier, "citation": _cite(src)})

        add("segmentation_gap", "segmentation", bool(seg_ev),
            f"{len(seg_ev)} critical service(s) not network-segmented" if seg_ev else "critical services segmented",
            seg_ev, {"requires": "segmented == true"})
        add("backup_coverage_gap", "backups", bool(cov_ev),
            f"{len(cov_ev)} critical service(s) without a backup" if cov_ev else "critical services have backups",
            cov_ev, {"requires": "backup.exists == true"})
        add("backup_immutability_gap", "backups", bool(imm_ev),
            f"{len(imm_ev)} critical-service backup(s) neither immutable nor offline"
            if imm_ev else "critical-service backups are immutable or offline",
            imm_ev, {"requires": "backup.immutable or backup.offline_copy"})
        add("restore_test_stale", "recovery", bool(rst_ev),
            f"{len(rst_ev)} critical service(s) with no/overdue restore test (> {cfg['restore_test_interval_days']}d)"
            if rst_ev else "restore tests are current",
            rst_ev, {"restore_test_interval_days": cfg["restore_test_interval_days"]})
        add("detection_coverage_gap", "detection", bool(det_ev),
            f"{len(det_ev)} critical service(s) below detection coverage {cfg['min_detection_coverage']}"
            if det_ev else "detection coverage meets threshold",
            det_ev, {"min_detection_coverage": cfg["min_detection_coverage"]})
        add("dependency_mapping_gap", "critical-service dependencies", bool(dep_ev),
            f"{len(dep_ev)} critical service(s) without a dependency map" if dep_ev else "critical services mapped",
            dep_ev, {"requires": "dependency_map == true"})
        if det_unknown:
            not_evaluable.append({"finding": "detection_coverage_gap",
                                  "why": f"{det_unknown} service(s) missing detection_coverage (evaluated where present)"})
    else:
        for f in ("segmentation_gap", "backup_coverage_gap", "backup_immutability_gap",
                  "restore_test_stale", "detection_coverage_gap", "dependency_mapping_gap"):
            not_evaluable.append({"finding": f, "why": "no critical_services provided"})

    # ---------------- third parties ----------------
    if third_parties is not None:
        tp_ev = []
        for tp in third_parties:
            if not tp.get("critical"):
                continue
            missing = []
            if tp.get("resilience_evidence") is not True:
                missing.append("resilience_evidence")
            if tp.get("recovery_commitment") is not True:
                missing.append("recovery_commitment")
            if missing:
                tp_ev.append({"tp_id": tp.get("tp_id", "?"), "name": tp.get("name"),
                              "missing": missing, "citation": _cite(tp.get("source_ref", "tp"))})
        add("third_party_resilience_gap", "third parties", bool(tp_ev),
            f"{len(tp_ev)} critical third part(y/ies) without resilience/recovery assurance"
            if tp_ev else "critical third parties have resilience assurance",
            tp_ev, {"requires": "resilience_evidence and recovery_commitment for critical vendors"})
    else:
        not_evaluable.append({"finding": "third_party_resilience_gap", "why": "no third_parties provided"})

    # ---------------- exercises ----------------
    if exercises is not None:
        relevant = [e for e in exercises if e.get("type") in cfg["relevant_exercise_types"]
                    and e.get("last_conducted")]
        latest = max((_parse_date(e["last_conducted"]) for e in relevant), default=None)
        overdue = latest is None or (as_of - latest).days > cfg["exercise_interval_days"]
        latest_s = latest.strftime("%Y-%m-%d") if latest else None
        add("exercise_overdue", "exercises", overdue,
            f"no ransomware/IR exercise within {cfg['exercise_interval_days']}d (latest {latest_s})"
            if overdue else f"exercise current (latest {latest_s})",
            [{"latest_relevant_exercise": latest_s,
              "citation": _cite((relevant[0].get("source_ref") if relevant else "exercises"))}] if overdue else [],
            {"exercise_interval_days": cfg["exercise_interval_days"],
             "relevant_types": cfg["relevant_exercise_types"]})
        if overdue:
            stage("ransomware-exercise", "exercise_overdue",
                  "schedule and conduct a ransomware tabletop / IR exercise",
                  _cite((relevant[0].get("source_ref") if relevant else "exercises")))
    else:
        not_evaluable.append({"finding": "exercise_overdue", "why": "no exercises provided"})

    # ---------------- communications ----------------
    if comms is not None:
        src = comms.get("source_ref", "comms")
        lt = comms.get("last_tested")
        untested = (not lt) or ((as_of - _parse_date(lt)).days > cfg["comms_test_interval_days"])
        no_oob = comms.get("out_of_band") is not True
        fired = no_oob or untested
        reasons = []
        if no_oob:
            reasons.append("no out-of-band crisis-communication channel")
        if untested:
            reasons.append(f"crisis-communication plan not tested within {cfg['comms_test_interval_days']}d")
        add("comms_readiness_gap", "communications", fired,
            "; ".join(reasons) if fired else "crisis communications ready and tested",
            [{"out_of_band": comms.get("out_of_band"), "last_tested": lt, "citation": _cite(src)}] if fired else [],
            {"requires": "out_of_band channel and tested plan"})
    else:
        not_evaluable.append({"finding": "comms_readiness_gap", "why": "no communications posture provided"})

    fired = [f["finding"] for f in findings if f["fired"]]
    if len(fired) >= 3 or (ESCALATORS & set(fired)):
        priority = "Elevated"
    elif fired:
        priority = "Review"
    else:
        priority = "Informational"

    context_prompts = []
    if fired:
        context_prompts = [
            "a documented compensating control or accepted exception is on file for a flagged gap",
            "remediation already in flight but not yet reflected in the evidence extract",
            "the critical service is scheduled for decommission / migration (verify before prioritizing)",
            "backup immutability provided by an out-of-band vault not captured in this extract",
            "an exercise was conducted but its after-action record is not yet logged",
        ]

    return {
        "readiness_id": f"rra-{doc.get('scope','scope')}-{doc['as_of']}-0001",
        "scope": doc.get("scope"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "findings": findings,
        "fired_findings": fired,
        "not_evaluable": not_evaluable,
        "staged_remediations": list(staged.values()),
        "suggested_priority": priority,
        "context_prompts": context_prompts,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "readiness_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
