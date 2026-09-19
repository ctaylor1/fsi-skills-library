"""Family discussion evidence and audience-safe drafts. No legal authority or action."""

from copy import deepcopy

from wealth_contract import iso_date, make_output, nonempty
from wealth_workflow import (
    add,
    base_errors,
    base_findings,
    cited,
    common_result,
    dec,
    enum,
    number,
    rows,
    texts,
    validate_result,
)

SKILL = "family-wealth-governance-preparer"
KINDS = {"discussion", "family-discussion-agreement", "legal-authority-question"}
POSITION = {"support", "oppose", "abstain", "not-recorded"}


def whole(value, lo=1, hi=1440):
    return number(value, lo, hi) and dec(value) == dec(value).to_integral_value()


def validate(doc):
    errors = base_errors(doc)
    if errors:
        return errors
    allowed = {
        "schema_version",
        "request_id",
        "household_id",
        "as_of",
        "engagement",
        "sources",
        "policy",
        "upstream_issues",
        "scope_type",
        "family_id",
        "scope_source_ids",
        "members",
        "roles",
        "topics",
        "succession",
        "education",
        "followups",
        "audience",
        "meeting",
    }
    if set(doc) - allowed:
        errors.append("unsupported top-level fields: " + ", ".join(sorted(set(doc) - allowed)))
    if (
        doc.get("scope_type") != "family-group"
        or not nonempty(doc.get("family_id"))
        or doc["household_id"] != "family:" + str(doc.get("family_id"))
    ):
        errors.append("scope requires family-group, family_id and household_id family:<family_id>")
    members = rows(doc, "members", errors, "member_id")
    roles = rows(doc, "roles", errors, "role_id")
    topics = rows(doc, "topics", errors, "topic_id")
    plans = rows(doc, "succession", errors, "succession_id")
    education = rows(doc, "education", errors, "education_id")
    followups = rows(doc, "followups", errors, "followup_id")
    policy = doc["policy"]
    rules = rows(policy, "decision_rules", errors, "rule_id")
    criteria = rows(policy, "succession_criteria", errors, "criterion_id")
    if not members or not topics:
        errors.append("at least one member and substantive topic required; no empty family readiness")
    if not rules or (plans and not criteria):
        errors.append("policy requires decision rules and nonempty succession criteria when succession is reviewed")
    if errors:
        return errors
    member_ids = {m["member_id"] for m in members}
    role_ids = {r["role_id"] for r in roles}
    topic_ids = {t["topic_id"] for t in topics}
    rule_ids = {r["rule_id"] for r in rules}
    criterion_ids = {c["criterion_id"] for c in criteria}

    def text_fields(row, fields, path):
        for field in fields:
            if not nonempty(row.get(field)):
                errors.append(f"{path}.{field} requires substantive nonempty text")

    def date(row, key, path, future=False, nullable=False):
        value = row.get(key)
        if value is None and nullable:
            return
        if iso_date(value) is None or (not future and value > doc["as_of"]):
            errors.append(f"{path}.{key} requires an ISO date" + ("" if future else " no later than as_of"))

    def ref(row, key, ids, path, nullable=False):
        value = row.get(key)
        if value is None and nullable:
            return
        if not isinstance(value, str) or value not in ids:
            errors.append(f"{path}.{key} must reference a declared record")

    def refs(row, key, ids, path, empty=False):
        value = row.get(key)
        if not texts(value, allow_empty=empty) or (
            isinstance(value, list) and any(not isinstance(x, str) or x not in ids for x in value)
        ):
            errors.append(f"{path}.{key} must contain unique declared IDs")

    def access(row, path):
        value = row.get("access")
        if value is not None:
            if not isinstance(value, dict):
                errors.append(f"{path}.access must be object or null")
            else:
                refs(value, "allowed_member_ids", member_ids, path + ".access", empty=True)

    for row in rules:
        text_fields(row, ["description"], "decision rule")
        if not enum(row.get("method"), {"unanimity", "majority-of-all-eligible", "discussion-only"}) or not whole(
            row.get("quorum_min"), 1, 1000
        ):
            errors.append("decision rule requires supported method and integer quorum_min 1..1000")
        access(row, "decision rule")
    for row in criteria:
        text_fields(row, ["description"], "succession criterion")
        access(row, "policy succession criterion")
    access(policy, "policy")
    for row in members:
        text_fields(row, ["label"], "member")
        if not enum(row.get("kind"), {"family-member", "professional"}):
            errors.append("member.kind must be family-member or professional")
        hid = row.get("household_id")
        if row.get("kind") == "family-member" and (not nonempty(hid) or hid.startswith(("family:", "book:", "trust:"))):
            errors.append("family member requires actual household_id, never a collection marker")
        if row.get("kind") == "professional" and hid is not None:
            errors.append("professional household_id must be explicit null")
        if not enum(row.get("participation_status"), {"willing", "declined", "unknown"}):
            errors.append("member participation must be willing, declined or unknown")
        date(row, "participation_as_of", "member", nullable=True)
        access(row, "member")
    for row in roles:
        ref(row, "member_id", member_ids, "role", nullable=True)
        text_fields(row, ["label", "scope_description"], "role")
        if not enum(row.get("authority_type"), {"family-discussion-role", "legal-role-assertion", "unknown"}):
            errors.append("role authority_type must distinguish family discussion from legal assertion")
        date(row, "review_date", "role", nullable=True)
        date(row, "review_by", "role", future=True, nullable=True)
        if (
            iso_date(row.get("review_date"))
            and iso_date(row.get("review_by"))
            and row["review_by"] < row["review_date"]
        ):
            errors.append("role review_by precedes review_date")
        if row.get("basis_reference") is not None and not nonempty(row["basis_reference"]):
            errors.append("role basis_reference must be nonempty or null")
        ref(row, "reviewer_member_id", member_ids, "role", nullable=True)
        access(row, "role")
    sequences = set()
    for row in topics:
        path = "topic." + row["topic_id"]
        text_fields(row, ["title", "question", "proposed_decision"], path)
        if not enum(row.get("decision_class"), KINDS):
            errors.append("topic decision_class is unsupported")
        if not whole(row.get("sequence"), 1, 1000) or (
            whole(row.get("sequence"), 1, 1000) and int(dec(row["sequence"])) in sequences
        ):
            errors.append("topic sequence must be a unique integer 1..1000")
        else:
            sequences.add(int(dec(row["sequence"])))
        if row.get("minutes") is not None and not whole(row["minutes"]):
            errors.append("topic minutes must be integer 1..1440 or null")
        refs(row, "eligible_member_ids", member_ids, path)
        refs(row, "role_ids", role_ids, path, empty=True)
        ref(row, "rule_id", rule_ids, path)
        responses = rows(row, "responses", errors, "member_id")
        for response in responses:
            ref(response, "member_id", member_ids, "response")
            if (
                isinstance(row.get("eligible_member_ids"), list)
                and response.get("member_id") not in row["eligible_member_ids"]
            ):
                errors.append("response member must belong to topic eligible member inventory")
            if not enum(response.get("position"), POSITION) or not enum(
                response.get("participation"), {"in-person", "written", "not-participating", "unknown"}
            ):
                errors.append("response needs explicit supported position and participation")
            if enum(response.get("participation"), {"not-participating", "unknown"}) and enum(
                response.get("position"), {"support", "oppose", "abstain"}
            ):
                errors.append("a recorded position requires in-person or written participation evidence")
            text_fields(response, ["statement"], "response")
            date(response, "recorded_on", "response", nullable=True)
            access(response, "response")
        access(row, path)
    for row in plans:
        ref(row, "topic_id", topic_ids, "succession")
        ref(row, "role_id", role_ids, "succession")
        linked_topic = next((t for t in topics if t["topic_id"] == row.get("topic_id")), None)
        if (
            linked_topic is not None
            and isinstance(linked_topic.get("role_ids"), list)
            and row.get("role_id") not in linked_topic["role_ids"]
        ):
            errors.append("succession role must be explicitly included in its topic role_ids")
        ref(row, "candidate_member_id", member_ids, "succession", nullable=True)
        if not enum(row.get("candidate_interest"), {"confirmed", "declined", "unknown"}):
            errors.append("succession candidate_interest must be confirmed, declined or unknown")
        date(row, "interest_as_of", "succession", nullable=True)
        date(row, "target_date", "succession", future=True, nullable=True)
        if iso_date(row.get("target_date")) and row["target_date"] < doc["as_of"]:
            errors.append("succession target_date cannot precede as_of")
        for criterion in rows(row, "criteria_evidence", errors, "criterion_id"):
            ref(criterion, "criterion_id", criterion_ids, "succession criterion")
            text_fields(criterion, ["observation"], "succession criterion")
            if not enum(criterion.get("status"), {"documented", "incomplete", "unknown", "not-applicable"}):
                errors.append("succession criterion status is invalid")
            ref(criterion, "reviewer_member_id", member_ids, "succession criterion", nullable=True)
            date(criterion, "review_date", "succession criterion", nullable=True)
            date(criterion, "review_by", "succession criterion", future=True, nullable=True)
            if (
                iso_date(criterion.get("review_date"))
                and iso_date(criterion.get("review_by"))
                and criterion["review_by"] < criterion["review_date"]
            ):
                errors.append("criterion review_by precedes review_date")
            access(criterion, "succession criterion")
        access(row, "succession")
    for row in education:
        ref(row, "topic_id", topic_ids, "education")
        refs(row, "participant_member_ids", member_ids, "education")
        ref(row, "facilitator_member_id", member_ids, "education", nullable=True)
        text_fields(row, ["learning_need_basis", "learning_objective", "proposed_activity"], "education")
        if row.get("minutes") is not None and not whole(row["minutes"]):
            errors.append("education minutes must be integer 1..1440 or null")
        access(row, "education")
    for row in followups:
        ref(row, "topic_id", topic_ids, "followup")
        ref(row, "owner_member_id", member_ids, "followup", nullable=True)
        text_fields(row, ["description"], "followup")
        date(row, "due_on", "followup", future=True, nullable=True)
        if not enum(row.get("status"), {"proposed", "agreed", "completed", "unknown"}) or not enum(
            row.get("owner_acceptance"), {"confirmed", "declined", "unknown"}
        ):
            errors.append("followup requires explicit status and owner acceptance")
        completion = row.get("completion_evidence")
        if completion is not None:
            if not isinstance(completion, dict):
                errors.append("completion_evidence must be object or null")
            else:
                ref(completion, "reviewer_member_id", member_ids, "completion")
                text_fields(completion, ["reference"], "completion")
                date(completion, "as_of", "completion")
                access(completion, "completion")
        access(row, "followup")
    audience = doc.get("audience")
    if not isinstance(audience, dict):
        errors.append("audience object required")
    else:
        refs(audience, "member_ids", member_ids, "audience")
        text_fields(audience, ["purpose"], "audience")
    meeting = doc.get("meeting")
    if not isinstance(meeting, dict):
        errors.append("meeting object required")
    else:
        refs(meeting, "participant_member_ids", member_ids, "meeting")
        ref(meeting, "facilitator_member_id", member_ids, "meeting", nullable=True)
        date(meeting, "proposed_date", "meeting", future=True, nullable=True)
        if (
            iso_date(meeting.get("proposed_date"))
            and not doc["as_of"] <= meeting["proposed_date"] <= policy["valid_until"]
        ):
            errors.append("proposed meeting date must be current/future and covered by policy")
        if meeting.get("available_minutes") is not None and not whole(meeting["available_minutes"]):
            errors.append("meeting available_minutes must be integer 1..1440 or null")
    return errors


