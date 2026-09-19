#!/usr/bin/env python3
"""Freeze, prepare, validate and summarize retained P4 model-evaluation artifacts.

Standard library only. This tool never calls a model or scores semantic quality.
"""

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import zipfile
from contextlib import contextmanager

VERSION = "wealth-p4-v1"
ROUTER = "wealth-management-router"
CONDITIONS = ("with-skill", "without-skill")
ROOT = Path(__file__).resolve().parents[1]
TOOL_POLICY = {
    "policy_id": "local-draft-v1",
    "description": "Read supplied local files; use local Python/calculation and local draft files. No network, external actions or access outside the isolated condition working directory. The same tool affordances apply to both conditions.",
}
LIMITATIONS = [
    "Artifact validity is not semantic correctness, source authenticity, professional approval or production certification.",
    "Scores are attributed independent-review judgments; the harness checks coverage and citations, never keyword-based semantic correctness.",
    "Small purposive paired cases are descriptive. Do not claim statistical significance, generalization or causal skill uplift.",
    "Model identity, isolation and tool-use declarations require retained runtime evidence; the harness cannot authenticate an external runtime.",
    "First-pass and revised results remain separate. Failed, missing and unassessed observations are never passes.",
]


class ContractError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise ContractError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def object_(value, label):
    need(isinstance(value, dict), label + " must be an object")
    return value


