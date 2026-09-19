from native_helpers import data, date, finding, pack, profile, refs, txt, unique, validate_with


def evaluate(doc):
    d = data(doc)
    f = []
    profile(doc, f)
    tasks = d.get("tasks", [])
    unique(tasks, "task_id")
    index = {t["task_id"]: t for t in tasks}
    if not tasks:
        finding(f, "task-gap", "Handling tasks have not been supplied")
    now = date(doc.get("as_of"))
    visiting = set()
    done = set()

    def visit(tid):
        if tid in visiting:
            raise ValueError("task dependencies contain a cycle")
        if tid in done:
            return
        visiting.add(tid)
        for dep in index[tid].get("depends_on", []):
            if dep not in index:
                raise ValueError("unknown dependency " + dep)
            visit(dep)
        visiting.remove(tid)
        done.add(tid)

    for tid in index:
        visit(tid)
    queue = []
    for t in tasks:
        refs(doc, t, f, t["task_id"])
        state = t.get("state", "unknown")
        if state not in {"open", "in_progress", "complete", "waived", "unknown"}:
            raise ValueError("task state invalid")
        if not txt(t.get("owner")):
            finding(f, "owner-gap", t["task_id"] + ": accountable owner unknown")
        due = date(t.get("due_date"))
        if due is None:
            finding(f, "deadline-gap", t["task_id"] + ": supplied due date unknown")
        if t.get("deadline_basis") not in {"reviewed_rule_profile", "service_target"}:
            finding(f, "deadline-basis", t["task_id"] + ": deadline basis unreviewed")
        if state == "unknown":
            finding(f, "task-state", t["task_id"] + ": completion state unknown")
        if state in {"complete", "waived"} and not txt(t.get("completion_evidence")):
            finding(f, "completion-gap", t["task_id"] + ": completion/waiver evidence missing")
            state = "unknown"
        blocked = [
            dep
            for dep in t.get("depends_on", [])
            if index[dep].get("state") not in {"complete", "waived"} or not txt(index[dep].get("completion_evidence"))
        ]
        if blocked and state in {"complete", "waived"}:
            finding(
                f,
                "sequence-review",
                t["task_id"] + ": marked complete while dependencies remain open",
                t.get("source_refs", []),
                "review",
            )
        overdue = None if due is None else now > due and state not in {"complete", "waived"}
        if overdue:
            finding(
                f,
                "overdue",
                t["task_id"] + ": overdue; preserve claimant service urgency even if dependencies remain open",
                t.get("source_refs", []),
                "review",
            )
        queue.append(
            {
                **t,
                "effective_state": state,
                "blocked_by": blocked,
                "overdue": overdue,
                "ready_to_work": not blocked and state in {"open", "in_progress"},
            }
        )
    queue.sort(key=lambda t: (t["due_date"] if t.get("due_date") else "9999-12-31", t["task_id"]))
    return pack(
        {
            "task_queue": queue,
            "communications_sent": False,
            "deadlines_are": "supplied_profile_or_service_targets",
            "claim_resolution": "not_determined",
        },
        f,
    )


def validate(doc):
    return validate_with(evaluate, doc)