def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    findings = base_findings(doc)
    policy_ok = cited(doc["policy"], doc, findings, "policy") and cited(doc["engagement"], doc, findings, "engagement")
    scope_ok = cited({"source_ids": doc.get("scope_source_ids")}, doc, findings, "family_scope")
    audience_ok = cited(doc["audience"], doc, findings, "audience")
    recipients = set(doc["audience"]["member_ids"])
    members = {m["member_id"]: m for m in doc["members"]}
    roles = {r["role_id"]: r for r in doc["roles"]}
    topics = {t["topic_id"]: t for t in doc["topics"]}
    rules = {r["rule_id"]: r for r in doc["policy"]["decision_rules"]}
    criteria = {c["criterion_id"]: c for c in doc["policy"]["succession_criteria"]}
    supported = {}
    shareable = {}

    def qualify(row, path):
        ok = cited(row, doc, findings, path)
        access = row.get("access")
        if not isinstance(access, dict):
            add(
                findings,
                "audience-boundary-unknown",
                "Record disclosure boundary is unknown; exclude it from audience draft.",
                path,
            )
            visible = False
        else:
            access_ok = cited(access, doc, findings, path + ".access")
            visible = access_ok and recipients <= set(access["allowed_member_ids"])
        supported[id(row)] = ok
        shareable[id(row)] = ok and visible and audience_ok and scope_ok and policy_ok
        return ok

    def visible(*records):
        return shareable.get(id(doc["policy"]), False) and all(
            row is not None and shareable.get(id(row), False) for row in records
        )

    qualify(doc["policy"], "policy")
    for kind in ("members", "roles", "topics", "succession", "education", "followups"):
        for row in doc[kind]:
            qualify(row, kind)
    rule_ok = {rid: qualify(r, "policy.decision_rules." + rid) for rid, r in rules.items()}
    criterion_ok = {cid: qualify(c, "policy.succession_criteria." + cid) for cid, c in criteria.items()}
    for member in members.values():
        if member["participation_status"] == "unknown" or member.get("participation_as_of") is None:
            add(
                findings,
                "participation-unknown",
                "Obtain the person’s own dated participation preference; do not infer it from age or family role.",
                "members." + member["member_id"],
            )
    role_results = []
    role_supported = {}
    for rid, role in roles.items():
        holder = members.get(role.get("member_id"))
        reviewer = members.get(role.get("reviewer_member_id"))
        current = (
            supported[id(role)]
            and holder is not None
            and supported[id(holder)]
            and reviewer is not None
            and supported[id(reviewer)]
            and role.get("basis_reference") is not None
            and role.get("review_date") is not None
            and role.get("review_by") is not None
            and role["review_by"] >= doc["as_of"]
            and role["authority_type"] != "unknown"
        )
        role_supported[rid] = current and policy_ok and scope_ok
        if not role_supported[rid]:
            add(
                findings,
                "role-evidence-gap",
                "Role holder, scope, basis or attributed current review is missing.",
                "roles." + rid,
            )
        role_results.append(
            {
                "role": deepcopy(role),
                "evidence_state": "documented-assertion" if role_supported[rid] else "incomplete",
                "legal_authority": "not-determined",
            }
        )
    decision_register = []
    topic_visible = {}
    for topic in sorted(doc["topics"], key=lambda t: int(dec(t["sequence"]))):
        tid = topic["topic_id"]
        rule = rules[topic["rule_id"]]
        response_map = {r["member_id"]: r for r in topic["responses"]}
        counts = {key: 0 for key in POSITION}
        present = 0
        evidence_complete = supported[id(topic)] and policy_ok and scope_ok and rule_ok[topic["rule_id"]]
        positions = []
        contributors = (
            [topic, rule]
            + [members[mid] for mid in topic["eligible_member_ids"]]
            + [roles[rid] for rid in topic["role_ids"]]
        )
        for rid in topic["role_ids"]:
            contributors += [members.get(roles[rid].get(key)) for key in ("member_id", "reviewer_member_id")]
        for mid in topic["eligible_member_ids"]:
            response = response_map.get(mid)
            ok = False
            if response is not None:
                ok = (
                    qualify(response, "topics." + tid + ".responses." + mid)
                    and response.get("recorded_on") is not None
                    and supported[id(members[mid])]
                )
                contributors.append(response)
            position = response["position"] if response is not None and ok else "not-recorded"
            counts[position] += 1
            if ok and response["participation"] in {"in-person", "written"}:
                present += 1
            if not ok or position == "not-recorded":
                evidence_complete = False
                add(
                    findings,
                    "position-unrecorded",
                    "No supported attributed position; silence is not agreement.",
                    "topics." + tid + ".responses." + mid,
                )
            positions.append(
                {
                    "member_id": mid,
                    "household_id": members[mid].get("household_id"),
                    "position": position,
                    "record": deepcopy(response),
                    "evidence_supported": ok,
                }
            )
        if int(dec(rule["quorum_min"])) > len(topic["eligible_member_ids"]):
            evidence_complete = False
            add(findings, "quorum-rule-gap", "Policy quorum exceeds the declared eligible group.", "topics." + tid)
        quorum = (
            present >= int(dec(rule["quorum_min"]))
            and rule_ok[topic["rule_id"]]
            and supported[id(topic)]
            and policy_ok
            and scope_ok
        )
        if not quorum:
            add(
                findings,
                "quorum-not-evidenced",
                "Recorded participation does not establish the supplied family-process quorum.",
                "topics." + tid,
            )
        if any(not role_supported[rid] for rid in topic["role_ids"]):
            evidence_complete = False
        observation = "not-evaluable"
        if topic["decision_class"] == "legal-authority-question":
            observation = "legal-review-required"
            add(
                findings,
                "legal-authority-boundary",
                "Family positions do not determine authority under trusts, estates or corporate instruments.",
                "topics." + tid,
            )
        elif topic["decision_class"] == "discussion" or rule["method"] == "discussion-only":
            observation = "discussion-only"
        elif evidence_complete and quorum:
            threshold = (
                counts["support"] == len(topic["eligible_member_ids"])
                if rule["method"] == "unanimity"
                else counts["support"] * 2 > len(topic["eligible_member_ids"])
            )
            observation = "documented-support-threshold-met" if threshold else "no-documented-support-threshold"
        if counts["oppose"]:
            add(
                findings,
                "recorded-dissent",
                "A documented opposing position remains in the register; do not fabricate consensus.",
                "topics." + tid,
            )
        decision_register.append(
            {
                "topic": deepcopy(topic),
                "decision_rule": deepcopy(rule),
                "positions": positions,
                "position_counts": counts,
                "eligible_count": len(topic["eligible_member_ids"]),
                "recorded_participation_count": present,
                "quorum_evidenced": quorum,
                "evidence_complete": evidence_complete,
                "process_observation": observation,
                "consensus_claim": "not-made",
                "legal_authority": "not-determined",
            }
        )
        topic_visible[tid] = visible(*contributors)
    succession_register = []
    succession_visible = {}
    for plan in doc["succession"]:
        sid = plan["succession_id"]
        role = roles[plan["role_id"]]
        candidate = members.get(plan.get("candidate_member_id"))
        ready = (
            supported[id(plan)]
            and policy_ok
            and scope_ok
            and role_supported[plan["role_id"]]
            and candidate is not None
            and supported[id(candidate)]
            and plan["candidate_interest"] == "confirmed"
            and plan.get("interest_as_of") is not None
            and plan.get("target_date") is not None
        )
        if not ready:
            add(
                findings,
                "succession-context-gap",
                "Candidate interest, role evidence or transition target remains unknown or unsupported.",
                "succession." + sid,
            )
        evidence = {c["criterion_id"]: c for c in plan["criteria_evidence"]}
        reviewed = []
        contributors = [plan, role, candidate]
        for cid, requirement in criteria.items():
            contributors.append(requirement)
            row = evidence.get(cid)
            complete = False
            if row is not None:
                reviewer = members.get(row.get("reviewer_member_id"))
                complete = (
                    qualify(row, "succession." + sid + ".criteria." + cid)
                    and criterion_ok[cid]
                    and row["status"] == "documented"
                    and reviewer is not None
                    and supported[id(reviewer)]
                    and row.get("review_date") is not None
                    and row.get("review_by") is not None
                    and row["review_by"] >= doc["as_of"]
                )
                contributors += [row, reviewer]
            if not complete:
                ready = False
                add(
                    findings,
                    "succession-criterion-gap",
                    "Required criterion lacks attributed current supporting evidence; no readiness inferred.",
                    "succession." + sid + ".criteria." + cid,
                )
            reviewed.append(
                {"criterion": deepcopy(requirement), "evidence": deepcopy(row), "evidence_complete": complete}
            )
        state = "evidence-complete-for-discussion" if ready else "incomplete-evidence"
        if role["authority_type"] == "legal-role-assertion":
            state = "legal-review-required"
            add(
                findings,
                "succession-legal-review",
                "A family succession discussion does not appoint a legal successor or establish activation of authority.",
                "succession." + sid,
            )
        succession_register.append(
            {
                "plan": deepcopy(plan),
                "criteria_review": reviewed,
                "readiness": state,
                "appointment_status": "not-appointed-by-this-artifact",
                "assessment_basis": "Attributed supplied criteria only; no age, wealth, personality or psychological inference.",
            }
        )
        succession_visible[sid] = topic_visible[plan["topic_id"]] and visible(*contributors)
    meeting = doc["meeting"]
    meeting_ok = cited(meeting, doc, findings, "meeting")
    if (
        meeting.get("facilitator_member_id") is None
        or meeting.get("proposed_date") is None
        or meeting.get("available_minutes") is None
    ):
        add(
            findings,
            "meeting-context-gap",
            "Meeting date, facilitator or time budget is unknown; nothing is scheduled.",
            "meeting",
        )
        meeting_ok = False
    facilitator = members.get(meeting.get("facilitator_member_id"))
    if facilitator is None or not supported[id(facilitator)]:
        add(findings, "meeting-facilitator-gap", "Facilitator identity is missing or unsupported.", "meeting")
        meeting_ok = False
    for mid in meeting["participant_member_ids"]:
        member = members[mid]
        if (
            not supported[id(member)]
            or member["participation_status"] != "willing"
            or member.get("participation_as_of") is None
        ):
            add(
                findings,
                "meeting-participation-gap",
                "A proposed attendee lacks a sourced dated willingness to participate.",
                "meeting.participants." + mid,
            )
            meeting_ok = False
    agenda = []
    education_results = []
    education_visible = {}
    for topic in sorted(doc["topics"], key=lambda t: int(dec(t["sequence"]))):
        agenda.append(
            {
                "kind": "discussion",
                "item_id": topic["topic_id"],
                "topic_id": topic["topic_id"],
                "purpose": topic["question"],
                "minutes": int(dec(topic["minutes"])) if topic.get("minutes") is not None else None,
                "source_ids": deepcopy(topic.get("source_ids")),
            }
        )
        for lesson in [e for e in doc["education"] if e["topic_id"] == topic["topic_id"]]:
            facilitator = members.get(lesson.get("facilitator_member_id"))
            lesson_ok = (
                supported[id(lesson)]
                and supported[id(topic)]
                and policy_ok
                and scope_ok
                and facilitator is not None
                and supported[id(facilitator)]
                and lesson.get("minutes") is not None
                and set(lesson["participant_member_ids"]) <= set(meeting["participant_member_ids"])
            )
            for mid in lesson["participant_member_ids"]:
                member = members[mid]
                if (
                    member["participation_status"] != "willing"
                    or not supported[id(member)]
                    or member.get("participation_as_of") is None
                ):
                    lesson_ok = False
            if not lesson_ok:
                add(
                    findings,
                    "education-evidence-gap",
                    "Learning activity needs supported participants, facilitator and duration; do not infer readiness or interest.",
                    "education." + lesson["education_id"],
                )
            education_results.append(
                {
                    "record": deepcopy(lesson),
                    "preparation_state": "documented-proposal" if lesson_ok else "needs-review",
                    "learning_outcome": "not-assessed",
                }
            )
            education_visible[lesson["education_id"]] = topic_visible[lesson["topic_id"]] and visible(
                lesson, facilitator, *[members[mid] for mid in lesson["participant_member_ids"]]
            )
            agenda.append(
                {
                    "kind": "education",
                    "item_id": lesson["education_id"],
                    "topic_id": lesson["topic_id"],
                    "purpose": lesson["learning_objective"],
                    "minutes": int(dec(lesson["minutes"])) if lesson.get("minutes") is not None else None,
                    "source_ids": deepcopy(lesson.get("source_ids")),
                }
            )
    known_minutes = sum(row["minutes"] or 0 for row in agenda)
    all_minutes = (
        all(row["minutes"] is not None for row in agenda)
        and policy_ok
        and scope_ok
        and all(supported[id(row)] for row in doc["topics"] + doc["education"])
    )
    if not all_minutes:
        add(
            findings,
            "agenda-duration-unknown",
            "Unknown agenda duration is not zero; total duration remains unknown.",
            "agenda",
        )
    available = (
        int(dec(meeting["available_minutes"])) if meeting.get("available_minutes") is not None and meeting_ok else None
    )
    if available is not None and known_minutes > available:
        add(
            findings,
            "agenda-over-budget",
            "Known discussion and education time exceeds the supplied meeting budget.",
            "agenda",
        )
    followup_register = []
    followup_visible = {}
    for followup in doc["followups"]:
        fid = followup["followup_id"]
        owner = members.get(followup.get("owner_member_id"))
        completion = followup.get("completion_evidence")
        complete = (
            supported[id(followup)]
            and policy_ok
            and scope_ok
            and supported[id(topics[followup["topic_id"]])]
            and owner is not None
            and supported[id(owner)]
            and followup.get("due_on") is not None
            and followup["owner_acceptance"] == "confirmed"
        )
        state = "owned-draft" if complete else "needs-owner-or-evidence"
        contributors = [followup, owner]
        if not complete:
            add(
                findings,
                "followup-context-gap",
                "Follow-up owner, acceptance, due date or source is missing; no assignment inferred.",
                "followups." + fid,
            )
        if followup["status"] == "completed":
            if completion is not None:
                reviewer = members[completion["reviewer_member_id"]]
                completion_ok = (
                    qualify(completion, "followups." + fid + ".completion_evidence") and supported[id(reviewer)]
                )
                contributors += [completion, reviewer]
            else:
                completion_ok = False
            if not completion_ok:
                state = "completion-unverified"
                add(
                    findings,
                    "completion-evidence-gap",
                    "A completed label without cited completion evidence cannot close the draft follow-up.",
                    "followups." + fid,
                )
            elif complete:
                state = "recorded-completion-for-review"
        elif followup.get("due_on") is not None and followup["due_on"] < doc["as_of"]:
            add(
                findings,
                "followup-overdue",
                "An unfinished follow-up is past its supplied due date.",
                "followups." + fid,
            )
        if followup["status"] == "unknown":
            add(
                findings,
                "followup-status-unknown",
                "Follow-up progress is unknown; do not infer work completed.",
                "followups." + fid,
            )
        followup_register.append({"record": deepcopy(followup), "draft_state": state, "action_taken": False})
        followup_visible[fid] = topic_visible[followup["topic_id"]] and visible(*contributors)
    result = common_result(doc)
    subject = {
        "scope_type": "family-group",
        "family_id": doc["family_id"],
        "collection_marker": doc["household_id"],
        "members": [{"member_id": m["member_id"], "household_id": m.get("household_id")} for m in doc["members"]],
        "actual_household_ids": sorted({m["household_id"] for m in doc["members"] if m["kind"] == "family-member"}),
    }
    result["handoff_context"].update(
        scope_type="family-group", family_id=doc["family_id"], member_household_mapping=deepcopy(subject["members"])
    )
    result.update(
        family_subject=subject,
        classification="internal-review-only; contains restricted source snapshot",
        role_register=role_results,
        decision_register=decision_register,
        succession_register=succession_register,
        education_register=education_results,
        followup_register=followup_register,
        meeting_plan={
            "record": deepcopy(meeting),
            "agenda": agenda,
            "known_minutes": known_minutes,
            "total_minutes": known_minutes if all_minutes else None,
            "supported_available_minutes": available,
            "remaining_minutes": available - known_minutes if available is not None and all_minutes else None,
            "scheduled": False,
        },
        boundaries={
            "legal_authority": "not-determined",
            "family_consensus": "not-fabricated; individual positions preserved",
            "succession": "No legal appointment or personal-capacity assessment.",
            "disclosure": "Full artifact is internal-only. Audience draft is a filtered candidate requiring human confidentiality review; no delivery.",
        },
    )
    safe_topics = [deepcopy(row) for row in decision_register if topic_visible[row["topic"]["topic_id"]]]
    if not safe_topics:
        add(
            findings,
            "audience-content-unavailable",
            "No substantive topic can be included for the requested audience under the supplied record boundaries.",
            "audience",
        )
    safe_succession = [deepcopy(row) for row in succession_register if succession_visible[row["plan"]["succession_id"]]]
    safe_education = [deepcopy(row) for row in education_results if education_visible[row["record"]["education_id"]]]
    safe_followups = [deepcopy(row) for row in followup_register if followup_visible[row["record"]["followup_id"]]]
    # Project safe substantive fields only. Never embed raw records/access lists, the source
    # registry, internal findings, hidden item identifiers or the full snapshot in this view.
    audience_draft = {
        "family_id": doc["family_id"],
        "as_of": doc["as_of"],
        "audience_member_ids": sorted(recipients),
        "purpose": doc["audience"]["purpose"],
        "human_review_required": True,
        "delivery_status": "not-delivered",
        "notice": "Audience-specific draft; facilitator and confidentiality review required. Internal source review is separate.",
        "topics": [
            {
                "topic_id": r["topic"]["topic_id"],
                "title": r["topic"]["title"],
                "question": r["topic"]["question"],
                "proposed_decision": r["topic"]["proposed_decision"],
                "process_observation": r["process_observation"],
                "legal_authority": "not-determined",
                "positions": [
                    {
                        "member_id": p["member_id"],
                        "position": p["position"],
                        "statement": p["record"]["statement"] if p["record"] else "No attributed statement supplied.",
                    }
                    for p in r["positions"]
                ],
                "source_ids": deepcopy(r["topic"].get("source_ids")),
            }
            for r in safe_topics
        ],
        "succession": [
            {
                "succession_id": r["plan"]["succession_id"],
                "candidate_member_id": r["plan"]["candidate_member_id"],
                "role_id": r["plan"]["role_id"],
                "role_label": roles[r["plan"]["role_id"]]["label"],
                "role_scope": roles[r["plan"]["role_id"]]["scope_description"],
                "authority_type": roles[r["plan"]["role_id"]]["authority_type"],
                "target_date": r["plan"].get("target_date"),
                "readiness": r["readiness"],
                "appointment_status": "not-appointed-by-this-artifact",
                "criteria": [
                    {
                        "criterion_id": c["criterion"]["criterion_id"],
                        "description": c["criterion"]["description"],
                        "observation": c["evidence"]["observation"]
                        if c["evidence"]
                        else "Missing attributed evidence.",
                        "evidence_complete": c["evidence_complete"],
                    }
                    for c in r["criteria_review"]
                ],
            }
            for r in safe_succession
        ],
        "education": [
            {
                "education_id": r["record"]["education_id"],
                "participant_member_ids": deepcopy(r["record"]["participant_member_ids"]),
                "learning_objective": r["record"]["learning_objective"],
                "proposed_activity": r["record"]["proposed_activity"],
                "facilitator_member_id": r["record"]["facilitator_member_id"],
                "minutes": r["record"]["minutes"],
                "preparation_state": r["preparation_state"],
            }
            for r in safe_education
        ],
        "followups": [
            {
                "followup_id": r["record"]["followup_id"],
                "description": r["record"]["description"],
                "owner_member_id": r["record"]["owner_member_id"],
                "due_on": r["record"]["due_on"],
                "draft_state": r["draft_state"],
            }
            for r in safe_followups
        ],
    }
    audience_draft["draft_markdown"] = render(audience_draft)
    result["audience_draft"] = audience_draft
    return make_output(SKILL, doc, result, findings)