def list_(value, label, nonempty=False):
    need(isinstance(value, list), label + " must be a list")
    need(not nonempty or bool(value), label + " must not be empty")
    return value


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}", value) is not None


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def hash_object(value):
    return digest(canonical(value))


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def timestamp(value, label):
    need(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", value), label + " must be an explicit UTC timestamp ending Z")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(label + " is not a valid timestamp") from exc


def load(path):
    try:
        return json.loads(Path(path).read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ContractError(f"Cannot read JSON {path}: {exc}") from exc


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def safe_path(base, relative, must_exist=True):
    need(text(relative), "Artifact path must be nonempty text")
    rel = PurePosixPath(relative)
    need(not rel.is_absolute() and ".." not in rel.parts and "\\" not in relative, "Artifact path must remain relative to its retained root")
    path = Path(base).joinpath(*rel.parts)
    need(path.resolve().is_relative_to(Path(base).resolve()), "Artifact path escapes retained root")
    need(not any(parent.is_symlink() for parent in [path, *path.parents] if parent.is_relative_to(Path(base))), "Symlink artifacts are not permitted")
    if must_exist:
        need(path.is_file(), f"Missing artifact: {relative}")
    return path


def ref(base, relative):
    path = safe_path(base, relative)
    return {"path": relative, "sha256": digest(path.read_bytes())}


def check_ref(base, value, label="evidence"):
    object_(value, label)
    path = safe_path(base, value.get("path"))
    need(value.get("sha256") == digest(path.read_bytes()), label + " hash mismatch")
    return path


def check_refs(base, values, label, nonempty=True):
    for value in list_(values, label, nonempty):
        check_ref(base, value, label)


def seal(value, key):
    return {**value, key: hash_object(value)}


def check_seal(value, key):
    object_(value, "sealed artifact")
    need(value.get(key) == hash_object({k: v for k, v in value.items() if k != key}), key + " mismatch")


def operational(relative):
    parts = PurePosixPath(relative).parts
    name = parts[-1]
    return (relative == "SKILL.md" or parts[0] in {"references", "scripts", "assets"}) and not (
        "evals" in parts or "__pycache__" in parts or name.endswith(".pyc")
        or name.startswith("test_") or name.endswith("_test.py")
        or "regression" in name.lower() or name == ".DS_Store"
    )


def discover(repo, expected_count=27):
    router = Path(repo) / "skills/wealth-management" / ROUTER
    tree = ast.parse((router / "scripts/route.py").read_text())
    assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ROUTES" for t in n.targets)]
    need(len(assignments) == 1, "Cannot inventory the router's literal route map")
    routes = ast.literal_eval(assignments[0].value)
    targets = sorted({row[0] for row in routes.values()})
    need(len(targets) == expected_count, f"Expected {expected_count} practitioner packages; found {len(targets)}")
    result = {}
    for name in targets + [ROUTER]:
        matches = sorted((Path(repo) / "skills").glob(f"*/{name}/SKILL.md"))
        need(len(matches) == 1, "Missing or ambiguous skill: " + name)
        result[name] = matches[0].parent
    return result


def snapshot(repo, output, expected_count=27):
    output = Path(output)
    need(not output.exists(), "Snapshot destination already exists; choose a new immutable artifact directory")
    packages = discover(repo, expected_count)
    records = []
    for name, source in sorted(packages.items()):
        files = []
        for path in sorted(source.rglob("*")):
            need(not path.is_symlink(), "Package symlinks are not permitted in snapshot")
            if not path.is_file() or "__pycache__" in path.parts or path.name in {".DS_Store"} or path.suffix == ".pyc":
                continue
            relative = path.relative_to(source).as_posix()
            data = path.read_bytes()
            destination = output / "packages" / name / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            files.append({"path": relative, "sha256": digest(data), "bytes": len(data), "exposed": operational(relative)})
        need(any(f["path"] == "SKILL.md" for f in files), "Skill lacks SKILL.md")
        exposed = [f for f in files if f["exposed"]]
        records.append({"skill_id": name, "repository_path": source.relative_to(repo).as_posix(), "role": "router" if name == ROUTER else "practitioner", "package_sha256": hash_object(files), "operational_sha256": hash_object(exposed), "files": files})
    manifest = seal({"schema_version": VERSION, "kind": "snapshot", "created_at": now(), "practitioner_count": expected_count, "packages": records}, "snapshot_sha256")
    save(output / "snapshot.json", manifest)
    return manifest


def validate_snapshot(directory):
    manifest = load(Path(directory) / "snapshot.json")
    check_seal(manifest, "snapshot_sha256")
    need(manifest.get("schema_version") == VERSION and manifest.get("kind") == "snapshot", "Unsupported snapshot")
    timestamp(manifest.get("created_at"), "snapshot.created_at")
    packages = list_(manifest.get("packages"), "snapshot packages", True)
    names = []
    expected_paths = set()
    for package in packages:
        object_(package, "package")
        name = package.get("skill_id")
        need(identifier(name), "Invalid skill identifier")
        names.append(name)
        files = list_(package.get("files"), "package files", True)
        paths = []
        for file in files:
            object_(file, "package file")
            rel = file.get("path")
            need(text(rel), "Missing package file path")
            full = f"packages/{name}/{rel}"
            path = check_ref(directory, {"path": full, "sha256": file.get("sha256")}, "snapshot file")
            need(file.get("bytes") == path.stat().st_size and file.get("exposed") == operational(rel), "Snapshot size/exposure mismatch")
            paths.append(rel)
            expected_paths.add(full)
        need(len(paths) == len(set(paths)) and "SKILL.md" in paths, "Duplicate/missing SKILL package file")
        need(package.get("package_sha256") == hash_object(files), "Package digest mismatch")
        need(package.get("operational_sha256") == hash_object([f for f in files if f["exposed"]]), "Operational package digest mismatch")
    need(len(names) == len(set(names)) and ROUTER in names, "Duplicate package or absent router")
    need(sum(p.get("role") == "practitioner" for p in packages) == manifest.get("practitioner_count"), "Practitioner inventory mismatch")
    actual = {p.relative_to(directory).as_posix() for p in (Path(directory) / "packages").rglob("*") if p.is_file()}
    need(actual == expected_paths, "Snapshot has unlisted or missing package files")
    return manifest


def validate_case(case, rubric, skill_ids):
    object_(case, "case")
    object_(rubric, "rubric")
    need(case.get("schema_version") == VERSION and rubric.get("schema_version") == VERSION, "Unsupported case/rubric version")
    need(identifier(case.get("case_id")) and identifier(case.get("rubric_id")), "Invalid case/rubric identifiers")
    need(case["case_id"] == rubric.get("case_id") and case["rubric_id"] == rubric.get("rubric_id"), "Case/rubric identity mismatch")
    need(text(case.get("title")) and text(case.get("prompt")), "Case needs a title and substantive prompt")
    ids = list_(case.get("skill_ids"), "skill_ids", True)
    need(all(identifier(s) and s in skill_ids for s in ids) and len(ids) == len(set(ids)), "Unknown/duplicate case skill")
    conditions = list_(case.get("conditions"), "conditions", True)
    need(len(conditions) == 2 and set(conditions) == set(CONDITIONS), "Every case requires both conditions")
    sources = list_(case.get("source_packet"), "source_packet", True)
    seen = set()
    for source in sources:
        object_(source, "source packet item")
        sid = source.get("source_id")
        need(identifier(sid) and sid not in seen and text(source.get("content")), "Invalid/duplicate source packet entry")
        need(set(source) <= {"source_id", "content", "reference"}, "Unexpected source-packet fields; keep rubric material separate")
        if "reference" in source:
            need(text(source["reference"]), "Source reference must be text")
        seen.add(sid)
    need(set(case) <= {"schema_version", "case_id", "title", "skill_ids", "prompt", "source_packet", "conditions", "rubric_id"}, "Unexpected public-case fields; keep grader notes in rubric")
    items = list_(rubric.get("items"), "rubric items", True)
    ids = []
    for item in items:
        object_(item, "rubric item")
        need(identifier(item.get("item_id")) and text(item.get("criterion")) and text(item.get("required_evidence")), "Rubric item lacks identifier, criterion or required evidence")
        need(item.get("severity") in {"critical", "major", "minor"}, "Unsupported rubric severity")
        ids.append(item["item_id"])
    need(len(ids) == len(set(ids)), "Duplicate rubric item")


def model_template():
    return {"availability": "unknown", "provider": None, "model_id": None, "evidence_refs": []}


def render_prompt(case, condition):
    guidance = "\nAvailable skill packages are in ./skills/. Read the router and relevant SKILL.md instructions and supporting operational resources. Do not use selftests, missing evaluation fixtures or external files.\n" if condition == "with-skill" else "\nNo skill packages are supplied in this working directory.\n"
    return case["prompt"] + "\n\nUse the cited records in ./source_packet.json. Produce a useful draft for human review and cite source IDs. Preserve unknowns and distinguish supplied facts from assumptions.\n" + TOOL_POLICY["description"] + "\n" + guidance


def prepare(snapshot_dir, case_dir, rubric_dir, output, experiment_id):
    need(identifier(experiment_id), "Invalid experiment_id")
    output = Path(output)
    need(not output.exists(), "Experiment destination already exists; preparation never overwrites retained runs")
    frozen = validate_snapshot(snapshot_dir)
    by_skill = {p["skill_id"]: p for p in frozen["packages"]}
    pairs = []
    rubric_by_id = {}
    for path in sorted(Path(rubric_dir).glob("*.json")):
        rubric = load(path)
        object_(rubric, "rubric")
        rid = rubric.get("rubric_id")
        need(identifier(rid) and rid not in rubric_by_id, "Invalid or duplicate rubric ID")
        rubric_by_id[rid] = rubric
    for path in sorted(Path(case_dir).glob("*.json")):
        case = load(path)
        object_(case, "case")
        rubric = rubric_by_id.get(case.get("rubric_id"))
        validate_case(case, rubric, by_skill)
        pairs.append((case, rubric))
    need(pairs, "No evaluation cases supplied")
    need(len({c["case_id"] for c, _ in pairs}) == len(pairs), "Duplicate case ID")
    shutil.copytree(snapshot_dir, output / "frozen_snapshot")
    expected = []
    case_records = []
    for case, rubric in pairs:
        cid = case["case_id"]
        save(output / "hidden" / "cases" / (cid + ".json"), case)
        save(output / "hidden" / "rubrics" / (cid + ".json"), rubric)
        case_records.append({"case_id": cid, "case": ref(output, f"hidden/cases/{cid}.json"), "rubric": ref(output, f"hidden/rubrics/{cid}.json")})
        for condition in CONDITIONS:
            run_id = cid + "--" + condition
            packet_relative = "conditions/" + run_id
            packet = output / packet_relative
            packet.mkdir(parents=True)
            save(packet / "source_packet.json", case["source_packet"])
            selected = sorted(set(case["skill_ids"]) | {ROUTER}) if condition == "with-skill" else []
            for sid in selected:
                for file in by_skill[sid]["files"]:
                    if file["exposed"]:
                        target = packet / "skills" / sid / file["path"]
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(Path(snapshot_dir) / "packages" / sid / file["path"], target)
            prompt = render_prompt(case, condition)
            (packet / "prompt.txt").write_text(prompt)
            exposed_files = [ref(output, p.relative_to(output).as_posix()) for p in sorted(packet.rglob("*")) if p.is_file()]
            skills = {sid: by_skill[sid]["operational_sha256"] for sid in selected}
            bindings = {"case_sha256": hash_object(case), "case_prompt_sha256": digest(case["prompt"].encode()), "prompt_sha256": digest(prompt.encode()), "source_packet_sha256": digest((packet / "source_packet.json").read_bytes()), "rubric_sha256": hash_object(rubric), "skill_hashes": skills, "skill_manifest_sha256": hash_object(skills), "snapshot_sha256": frozen["snapshot_sha256"]}
            expected.append({"run_id": run_id, "case_id": cid, "condition": condition, "packet_dir": packet_relative, "record_path": "runs/" + run_id + ".json", "bindings": bindings, "exposed_files": exposed_files})
    manifest = seal({"schema_version": VERSION, "kind": "experiment", "experiment_id": experiment_id, "created_at": now(), "snapshot_sha256": frozen["snapshot_sha256"], "tool_policy": TOOL_POLICY, "cases": case_records, "expected_runs": expected, "limitations": LIMITATIONS}, "manifest_sha256")
    save(output / "manifest.json", manifest)
    for run in expected:
        save(output / run["record_path"], {"schema_version": VERSION, "run_id": run["run_id"], "manifest_sha256": manifest["manifest_sha256"], "bindings": run["bindings"], "generator": {"identity": None, "model": model_template()}, "execution": {"status": "missing", "started_at": None, "ended_at": None, "isolation": {"fresh_context": None, "isolated_workdir": None, "hidden_rubric_unavailable": None, "tool_policy_matched": None}, "evidence_refs": []}, "attempts": []})
    (output / "reviews").mkdir()
    return manifest


def validate_prepared(directory):
    directory = Path(directory)
    manifest = load(directory / "manifest.json")
    check_seal(manifest, "manifest_sha256")
    need(manifest.get("schema_version") == VERSION and manifest.get("kind") == "experiment", "Unsupported experiment")
    frozen = validate_snapshot(directory / "frozen_snapshot")
    need(manifest.get("snapshot_sha256") == frozen["snapshot_sha256"], "Experiment snapshot mismatch")
    need(timestamp(frozen["created_at"], "snapshot.created_at") <= timestamp(manifest.get("created_at"), "manifest.created_at"), "Experiment freeze cannot predate its skill snapshot")
    need(manifest.get("tool_policy") == TOOL_POLICY, "Tool policy differs from prepared contract")
    by_skill = {p["skill_id"]: p for p in frozen["packages"]}
    cases = {}
    for record in list_(manifest.get("cases"), "manifest cases", True):
        case = load(check_ref(directory, record.get("case"), "case"))
        rubric = load(check_ref(directory, record.get("rubric"), "rubric"))
        validate_case(case, rubric, by_skill)
        need(record.get("case_id") == case["case_id"] and case["case_id"] not in cases, "Case identity mismatch")
        cases[case["case_id"]] = (case, rubric)
    runs = list_(manifest.get("expected_runs"), "expected runs", True)
    need({r.get("run_id") for r in runs} == {cid + "--" + cond for cid in cases for cond in CONDITIONS} and len(runs) == 2 * len(cases), "Expected run set is incomplete or duplicated")
    for run in runs:
        case, rubric = cases[run["case_id"]]
        condition = run.get("condition")
        need(condition in CONDITIONS and run["run_id"] == case["case_id"] + "--" + condition, "Run identity/condition mismatch")
        selected = sorted(set(case["skill_ids"]) | {ROUTER}) if condition == "with-skill" else []
        skills = {sid: by_skill[sid]["operational_sha256"] for sid in selected}
        packet = directory / "conditions" / run["run_id"]
        need(run.get("packet_dir") == packet.relative_to(directory).as_posix() and run.get("record_path") == "runs/" + run["run_id"] + ".json", "Run artifact path mismatch")
        exposed = list_(run.get("exposed_files"), "exposed files", True)
        actual = {p.relative_to(directory).as_posix() for p in packet.rglob("*") if p.is_file()}
        expected = {f["path"] for f in exposed}
        need(actual == expected and len(expected) == len(exposed), "Condition directory has extra/missing files; run a separate copy and retain outputs outside the frozen packet")
        allowed = {f"{run['packet_dir']}/prompt.txt", f"{run['packet_dir']}/source_packet.json"}
        allowed |= {f"{run['packet_dir']}/skills/{sid}/{f['path']}" for sid in selected for f in by_skill[sid]["files"] if f["exposed"]}
        need(expected == allowed, "Exposure inventory includes disallowed or missing resources")
        for file in exposed:
            check_ref(directory, file, "exposed file")
        for sid in selected:
            for file in by_skill[sid]["files"]:
                if file["exposed"]:
                    need(digest((packet / "skills" / sid / file["path"]).read_bytes()) == file["sha256"], "Exposed skill differs from snapshot")
        need(load(packet / "source_packet.json") == case["source_packet"], "Source packet differs across prepared case")
        need((packet / "prompt.txt").read_text() == render_prompt(case, condition), "Prompt differs from reproducible preparation recipe")
        bindings = {"case_sha256": hash_object(case), "case_prompt_sha256": digest(case["prompt"].encode()), "prompt_sha256": digest((packet / "prompt.txt").read_bytes()), "source_packet_sha256": digest((packet / "source_packet.json").read_bytes()), "rubric_sha256": hash_object(rubric), "skill_hashes": skills, "skill_manifest_sha256": hash_object(skills), "snapshot_sha256": frozen["snapshot_sha256"]}
        need(run.get("bindings") == bindings, "Prepared input/skill binding mismatch")
    return manifest, cases


def validate_model(directory, model):
    object_(model, "model")
    need(model.get("availability") in {"known", "unknown"}, "Model identity availability must be known or unknown")
    if model["availability"] == "known":
        need(text(model.get("provider")) and text(model.get("model_id")), "Known model identity requires provider and model_id")
        check_refs(directory, model.get("evidence_refs"), "model identity evidence")
    else:
        need(model.get("provider") is None and model.get("model_id") is None, "Unknown model identity cannot include inferred names")
        check_refs(directory, model.get("evidence_refs"), "model identity evidence", False)


def validate_run(directory, run, expected, manifest):
    object_(run, "run")
    need(run.get("schema_version") == VERSION and run.get("run_id") == expected["run_id"], "Run identity/version mismatch")
    need(run.get("manifest_sha256") == manifest["manifest_sha256"] and run.get("bindings") == expected["bindings"], "Run does not bind exact prepared inputs")
    execution = object_(run.get("execution"), "execution")
    status = execution.get("status")
    need(status in {"missing", "failed", "completed"}, "Execution status must be missing, failed or completed")
    attempts = list_(run.get("attempts"), "attempts")
    generator = object_(run.get("generator"), "generator")
    validate_model(directory, generator.get("model"))
    if "requested_model" in generator:
        requested = object_(generator["requested_model"], "requested model")
        need(text(requested.get("provider")) and text(requested.get("model_id")), "Requested model metadata needs provider and model_id; this is not reported backend identity")
    if status == "missing":
        need(not attempts and execution.get("started_at") is None and execution.get("ended_at") is None, "Missing run cannot contain attempts or execution timestamps")
        return []
    need(text(generator.get("identity")), "Executed run needs a generator identity")
    started = timestamp(execution.get("started_at"), "execution.started_at")
    ended = timestamp(execution.get("ended_at"), "execution.ended_at")
    need(timestamp(manifest["created_at"], "manifest.created_at") <= started <= ended, "Execution timestamps out of order or before case/rubric freeze")
    isolation = object_(execution.get("isolation"), "isolation")
    for key in ("fresh_context", "isolated_workdir", "hidden_rubric_unavailable", "tool_policy_matched"):
        need(type(isolation.get(key)) is bool, "Executed run needs explicit isolation declaration: " + key)
    check_refs(directory, execution.get("evidence_refs"), "execution evidence")
    if status == "completed":
        need(bool(attempts), "Completed execution needs a first-pass attempt")
    ids = []
    previous_end = started
    for index, attempt in enumerate(attempts):
        object_(attempt, "attempt")
        aid = attempt.get("attempt_id")
        need(identifier(aid) and aid not in ids, "Invalid or duplicate attempt ID")
        stage = attempt.get("stage")
        need(stage == ("first-pass" if index == 0 else "revised"), "First retained attempt must be first-pass; later attempts are revised")
        need(attempt.get("parent_attempt_id") == (None if index == 0 else ids[-1]), "Attempt parent must preserve ordered repair lineage")
        ids.append(aid)
        astart = timestamp(attempt.get("started_at"), "attempt.started_at")
        aend = timestamp(attempt.get("ended_at"), "attempt.ended_at")
        need(previous_end <= astart <= aend <= ended, "Attempt timestamps outside execution or prior attempt")
        previous_end = aend
        need(attempt.get("status") in {"completed", "failed"}, "Attempt status must be completed or failed")
        response = attempt.get("response")
        if response is not None:
            path = check_ref(directory, response, "response")
            need(text(path.read_text()), "Retained response must not be empty")
        need(attempt["status"] != "completed" or response is not None, "Completed attempt needs retained response")
        if "generated_artifacts" in attempt:
            generated = list_(attempt["generated_artifacts"], "generated artifacts")
            check_refs(directory, generated, "generated artifact", False)
            need(len({g["path"] for g in generated}) == len(generated), "Duplicate generated artifact path")
        check_refs(directory, attempt.get("evidence_refs"), "attempt/runtime evidence")
        tools = object_(attempt.get("tool_usage"), "tool usage")
        need(tools.get("status") in {"used", "none", "unknown"}, "Tool usage must be explicit")
        events = list_(tools.get("events"), "tool events")
        need((tools["status"] == "used") == bool(events), "Used tools require retained events; none/unknown cannot carry events")
        for event in events:
            object_(event, "tool event")
            need(text(event.get("tool")) and text(event.get("description")) and event.get("status") in {"succeeded", "failed"}, "Tool event needs tool, description and status")
            tstart = timestamp(event.get("started_at"), "tool.started_at")
            tend = timestamp(event.get("ended_at"), "tool.ended_at")
            need(astart <= tstart <= tend <= aend, "Tool event outside attempt timestamps")
            check_refs(directory, event.get("evidence_refs"), "tool evidence")
        repair = attempt.get("repair")
        if index == 0:
            need(repair is None, "First-pass cannot include a repair record")
        else:
            object_(repair, "repair")
            need(text(repair.get("reason")) and text(repair.get("requested_by")), "Revision needs repair reason and requester")
            check_refs(directory, repair.get("evidence_refs"), "repair evidence")
    need(status != "completed" or any(a["status"] == "completed" for a in attempts), "Completed execution contains no completed attempt")
    return attempts


def validate_review(directory, review, run, attempt, rubric, case, manifest):
    object_(review, "review")
    need(review.get("schema_version") == VERSION and review.get("run_id") == run["run_id"] and review.get("attempt_id") == attempt["attempt_id"], "Review identity mismatch")
    need(attempt["status"] == "completed", "Failed attempts cannot receive a passing semantic review")
    bindings = {"manifest_sha256": manifest["manifest_sha256"], "response_sha256": attempt["response"]["sha256"], "rubric_sha256": hash_object(rubric)}
    if "generated_artifacts" in attempt:
        bindings["generated_artifacts_sha256"] = hash_object(attempt["generated_artifacts"])
    need(review.get("bindings") == bindings, "Review is not bound to response, generated artifacts and hidden rubric")
    reviewer = object_(review.get("reviewer"), "reviewer")
    need(text(reviewer.get("identity")) and reviewer["identity"] != run["generator"]["identity"], "Reviewer must be identified independently from generator")
    need(reviewer.get("kind") in {"human", "model"} and reviewer.get("independent_from_generation") is True, "Review requires an explicit independent-review declaration")
    check_refs(directory, review.get("evidence_refs"), "review evidence")
    need(timestamp(review.get("reviewed_at"), "reviewed_at") >= timestamp(attempt["ended_at"], "attempt ended_at"), "Review cannot predate response")
    scores = list_(review.get("items"), "review items", True)
    by_id = {item["item_id"]: item for item in rubric["items"]}
    need(all(isinstance(s, dict) for s in scores), "Review items must be objects")
    need(len(scores) == len(by_id) and {s.get("item_id") for s in scores} == set(by_id), "Review must explicitly cover every rubric item exactly once")
    response = check_ref(directory, attempt["response"]).read_text()
    generated = {g["path"]: g for g in attempt.get("generated_artifacts", [])}
    source_records = {s["source_id"]: s for s in case["source_packet"]}
    for score in scores:
        verdict = score.get("verdict")
        need(verdict in {"pass", "fail", "not-assessed"} and text(score.get("rationale")), "Each score needs verdict and substantive review rationale")
        citations = list_(score.get("evidence"), "score evidence", verdict != "not-assessed")
        response_cited = False
        for citation in citations:
            object_(citation, "citation")
            artifact = citation.get("artifact")
            need(artifact in {"response", "generated", "source"}, "Citation artifact must be response, generated or source")
            if artifact == "response":
                content = response
                response_cited = True
            elif artifact == "generated":
                need(citation.get("path") in generated, "Citation path is not a retained generated artifact")
                content = check_ref(directory, generated[citation["path"]]).read_text()
                response_cited = True
            else:
                need(citation.get("source_id") in source_records, "Unknown citation source")
                field = citation.get("source_field", "content")
                need(field in {"content", "reference"}, "Source citation field must be content or reference")
                content = source_records[citation["source_id"]].get(field)
                need(text(content), "Cited source field is absent or empty")
            start, end = citation.get("line_start"), citation.get("line_end")
            lines = content.splitlines()
            need(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines), "Citation line span is invalid")
            need(text(citation.get("quote")) and citation["quote"] in "\n".join(lines[start - 1:end]), "Citation quote is absent from claimed lines")
        need(verdict == "not-assessed" or response_cited, "Assessed scores need response/generated-deliverable evidence; missing content may cite the complete answer with an absence rationale")
    verdicts = [s["verdict"] for s in scores]
    verdict = "fail" if "fail" in verdicts else "not-assessed" if "not-assessed" in verdicts else "pass"
    return {"status": verdict, "item_counts": dict(Counter(verdicts)), "critical_failures": [s["item_id"] for s in scores if s["verdict"] == "fail" and by_id[s["item_id"]]["severity"] == "critical"]}


def report(directory):
    directory = Path(directory)
    manifest, cases = validate_prepared(directory)
    records, errors = [], []
    known_review_paths = set()
    for expected in manifest["expected_runs"]:
        rid = expected["run_id"]
        row = {"run_id": rid, "case_id": expected["case_id"], "condition": expected["condition"], "first_pass": {"status": "missing"}, "revised": [], "model_identity": "unknown", "reported_model": None, "requested_model": None, "comparison_eligible": False}
        records.append(row)
        path = directory / expected["record_path"]
        if not path.exists():
            continue
        try:
            run = load(path)
            attempts = validate_run(directory, run, expected, manifest)
            row["model_identity"] = run["generator"]["model"]["availability"]
            row["reported_model"] = {key: run["generator"]["model"][key] for key in ("provider", "model_id")}
            row["requested_model"] = run["generator"].get("requested_model")
            row["execution_status"] = run["execution"]["status"]
            row["comparison_eligible"] = run["execution"]["status"] == "completed" and all(run["execution"]["isolation"].get(k) is True for k in ("fresh_context", "isolated_workdir", "hidden_rubric_unavailable", "tool_policy_matched")) and row["model_identity"] == "known" and all(a["tool_usage"]["status"] != "unknown" for a in attempts)
            if not attempts:
                row["first_pass"]["status"] = run["execution"]["status"]
            case, rubric = cases[expected["case_id"]]
            for attempt in attempts:
                item = {"attempt_id": attempt["attempt_id"], "status": "failed" if attempt["status"] == "failed" else "unreviewed"}
                review_relative = f"reviews/{rid}--{attempt['attempt_id']}.json"
                known_review_paths.add(review_relative)
                review_path = directory / review_relative
                if review_path.exists():
                    try:
                        item.update(validate_review(directory, load(review_path), run, attempt, rubric, case, manifest))
                    except (ContractError, KeyError, TypeError, UnicodeError, OSError, ValueError) as exc:
                        item["status"] = "invalid"
                        errors.append({"run_id": rid, "attempt_id": attempt["attempt_id"], "error": str(exc)})
                if run["execution"]["status"] == "failed" and item["status"] != "invalid":
                    item["review_status"] = item["status"]
                    item["status"] = "failed"
                if attempt["stage"] == "first-pass":
                    row["first_pass"] = item
                else:
                    row["revised"].append(item)
        except (ContractError, KeyError, TypeError, UnicodeError, OSError, ValueError) as exc:
            row["first_pass"]["status"] = "invalid"
            errors.append({"run_id": rid, "error": str(exc)})
    extra_runs = {p.relative_to(directory).as_posix() for p in (directory / "runs").glob("*.json")} - {r["record_path"] for r in manifest["expected_runs"]}
    extra_reviews = {p.relative_to(directory).as_posix() for p in (directory / "reviews").glob("*.json")} - known_review_paths
    for path in sorted(extra_runs | extra_reviews):
        errors.append({"error": "Unmapped retained run/review artifact: " + path})
    counts = {}
    for condition in CONDITIONS:
        subset = [r for r in records if r["condition"] == condition]
        first = Counter(r["first_pass"]["status"] for r in subset)
        revised = Counter(a["status"] for r in subset for a in r["revised"])
        expected_items = sum(len(cases[r["case_id"]][1]["items"]) for r in subset)
        item_counts = Counter()
        for row in subset:
            if row["first_pass"]["status"] in {"pass", "fail", "not-assessed"}:
                item_counts.update(row["first_pass"].get("item_counts", {}))
        counts[condition] = {"expected_runs": len(subset), "first_pass": {k: first[k] for k in ("missing", "failed", "invalid", "unreviewed", "not-assessed", "pass", "fail")}, "first_pass_rubric_items": {"expected": expected_items, **{k: item_counts[k] for k in ("pass", "fail", "not-assessed")}, "unreviewed_or_unusable": expected_items - sum(item_counts.values())}, "revised_attempts": sum(revised.values()), "revised": dict(revised), "known_model_runs": sum(r["model_identity"] == "known" for r in subset), "comparison_eligible_runs": sum(r["comparison_eligible"] for r in subset)}
    skills = sorted({sid for case, _ in cases.values() for sid in case["skill_ids"] if sid != ROUTER})
    inventory = validate_snapshot(directory / "frozen_snapshot")
    all_skills = {p["skill_id"] for p in inventory["packages"] if p["role"] == "practitioner"}
    pairs = []
    for cid in cases:
        matching = {r["condition"]: r for r in records if r["case_id"] == cid}
        left, right = (matching[c] for c in CONDITIONS)
        pairs.append({"case_id": cid, **{c: matching[c]["first_pass"]["status"] for c in CONDITIONS}, "metadata_comparable": all(r["comparison_eligible"] for r in matching.values()) and left["reported_model"] == right["reported_model"] and left["requested_model"] == right["requested_model"]})
    first = [r["first_pass"]["status"] for r in records]
    complete = all(status in {"pass", "fail"} for status in first) and not errors
    return {"schema_version": VERSION, "experiment_id": manifest["experiment_id"], "manifest_sha256": manifest["manifest_sha256"], "artifact_status": "invalid" if errors else "complete-reviewed" if complete else "incomplete", "expected_runs": len(records), "case_count": len(cases), "coverage": {"practitioner_inventory": len(all_skills), "case_targeted_practitioners": len(skills), "case_targeted_skill_ids": skills, "not_case_targeted_skill_ids": sorted(all_skills - set(skills)), "routing_exposure_does_not_establish_task_quality": True}, "conditions": counts, "paired_first_pass_observations": pairs, "runs": records, "errors": errors, "limitations": LIMITATIONS}


def markdown(summary):
    lines = ["# Wealth P4 retained-artifact report", "", f"Experiment: {summary['experiment_id']}", f"Artifact status: {summary['artifact_status']}", f"Expected runs: {summary['expected_runs']} across {summary['case_count']} cases.", "", "| Condition | Expected | Pass | Fail | Missing | Failed run | Invalid | Unreviewed | Not assessed |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for condition, row in summary["conditions"].items():
        c = row["first_pass"]
        lines.append(f"| {condition} | {row['expected_runs']} | {c['pass']} | {c['fail']} | {c['missing']} | {c['failed']} | {c['invalid']} | {c['unreviewed']} | {c['not-assessed']} |")
    lines += ["", "First-pass only above; revised attempts are retained separately:"]
    for condition, row in summary["conditions"].items():
        lines.append(f"- {condition}: {row['revised_attempts']} revised attempts; {json.dumps(row['revised'], sort_keys=True)}. Known model identity {row['known_model_runs']}/{row['expected_runs']}; metadata-comparable {row['comparison_eligible_runs']}/{row['expected_runs']}.")
        lines.append(f"  First-pass rubric-item denominator: {json.dumps(row['first_pass_rubric_items'], sort_keys=True)}.")
    coverage = summary["coverage"]
    lines += ["", f"Case-targeted practitioner coverage: {coverage['case_targeted_practitioners']}/{coverage['practitioner_inventory']}. Exposure to the router is not evidence of performance on every route.", "", "Limitations:"]
    lines += ["- " + value for value in summary["limitations"]]
    if summary["errors"]:
        lines += ["", "Artifact errors:"] + ["- " + json.dumps(e, sort_keys=True) for e in summary["errors"]]
    return "\n".join(lines) + "\n"


@contextmanager
def artifact_directory(path):
    """Read a directory or a ZIP made with its contents at the archive root."""
    path = Path(path)
    if path.is_dir():
        yield path
        return
    need(path.is_file() and zipfile.is_zipfile(path), "Artifact must be a directory or ZIP archive")
    with tempfile.TemporaryDirectory(prefix="wealth-p4-artifact-") as temporary:
        target = Path(temporary)
        with zipfile.ZipFile(path) as archive:
            files = archive.infolist()
            need(len(files) <= 30000 and sum(f.file_size for f in files) <= 256 * 1024 * 1024, "Archive exceeds bounded artifact size")
            need(len({f.filename for f in files}) == len(files), "Archive contains duplicate paths")
            for member in files:
                safe_path(target, member.filename, must_exist=False)
                need((member.external_attr >> 16) & 0o170000 != 0o120000, "Archive symlinks are not permitted")
            archive.extractall(target)
        yield target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("--repo", type=Path, default=ROOT)
    snap.add_argument("--out", type=Path, required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--snapshot", type=Path, required=True)
    prep.add_argument("--cases", type=Path, default=ROOT / "docs/wealth-management/p4/cases")
    prep.add_argument("--rubrics", type=Path, default=ROOT / "docs/wealth-management/p4/rubrics")
    prep.add_argument("--out", type=Path, required=True)
    prep.add_argument("--experiment-id", required=True)
    val = sub.add_parser("validate")
    val.add_argument("experiment", type=Path)
    summ = sub.add_parser("summarize")
    summ.add_argument("experiment", type=Path)
    summ.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            result = snapshot(args.repo, args.out)
            print(json.dumps({"snapshot_sha256": result["snapshot_sha256"], "practitioner_count": result["practitioner_count"], "packages": len(result["packages"])}))
        elif args.command == "prepare":
            with artifact_directory(args.snapshot) as source:
                result = prepare(source, args.cases, args.rubrics, args.out, args.experiment_id)
            print(json.dumps({"manifest_sha256": result["manifest_sha256"], "cases": len(result["cases"]), "expected_runs": len(result["expected_runs"])}))
        else:
            with artifact_directory(args.experiment) as source:
                result = report(source)
            print(markdown(result) if args.command == "summarize" and args.format == "markdown" else json.dumps(result, indent=2))
            if args.command == "validate":
                return 1 if result["errors"] else 0
        return 0
    except (ContractError, KeyError, TypeError, OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"errors": [str(exc)], "artifact_status": "invalid"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
