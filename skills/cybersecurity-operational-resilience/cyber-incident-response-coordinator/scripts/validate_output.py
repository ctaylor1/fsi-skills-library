#!/usr/bin/env python3
"""Deterministic output validation for cyber-incident-response-coordinator.

Validates the coordination pack (the calculate_or_transform core + a narrative) before it is
presented or handed off. This is the R3 fail-closed screen: the skill produces a coordination
record with recommendations and evidence ONLY, and must never make an autonomous regulated
decision, set a binding severity, close the incident, or file a regulatory notification.

Checks:
  1. No autonomous decision / closure / filing / binding-classification language, and no
     self-attributed executed response action (revoke/isolate/patch/restore/block/quarantine/
     contain/disable) in free text.
  2. record_status is not a closed/filed/reported state (the agent never closes or files).
  3. Every decision in a terminal state (adjudicated/approved/rejected) names a human decided_by.
  4. severity_suggested equals the deterministic mapping recomputed from the impact block.
  5. Every evidence item and every chronology entry carries a source_ref (citability).
  6. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Coordination record only; recommendations and evidence for human adjudication. "
              "No regulated decision, severity classification, incident closure, regulatory "
              "filing, or system-of-record write has been performed by this skill.")
CLOSED_STATES = {"closed", "filed", "reported", "submitted", "resolved-final"}
TERMINAL_DECISION = {"adjudicated", "approved", "rejected"}

# Autonomous action / closure / filing / binding-decision assertions an R3 coordinator must
# not make. Reminders that obligations "may apply" and routing to humans are permitted; these
# patterns target the agent claiming it decided, closed, filed, or issued a binding call.
PROHIBITED_PATTERNS = [
    r"\b(i|we) (have |ve )?(closed|resolved) the (incident|case)\b",
    r"\bincident (is |has been )?closed\b",
    r"\bcase closed\b",
    r"\bclosing the (incident|case)\b",
    r"\b(i|we) (have |ve )?filed\b",
    r"\bfiled the (breach|regulatory|sar|notification|report)\b",
    r"\bnotification (has been |was )?(sent|filed|submitted)\b",
    r"\breported to the (regulator|authorities|ico|sec|occ|fca)\b",
    r"\bsubmitted the (report|notification|filing)\b",
    r"\b(reporting|notification|filing) is (not )?required\b",
    r"\bno (regulatory )?(reporting|notification) (is )?(needed|required)\b",
    r"\bfinal (severity )?(classification|determination|decision)\b",
    r"\bseverity (is|has been) (officially|formally) (declared|classified|set)\b",
    r"\bofficially declared\b",
    r"\bdecision is final\b",
    r"\bsar (has been |was )?filed\b",
]

# Self-attributed EXECUTED response/containment actions. The coordinator TRACKS these; the
# entitled technical team executes them via their own tools. Recommendations (imperative
# "Isolate segment"), decision text, and chronology entries attributing an action to a named
# technical actor stay permitted — these patterns target the SKILL claiming it itself performed
# a revoke/isolate/patch/restore/block/quarantine/contain/disable (mirrors the DLP and
# security-alert containment screens).
_RESP_VERBS = (r"revoked|isolated|quarantined|contained|blocked|blacklisted|disabled|deactivated|"
               r"suspended|locked|deprovisioned|patched|restored|rebuilt|reimaged|rotated|reset|"
               r"killed|terminated|wiped|remediated|eradicated|recalled|purged")
_RESP_NOUNS = (r"account|identity|user|host|endpoint|device|asset|segment|network|subnet|service|"
               r"system|session|process|credential|token|key|password|ip|domain|url|hash|sender|"
               r"mailbox|inbox|server|share")
RESPONSE_ACTION_PATTERNS = [
    # first-person: "I/we (have) isolated ...", "I/we then revoked ..."
    rf"\b(i|we) (have |ve |had |just |already |then |now )*({_RESP_VERBS})\b",
    # passive with a target noun: "the account has been revoked", "segment was isolated"
    rf"\b(the )?({_RESP_NOUNS})s? (has|have|was|were|is|are) (been )?({_RESP_VERBS})\b",
    # completion assertions for the response phases
    r"\b(containment|eradication|remediation|recovery|isolation) (is|was|has been) "
    r"(complete|completed|executed|performed|actioned|done|in place)\b",
    r"\b(pushed|applied|placed|enforced) (a |the )?(block|quarantine|isolation|containment)\b",
]


def _expected_severity(impact: dict, major: int) -> str:
    tol = bool(impact.get("impact_tolerance_breached"))
    scope = impact.get("scope")
    exposure = bool(impact.get("confirmed_data_exposure"))
    regulated = bool(impact.get("regulated_data"))
    try:
        records = int(impact.get("records_exposed") or 0)
    except (TypeError, ValueError):
        records = 0
    crit = bool(impact.get("critical_service_affected"))
    if tol or scope == "enterprise" or (exposure and regulated and records >= major):
        return "SEV1"
    if crit or exposure or scope == "multi-system":
        return "SEV2"
    if records > 0 or impact.get("suspected_compromise") or scope == "single-system":
        return "SEV3"
    return "SEV4"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    # 1. free-text language screen (narrative/notes/summary + decision + reminder text),
    #    excluding the standing disclaimer field which legitimately names these terms.
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", "")), str(pack.get("summary", ""))]
    for d in pack.get("decisions") or []:
        text_parts.append(str(d.get("recommendation", "")))
        text_parts.append(str(d.get("description", "")))
    for a in pack.get("post_incident_actions") or []:
        text_parts.append(str(a.get("description", "")))
    for r in pack.get("notification_reminders") or []:
        text_parts.append(str(r.get("reminder", "")))
    text = " ".join(text_parts)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"autonomous decision/closure/filing language detected: {m.group(0)!r} "
                          "(R3 coordinates and recommends; humans decide, close, and file)")
    for pat in RESPONSE_ACTION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"executed response-action / containment language detected: {m.group(0)!r} "
                          "(R3 tracks response actions; the entitled technical team executes "
                          "revoke/isolate/patch/restore/block/quarantine/contain/disable)")

    # 2. record_status must not be a closed/filed state
    rs = str(pack.get("record_status", "")).lower()
    if rs in CLOSED_STATES:
        errors.append(f"record_status {rs!r} is a closed/filed state — this skill never closes or files")
    if not rs:
        errors.append("missing record_status")

    # 3. terminal decisions need a human decided_by
    for d in pack.get("decisions") or []:
        if d.get("status") in TERMINAL_DECISION and not (str(d.get("decided_by") or "").strip()):
            errors.append(f"decision {d.get('decision_id')} is {d.get('status')!r} without a human "
                          "decided_by (an adjudicated decision must be made by a named human)")

    # 4. severity tie-out
    impact = pack.get("impact") or {}
    major = int((pack.get("severity_config") or {}).get("major_breach_records", 500))
    exp = _expected_severity(impact, major)
    if pack.get("severity_suggested") != exp:
        errors.append(f"severity_suggested {pack.get('severity_suggested')!r} != deterministic "
                      f"{exp!r} for impact block")

    # 5. citability of evidence + chronology
    for ev in pack.get("evidence") or []:
        if not str(ev.get("source_ref") or "").strip():
            errors.append(f"evidence {ev.get('evidence_id')} missing source_ref (not citable)")
    for i, e in enumerate(pack.get("chronology") or []):
        if not str(e.get("source_ref") or "").strip():
            errors.append(f"chronology[{i}] missing source_ref (not citable)")

    # 6. disclaimer present
    hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in hay:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "coordination_pack.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
