"""Literal estate-intention/record comparison, never legal interpretation."""
from wealth_contract import make_output, validate_output_envelope, iso_date, nonempty
from workflow_support import base_errors, rows, texts, enum, number, dec, cited, add, base_findings, common_result

SKILL = "estate-wealth-transfer-reviewer"
KINDS = {"will", "trust", "power-of-attorney", "healthcare-directive", "other"}
TIERS = {"primary", "contingent"}


def beneficiary_errors(value, path, errors, nullable=False):
    if value is None and nullable:
        return
    if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
        errors.append(f"{path} must be a list of beneficiary objects or explicit null where permitted")
        return
    seen = set()
    for row in value:
        if not nonempty(row.get("party_id")) or not enum(row.get("tier"), TIERS):
            errors.append(f"{path}: each beneficiary requires party_id and primary/contingent tier")
            continue
        key = (row["party_id"], row["tier"])
        if key in seen:
            errors.append(f"{path}: duplicate beneficiary in tier")
        seen.add(key)
        if row.get("share") is not None and not number(row["share"], 0, 1):
            errors.append(f"{path}: share must be a fraction from zero through one or null")


def validate(doc):
    errors = base_errors(doc)
    if errors:
        return errors
    p = doc["policy"]
    for key, allowed in (("required_document_kinds", KINDS), ("required_beneficiary_tiers", TIERS)):
        if not texts(p.get(key), True) or any(x not in allowed for x in p[key]):
            errors.append(f"policy.{key} must explicitly list supported unique values")
    for row in rows(doc, "parties", errors, "party_id"):
        if not nonempty(row.get("display_name")) or not nonempty(row.get("role")):
            errors.append("parties require masked display_name and role")
    for row in rows(doc, "documents", errors, "document_id"):
        if not enum(row.get("kind"), KINDS) or not enum(row.get("status"), {"current", "superseded", "unknown"}):
            errors.append("documents require supported kind and explicit status")
        if not nonempty(row.get("version")) or not nonempty(row.get("summary")):
            errors.append("documents require supplied version and summary")
        if row.get("executed_date") is not None and (iso_date(row["executed_date"]) is None or row["executed_date"] > doc["as_of"]):
            errors.append("document executed_date must be historical ISO date or null")
    for row in rows(doc, "assets", errors, "asset_id"):
        if not nonempty(row.get("description")) or not enum(row.get("registration"), {"individual", "joint", "trust", "retirement", "insurance", "other"}):
            errors.append("assets require description and supported registration")
        if not texts(row.get("owner_party_ids"), True) or not texts(row.get("document_ids"), True):
            errors.append("asset owner_party_ids and document_ids must be explicit unique lists")
        if not enum(row.get("designation_status"), {"documented", "none-recorded", "unknown"}):
            errors.append("asset designation_status must be documented, none-recorded or unknown")
    for row in rows(doc, "intentions", errors, "intention_id"):
        if not nonempty(row.get("asset_id")) or not nonempty(row.get("description")):
            errors.append("intentions require asset_id and description")
        for key in ("target_owner_party_ids", "governing_document_ids"):
            if row.get(key) is not None and not texts(row[key], True):
                errors.append(f"intention {key} must be a unique list or null")
        beneficiary_errors(row.get("beneficiaries"), "intention beneficiaries", errors, True)
    for row in rows(doc, "designations", errors, "designation_id"):
        if not nonempty(row.get("asset_id")) or not enum(row.get("status"), {"current", "superseded", "unknown"}) or not texts(row.get("document_ids"), True):
            errors.append("designations require asset_id, explicit status and document_ids list")
        beneficiary_errors(row.get("beneficiaries"), "designation beneficiaries", errors)
    return errors