def render(view):
    lines = ["# Draft family discussion — " + view["family_id"], view["notice"], "", "## Discussion topics"]
    for row in view["topics"]:
        lines += [
            "",
            "### " + row["title"],
            row["question"],
            "Proposal: " + row["proposed_decision"],
            "Recorded process observation: " + row["process_observation"] + ". Legal authority not determined.",
        ]
        lines += ["- " + p["member_id"] + ": " + p["position"] + " — " + p["statement"] for p in row["positions"]]
    lines += ["", "## Succession discussion"]
    for row in view["succession"]:
        lines.append(
            "- "
            + row["role_label"]
            + " — candidate "
            + (row["candidate_member_id"] or "unknown")
            + "; proposed target "
            + (row["target_date"] or "unknown")
            + "; "
            + row["readiness"]
            + "; no appointment made."
        )
        lines.append(
            "  Role scope: "
            + row["role_scope"]
            + " Authority type: "
            + row["authority_type"]
            + "; legal authority not determined."
        )
        lines += ["  - " + c["description"] + ": " + c["observation"] for c in row["criteria"]]
    lines += ["", "## Education proposals"]
    for row in view["education"]:
        lines.append(
            "- "
            + row["learning_objective"]
            + ": "
            + row["proposed_activity"]
            + " ("
            + str(row["minutes"] if row["minutes"] is not None else "unknown")
            + " minutes)."
        )
    lines += ["", "## Follow-up drafts"]
    for row in view["followups"]:
        lines.append(
            "- "
            + row["description"]
            + " Owner: "
            + (row["owner_member_id"] or "unassigned")
            + "; due "
            + (row["due_on"] or "unknown")
            + "; "
            + row["draft_state"]
            + "."
        )
    return "\n".join(lines)


def validate_output(out):
    return validate_result(out, SKILL, build)