def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    findings = base_findings(doc)
    parties = {r["party_id"] for r in doc["parties"]}
    documents = {r["document_id"]: r for r in doc["documents"]}
    assets = {r["asset_id"]: r for r in doc["assets"]}
    if not assets:
        add(findings, "missing-assets", "No asset inventory supplied for estate coordination", "assets")
    for group in ("parties", "documents", "assets", "intentions", "designations"):
        for i, row in enumerate(doc[group]):
            path = f"{group}[{i}]"
            cited(row, doc, findings, path)
            if group in {"intentions", "designations"} and row["asset_id"] not in assets:
                add(findings, "unknown-asset", "Asset reference does not resolve", path)
            owner_ids = row.get("owner_party_ids", row.get("target_owner_party_ids"))
            if owner_ids is not None:
                for pid in owner_ids:
                    if pid not in parties:
                        add(findings, "unknown-party", f"Party reference {pid} does not resolve", path)
            for did in row.get("document_ids", row.get("governing_document_ids")) or []:
                record = documents.get(did)
                if record is None or record["status"] != "current":
                    add(findings, "document-gap", f"Referenced document {did} is missing or not recorded current", path)
            for b in row.get("beneficiaries") or []:
                cited(b, doc, findings, path + ".beneficiaries")
                if b["party_id"] not in parties:
                    add(findings, "unknown-party", "Beneficiary party does not resolve", path)
                if b.get("share") is None:
                    add(findings, "unknown-share", "Beneficiary share is unknown", path)
            beneficiaries = row.get("beneficiaries")
            if beneficiaries is not None:
                for tier in sorted(TIERS):
                    selected = [b for b in beneficiaries if b["tier"] == tier]
                    if selected and all(b.get("share") is not None for b in selected):
                        if sum(dec(b["share"]) for b in selected) != 1:
                            add(findings, "allocation-total", f"{tier} beneficiary shares do not total 100 percent", path)
                    if group == "designations" and row["status"] == "current" and tier in doc["policy"]["required_beneficiary_tiers"] and not selected:
                        add(findings, "missing-beneficiary-tier", f"Policy requires review of absent {tier} designation", path)
    for kind in doc["policy"]["required_document_kinds"]:
        matches = [d for d in doc["documents"] if d["kind"] == kind and d["status"] == "current"]
        if not matches:
            add(findings, "missing-document-kind", f"No current {kind} record supplied under review policy", "documents")
    for d in doc["documents"]:
        if d["status"] == "unknown" or d.get("executed_date") is None:
            add(findings, "document-status-gap", "Confirm document date and recorded status with counsel; no validity inference", "documents", document_id=d["document_id"])
    comparisons = []
    for aid, asset in assets.items():
        intents = [r for r in doc["intentions"] if r["asset_id"] == aid]
        records = [r for r in doc["designations"] if r["asset_id"] == aid and r["status"] != "superseded"]
        start = len(findings)
        if not asset["owner_party_ids"]:
            add(findings, "ownership-gap", "Recorded owners are unknown", aid)
        if len(intents) != 1:
            add(findings, "intention-gap", "Exactly one consolidated intention per asset is required; conflicting versions remain unresolved", aid)
        if asset["designation_status"] == "unknown" or (asset["designation_status"] == "documented" and not records):
            add(findings, "designation-gap", "Recorded beneficiary evidence is unavailable", aid)
        if len(records) > 1 or any(r["status"] != "current" for r in records):
            add(findings, "designation-conflict", "Multiple or unknown-status designations require owner reconciliation", aid)
        if asset["designation_status"] == "none-recorded" and records:
            add(findings, "designation-status-conflict", "None-recorded assertion conflicts with supplied designations", aid)
        differences = []
        if len(intents) == 1:
            intent = intents[0]
            wanted = intent.get("target_owner_party_ids")
            if wanted is None:
                add(findings, "owner-intention-unknown", "Intended titling not collected", aid)
            if wanted is not None and set(wanted) != set(asset["owner_party_ids"]):
                differences.append("intended owners differ from recorded owners")
            target_docs = intent.get("governing_document_ids")
            if target_docs is None:
                add(findings, "document-intention-unknown", "Intended governing-document links not collected", aid)
            if target_docs is not None and set(target_docs) != set(asset["document_ids"]):
                differences.append("intended document links differ from recorded asset document links")
            wanted_b = intent.get("beneficiaries")
            if wanted_b is None:
                add(findings, "beneficiary-intention-unknown", "Beneficiary intention not collected; no inference from current records", aid)
            elif len(records) <= 1 and all(r["status"] == "current" for r in records):
                actual = records[0]["beneficiaries"] if records else []
                signature = lambda bs: sorted((b["tier"], b["party_id"], str(dec(b["share"]).normalize()) if b.get("share") is not None else "unknown") for b in bs)
                if signature(wanted_b) != signature(actual):
                    differences.append("intended beneficiaries or shares differ from recorded designations")
            for text in differences:
                add(findings, "coordination-difference", text + "; counsel/custodian confirmation required", aid,
                    source_ids=sorted({sid for rec in [asset, intent] + records for sid in (rec.get("source_ids") if isinstance(rec.get("source_ids"), list) else []) if isinstance(sid, str)}))
        comparisons.append({"asset_id": aid, "asset": asset, "intentions": intents, "recorded_designations": records,
                            "literal_differences": differences, "asset_review_questions": findings[start:],
                            "legal_effect": "not-determined"})
    result = common_result(doc)
    result.update(parties=doc["parties"], documents=doc["documents"], asset_comparisons=comparisons,
                  review_summary={"assets_reviewed": len(assets), "coordination_differences": sum(len(r["literal_differences"]) for r in comparisons),
                                  "open_items": len(findings)},
                  specialist_questions=[{"owner": "estate counsel / custodian / advisor", "question": f["message"], "path": f["path"]} for f in findings],
                  limitations=["Literal evidence comparison only; no determination of enforceability, inheritance, probate, tax or document precedence.",
                               "No legal drafting, beneficiary update, ownership change or transfer instruction."])
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    errors = validate_output_envelope(out, SKILL)
    snapshot = out.get("result", {}).get("input_snapshot") if isinstance(out, dict) and isinstance(out.get("result"), dict) else None
    try:
        expected = build(snapshot)
        if out != expected:
            errors.append("output differs from full reconstruction of source snapshot, identities, comparisons or findings")
    except (ValueError, TypeError, KeyError) as exc:
        errors.append(f"invalid input snapshot: {exc}")
    return errors
