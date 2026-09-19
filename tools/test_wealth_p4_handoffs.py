#!/usr/bin/env python3
"""P4 test-only, source-preserving adapters exercising five real CLI handoff chains.

These adapters implement only the explicit synthetic mappings in the paired fixtures.
They are not a production integration, an identity resolver, an authority decision,
or a real-model behavioral evaluation. Every computed artifact is output-validated
before consumption; no package-local modules are imported or cached.
"""

import copy
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "skills/wealth-management"
FIXTURES = ROOT / "tools/fixtures/wealth-p4-handoffs"
DATE = "2026-09-17"
HH = "P4-HH-MARIN"
DISCOVERY = "wealth-client-discovery-assistant"
RECON = "household-wealth-data-reconciler"
RISK = "investment-risk-profile-reviewer"
IPS = "investment-policy-statement-builder"
REVIEW = "client-review-preparer"
FOLLOWUP = "advisor-follow-up-assistant"
FAMILY = "family-wealth-governance-preparer"
TRUST = "trust-administration-reviewer"
SERVICE = "wealth-account-service-packager"
PRIVATE = "private-market-client-reviewer"
LENDING = "wealth-lending-liquidity-reviewer"
CONSTRUCTION = "portfolio-construction-assistant"
COMPARISON = "portfolio-proposal-comparator"
RECOMMENDATION = "investment-recommendation-evidence-reviewer"


def fixture(name):
    return json.loads((FIXTURES / (name + ".json")).read_text())


def snapshot(out):
    return out.get("input_snapshot", out.get("result", {}).get("input_snapshot"))


def artifact_source(out):
    return {
        "source_id": "artifact:" + out["artifact_id"],
        "reference": "generated-artifact:" + out["artifact_id"] + ":sha256:" + out["input_hash"],
        "owner": "Synthetic P4 adapter record steward",
        "as_of": out.get("as_of", out.get("as_of_date")),
        "valid_until": "2026-12-31",
    }


def merge_sources(target, rows):
    """Keep IDs unchanged; a conflicting same-ID record is an error, not an overwrite."""
    registry = {s["source_id"]: s for s in target["sources"]}
    for row in rows:
        old = registry.get(row["source_id"])
        if old is not None and old != row:
            raise ValueError("conflicting source identity: " + row["source_id"])
        registry[row["source_id"]] = copy.deepcopy(row)
    target["sources"] = list(registry.values())


def issue_key(issue):
    return issue["artifact_id"], issue["code"], issue["message"]


def issues_from(out):
    """Carry original issue identities; add artifact-local findings with explicit lineage.

    P0 findings often have no citation list. The adapter conservatively binds them to
    all original sources AND the generated artifact, without claiming finer attribution.
    """
    raw = snapshot(out) or {}
    inherited = out.get("result", {}).get("upstream_issues", raw.get("upstream_issues", [])) or []
    issues = {issue_key(x): copy.deepcopy(x) for x in inherited}
    for finding in out.get("findings", []):
        if finding["code"] == "upstream-unresolved":
            continue
        row = {
            "artifact_id": out["artifact_id"],
            "code": finding["code"],
            "message": finding["message"],
            "status": "unresolved",
            "source_ids": sorted(
                set(finding.get("source_ids") or [s["source_id"] for s in out["sources"]])
                | {artifact_source(out)["source_id"]}
            ),
        }
        # Context such as account/date/amount remains attributed, not reduced to prose.
        row["origin_context"] = {
            k: copy.deepcopy(v) for k, v in finding.items() if k not in {"code", "message", "source_ids"}
        }
        issues[issue_key(row)] = row
    return list(issues.values())


def import_common(target, upstream, expected_subject):
    if upstream.get("household_id") != expected_subject:
        raise ValueError("upstream subject does not match the reviewed handoff mapping")
    merge_sources(target, upstream["sources"] + [artifact_source(upstream)])
    combined = {issue_key(x): copy.deepcopy(x) for x in target.get("upstream_issues", [])}
    combined.update({issue_key(x): x for x in issues_from(upstream)})
    target["upstream_issues"] = list(combined.values())
    target.setdefault("handoff_inputs", []).append(
        {
            "artifact_id": upstream["artifact_id"],
            "input_hash": upstream["input_hash"],
            "upstream_household_id": expected_subject,
            "target_household_id": target["household_id"],
            "source_id_map": {s["source_id"]: s["source_id"] for s in upstream["sources"]},
            "action_taken": upstream["action_taken"],
            "human_review_required": upstream["human_review_required"],
            "delivery_status": upstream["delivery_status"],
        }
    )
    return artifact_source(upstream)["source_id"]


class WealthP4HandoffTests(unittest.TestCase):
    def cli(self, skill, script, value):
        with tempfile.TemporaryDirectory(prefix="wealth-p4-handoff-") as tmp:
            path = Path(tmp) / "input.json"
            path.write_text(json.dumps(value, allow_nan=False))
            run = subprocess.run(
                [sys.executable, "-B", str(PACKAGES / skill / "scripts" / script), str(path)],
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        self.assertFalse(run.stderr, run.stderr)
        return run.returncode, run.stdout

    def compute(self, skill, doc):
        code, raw = self.cli(skill, "calculate_or_transform.py", doc)
        self.assertEqual(code, 0, f"{skill}: {raw}")
        out = json.loads(raw)
        code, validation = self.cli(skill, "validate_output.py", out)
        self.assertEqual(code, 0, f"{skill}: {validation}")
        self.assertFalse(out["action_taken"])
        self.assertTrue(out["human_review_required"])
        self.assertEqual(out["delivery_status"], "not-delivered")
        self.assertEqual(snapshot(out), doc)
        return out

    def assert_common_edge(self, before, after, expected_subject=None):
        doc = snapshot(after)
        if expected_subject is None:
            self.assertEqual(after["household_id"], before["household_id"])
        expected_subject = expected_subject or before["household_id"]
        self.assertEqual(before["household_id"], expected_subject)
        self.assertEqual(after["household_id"], doc["household_id"])
        imports = {x["artifact_id"]: x for x in doc.get("handoff_inputs", [])}
        if imports:
            record = imports[before["artifact_id"]]
            self.assertEqual(record["input_hash"], before["input_hash"])
            self.assertEqual(record["upstream_household_id"], expected_subject)
            self.assertEqual(record["target_household_id"], after["household_id"])
            self.assertFalse(record["action_taken"])
            self.assertTrue(record["human_review_required"])
            self.assertEqual(record["delivery_status"], "not-delivered")
        else:
            # Trust rejects extra top-level adapter metadata. Its source registry carries
            # artifact ID/hash; identity mapping is checked before construction and below.
            self.assertEqual(after["household_id"], "trust:P4-TRUST")
            self.assertEqual(doc["beneficiaries"][0]["household_id"], "P4-HH-BEN")
        registry = {s["source_id"]: s for s in after["sources"]}
        for source in before["sources"] + [artifact_source(before)]:
            self.assertEqual(registry.get(source["source_id"]), source)
        wanted = {issue_key(x): x for x in issues_from(before)}
        actual = {issue_key(x): x for x in doc["upstream_issues"]}
        for key, issue in wanted.items():
            self.assertIn(key, actual)
            self.assertEqual(actual[key]["source_ids"], issue["source_ids"])
            if issue["status"] == "unresolved" and actual[key]["status"] == "resolved":
                self.assertTrue(actual[key].get("resolution"))
            else:
                self.assertEqual(actual[key]["status"], issue["status"])

    def assert_review_edge(self, ips, review):
        raw = snapshot(review)
        pack = review["reviews"][0]["review_pack"]
        self.assertEqual(pack["client_id"], ips["household_id"])
        self.assertEqual(review["prior_artifact_id"], ips["artifact_id"])
        self.assertEqual(raw["handoff_issue_register"], issues_from(ips))
        registry = {s["source_id"]: s for s in raw["reviews"][0]["sources"]}
        for source in ips["sources"] + [artifact_source(ips)]:
            projected = registry[source["source_id"]]
            self.assertEqual(projected["ref"], source["reference"])
            self.assertEqual(projected["date"], source["as_of"])
            self.assertEqual(projected["owner"], source["owner"])
            self.assertEqual(projected["valid_until"], source["valid_until"])
        actions = pack["open_actions"]
        for issue in issues_from(ips):
            self.assertTrue(
                any(
                    all(
                        token in action["action"]
                        for token in [
                            issue["artifact_id"],
                            issue["code"],
                            issue["message"],
                            "status=" + issue["status"],
                        ]
                    )
                    for action in actions
                )
            )

    def assert_followup_edge(self, review, follow):
        pack = review["reviews"][0]["review_pack"]
        raw = snapshot(follow)
        self.assertEqual(follow["client"]["household_id"], pack["client_id"])
        self.assertEqual(follow["prior_artifact_id"], review["artifact_id"])
        self.assertEqual(raw["handoff_issue_register"], snapshot(review)["handoff_issue_register"])
        registry = {s["citation"]: s for s in follow["source_inventory"]}
        for source in snapshot(review)["reviews"][0]["sources"]:
            citation = f"{source['system']}:{source['ref']}@{source['date']}"
            self.assertEqual(raw["review_citation_map"][source["source_id"]], citation)
            projected = registry[citation]
            self.assertEqual(projected["owner"], source["owner"])
            self.assertEqual(projected["as_of"], source["date"])
            self.assertEqual(projected["valid_until"], source["valid_until"])
        for action in pack["open_actions"]:
            if action["status"] != "open":
                continue
            kept = next((x for x in follow["action_items"] if x["description"] == action["action"]), None)
            self.assertIsNotNone(kept)
            for key in ["owner", "due_date", "citation"]:
                self.assertEqual(kept[key], action[key])
            self.assertIn(action["action"], follow["client_communication"]["body"])
            self.assertTrue(any(p["summary"] == action["action"] for p in follow["discussion_points"]))

    def discovery_to_recon(self, out, unconfirmed=False):
        mapping = fixture("account-mapping")
        if out["household_id"] != mapping["household_id"]:
            raise ValueError("discovery household conflicts with account mapping")
        facts = {x["area"]: x for x in out["result"]["facts"]}
        d = {k: copy.deepcopy(mapping[k]) for k in ["schema_version", "household_id", "as_of", "engagement", "sources"]}
        d.update(
            request_id="P4-RECON",
            base_currency="USD",
            household_party_ids=[mapping["party_id"]],
            valuation_policy={"version": "synthetic-P4-v1", "max_age_days": 7, "source_ids": ["p4-account-mapping"]},
            expected_accounts=[],
            records=[],
            account_mapping_evidence=mapping["mapping_review"],
        )
        sid = import_common(d, out, HH)
        cash = Decimal(str(mapping["cash_amount"]))
        assets, liabilities = Decimal(str(facts["assets"]["value"])), Decimal(str(facts["liabilities"]["value"]))
        for name, kind, value, area in [
            ("investment", "asset", assets - cash, "assets"),
            ("cash", "asset", cash, "assets"),
            ("liability", "liability", liabilities, "liabilities"),
        ]:
            aid = mapping["account_ids"][name]
            citations = sorted(set(facts[area]["source_ids"] + [sid, "p4-account-mapping"]))
            d["expected_accounts"].append(dict(account_id=aid, kind=kind, source_ids=citations))
            d["records"].append(
                dict(
                    record_id="RECORD-" + aid,
                    account_id=aid,
                    kind=kind,
                    value=str(value),
                    household_share="1",
                    currency="USD",
                    valuation_date=DATE,
                    owner_party_ids=[mapping["party_id"]],
                    identity_verified=not (unconfirmed and name == "investment"),
                    is_held_away=False,
                    source_ids=citations,
                )
            )
        d["reference_totals"] = dict(
            assets=str(assets),
            liabilities=str(liabilities),
            basis="household-share",
            currency="USD",
            source_ids=facts["assets"]["source_ids"] + [sid],
        )
        return d

    def recon_to_risk(self, recon, discovery):
        d = fixture("risk-assessments")
        sid = import_common(d, recon, d["household_id"])
        goal_sid = import_common(d, discovery, d["household_id"])
        total = recon["result"]["totals"]
        if total["partial"]:
            d["dimensions"]["loss_capacity"].pop("investable_assets", None)
        else:
            d["dimensions"]["loss_capacity"]["investable_assets"] = float(total["assets"])
        d["dimensions"]["loss_capacity"]["source_ids"] += [sid]
        cash = next((x for x in recon["result"]["included_accounts"] if x["account_id"] == "MARIN-CASH"), None)
        liq = d["dimensions"]["liquidity"]
        liq["available_liquid_amount"] = float(cash["household_value"]) if cash else None
        liq["required_amount"] = discovery["result"]["goals"][0]["target_amount"]
        liq["source_ids"] += [sid, goal_sid]
        return d

    def risk_to_ips(self, risk):
        d = fixture("ips-policy")
        sid = import_common(d, risk, d["household_id"])
        profile = d["mandate"]["risk_profile"]
        profile.update(
            profile_artifact_id=risk["artifact_id"], assessment_reference="generated-artifact:" + risk["artifact_id"]
        )
        profile["source_ids"] += [sid]
        profile["dimensions"] = [
            dict(
                dimension=x["dimension"].replace("_", "-"),
                assessment=json.dumps(x["facts"], sort_keys=True),
                source_ids=sorted(set(x["facts"].get("source_ids", []) + [sid])),
            )
            for x in risk["result"]["dimensions"]
        ]
        dimensions = {x["dimension"]: x["facts"] for x in risk["result"]["dimensions"]}
        required = dimensions.get("liquidity", {}).get("required_amount")
        d["mandate"]["liquidity"]["reserve_amount"] = required
        d["mandate"]["liquidity"]["source_ids"] += [sid]
        for event in d["mandate"]["liquidity"]["events"]:
            event["amount"] = required
            event["source_ids"] += [sid]
        d["mandate"]["objectives"]["spending_objective"] = (
            f"Review the supplied dated reserve requirement: {required if required is not None else 'unknown'} USD"
        )
        d["mandate"]["objectives"]["source_ids"] += [sid]
        d["mandate"]["time_horizon"]["months"] = dimensions.get("horizon", {}).get("months")
        d["mandate"]["time_horizon"]["source_ids"] += [sid]
        profile["unresolved_findings"] = [
            dict(
                description=x["message"],
                source_ids=x["source_ids"],
                origin_artifact_id=x["artifact_id"],
                origin_code=x["code"],
            )
            for x in issues_from(risk)
            if x["status"] == "unresolved"
        ]
        return d

    def planning_chain(self, unconfirmed=False):
        discovery = self.compute(DISCOVERY, fixture("discovery"))
        recon = self.compute(RECON, self.discovery_to_recon(discovery, unconfirmed))
        risk = self.compute(RISK, self.recon_to_risk(recon, discovery))
        ips = self.compute(IPS, self.risk_to_ips(risk))
        for before, after in [(discovery, recon), (recon, risk), (discovery, risk), (risk, ips)]:
            self.assert_common_edge(before, after)
        return discovery, recon, risk, ips

    def ips_to_review(self, ips, recon, discovery):
        if any(x["household_id"] != HH for x in (ips, recon, discovery)):
            raise ValueError("review household conflict")
        if recon["result"]["totals"]["partial"]:
            raise ValueError("this review adapter requires a complete included-account inventory")
        d = fixture("review-policy")
        d["prior_artifact_id"] = ips["artifact_id"]
        sources = {}
        for out in (ips, recon, discovery):
            for s in out["sources"] + [artifact_source(out)]:
                if s["source_id"] in sources and sources[s["source_id"]] != s:
                    raise ValueError("source collision")
                sources[s["source_id"]] = s
        review_sources = [
            dict(
                source_id=s["source_id"],
                system="p4-import",
                ref=s["reference"],
                date=s["as_of"],
                owner=s["owner"],
                valid_until=s["valid_until"],
            )
            for s in sources.values()
        ]
        ips_sid = artifact_source(ips)["source_id"]
        recon_sid = artifact_source(recon)["source_id"]
        disc_sid = artifact_source(discovery)["source_id"]
        issues = issues_from(ips)
        d["handoff_issue_register"] = copy.deepcopy(issues)
        d["handoff_source_map"] = {s["source_id"]: s["source_id"] for s in sources.values()}
        row = dict(
            client_id=HH,
            review_id="P4-REVIEW-MARIN",
            household_name="Marin household (masked)",
            advisor="Synthetic advisor",
            review_type="ad-hoc",
            entity_resolved=True,
            flags=dict(recommendation_contemplated=False, senior_investor=False, drift_flag=False),
            sources=review_sources,
            accounts=[],
            holdings=[],
            performance=[],
            goals=[],
            plan_items=[],
            prior_notes=[],
            service_history=[],
            life_events=[],
            open_actions=[],
            discussion_questions=[],
            disclosures=[dict(disclosure_id="DRAFT-LIMITATIONS", source_id=ips_sid)],
        )
        for a in recon["result"]["included_accounts"]:
            if a["kind"] != "asset":
                continue
            row["accounts"].append(
                dict(
                    account_id=a["account_id"],
                    type="Taxable",
                    registration="Supplied individual registration",
                    reported_value=float(a["household_value"]),
                    source_id=recon_sid,
                )
            )
            row["holdings"].append(
                dict(
                    account_id=a["account_id"],
                    security="Supplied account-level value; no inferred security composition",
                    asset_class="Unclassified account aggregate",
                    market_value=float(a["household_value"]),
                    source_id=recon_sid,
                )
            )
        row["household_reported_value"] = float(recon["result"]["totals"]["assets"])
        for goal in discovery["result"]["goals"]:
            row["goals"].append(
                dict(
                    goal=goal["description"],
                    target=goal["target_amount"],
                    target_date=goal["target_date"],
                    source_id=disc_sid,
                )
            )
        row["plan_items"].append(
            dict(
                item="Draft IPS " + ips["artifact_id"] + "; pending human review and not effective",
                status=ips["status"],
                source_id=ips_sid,
            )
        )
        for issue in issues:
            text = (
                "["
                + issue["artifact_id"]
                + " / "
                + issue["code"]
                + "] "
                + issue["message"]
                + "; status="
                + issue["status"]
            )
            row["open_actions"].append(
                dict(
                    action=text,
                    owner="Synthetic advisor",
                    due_date="2026-09-24",
                    status="open" if issue["status"] == "unresolved" else "closed",
                    source_id=ips_sid,
                )
            )
            row["discussion_questions"].append(
                dict(question="Review this attributed issue: " + text, source_id=ips_sid)
            )
        d["reviews"] = [row]
        return d

    def review_to_followup(self, review):
        pack = review["reviews"][0].get("review_pack")
        d = fixture("followup-meeting")
        if not pack or pack["client_id"] != d["client"]["household_id"]:
            raise ValueError("review pack missing or wrong meeting household")
        d["prior_artifact_id"] = review["artifact_id"]
        d["meeting_record"]["reviewed_artifacts"] = [review["artifact_id"]]
        d["handoff_issue_register"] = copy.deepcopy(snapshot(review)["handoff_issue_register"])
        d["review_citation_map"] = {}
        for s in snapshot(review)["reviews"][0]["sources"]:
            citation = f"{s['system']}:{s['ref']}@{s['date']}"
            d["source_inventory"].append(
                dict(citation=citation, owner=s["owner"], as_of=s["date"], valid_until=s["valid_until"])
            )
            d["review_citation_map"][s["source_id"]] = citation
        d["source_inventory"].append(
            dict(
                citation="generated-artifact:" + review["artifact_id"],
                owner="Synthetic P4 record steward",
                as_of=DATE,
                valid_until="2026-12-31",
            )
        )
        d["discussion_points"] = [
            dict(
                topic="Open evidence issue discussed in the separately supplied meeting record",
                summary=a["action"],
                citation=a["citation"],
            )
            for a in pack["open_actions"]
        ]
        d["action_items"] = [
            dict(
                id="P4-ACTION-" + str(i + 1),
                owner=a["owner"],
                description=a["action"],
                due_date=a["due_date"],
                citation=a["citation"],
            )
            for i, a in enumerate(pack["open_actions"])
            if a["status"] == "open"
        ]
        d["client_communication"]["key_points"] = [
            dict(text=a["description"], citation=a["citation"]) for a in d["action_items"]
        ]
        return d

    def family_to_trust(self, family, resolved=False, mapping=None):
        mapping = mapping or fixture("subject-map")
        d = fixture("trust")
        subject = family["result"]["family_subject"]
        member = next((x for x in subject["members"] if x["member_id"] == mapping["member_id"]), None)
        if (
            subject["family_id"] != mapping["family_id"]
            or not member
            or member["household_id"] != mapping["household_id"]
        ):
            raise ValueError("family subject mapping is not established")
        if d["trust_id"] != mapping["trust_id"] or d["beneficiaries"][0]["household_id"] != mapping["household_id"]:
            raise ValueError("trust beneficiary mapping conflicts")
        if set(s["source_id"] for s in family["sources"]) != set(mapping["allowed_source_ids"]):
            raise ValueError("source disclosure scope exceeds reviewed internal handoff permission")
        sid = import_common(d, family, "family:" + mapping["family_id"])
        merge_sources(d, mapping["sources"])
        d.pop("handoff_inputs")
        legal_topic = next(
            x
            for x in family["result"]["decision_register"]
            if x["topic"]["decision_class"] == "legal-authority-question"
        )
        d["distribution_requests"][0]["packet"][0]["description"] += (
            "; family discussion context only: " + legal_topic["topic"]["proposed_decision"]
        )
        d["distribution_requests"][0]["packet"][0]["source_ids"] += [sid, "p4-subject-map"]
        d["distribution_requests"][0]["source_ids"] += [sid, "p4-subject-map"]
        if resolved:
            for issue in d["upstream_issues"]:
                if issue["code"] == "legal-authority-boundary":
                    issue["status"] = "resolved"
                    issue["resolution"] = copy.deepcopy(mapping["resolution"])
        return d

    def trust_to_service(self, trust):
        d = fixture("service-policy")
        mapping = fixture("subject-map")
        if trust["household_id"] != "trust:" + mapping["trust_id"]:
            raise ValueError("wrong trust for beneficiary service preparation")
        distribution = trust["result"]["distribution_requests"][0]
        if distribution["beneficiary_household_id"] != d["household_id"]:
            raise ValueError("beneficiary household does not match service context")
        sid = import_common(d, trust, trust["household_id"])
        d["subject_mapping_evidence"] = mapping
        cash = trust["result"]["cash_reconciliation"][0]
        d["accounts"] = [
            dict(
                account_id=cash["account"]["account_id"],
                registration="trust",
                currency="USD",
                owner_party_ids=["TRUST-ENTITY"],
                available_cash=float(cash["components"]["total"]["expected_closing"])
                if cash["components"]["total"]["expected_closing"] is not None
                else None,
                positions=[],
                source_ids=[sid],
            )
        ]
        raw = distribution["record"]
        d["requests"] = [
            dict(
                service_request_id="P4-TUITION-PACKET",
                type="distribution",
                account_id=raw["account_id"],
                requested_by_party_id="FID-1",
                requested_date=DATE,
                source_ids=[sid],
                details=dict(
                    amount=float(distribution["outstanding_requested_amount"])
                    if distribution["outstanding_requested_amount"] is not None
                    else None,
                    currency="USD",
                    payee_ref_masked="Beneficiary tuition payee ****7",
                    purpose=raw["purpose"],
                    tax_instruction_ref="synthetic:unexecuted-tax-instructions-P4",
                    source_ids=[sid],
                ),
            )
        ]
        d["conditions"] = [
            dict(
                condition_id="P4-CONDITION-" + str(i),
                service_request_id="P4-TUITION-PACKET",
                requirement=req,
                status="received",
                description="Attributed evidence record received for human review; no authorization inferred",
                source_ids=[sid],
            )
            for i, req in enumerate(d["policy"]["service_requirements"]["distribution"])
        ]
        d["distribution_lineage"] = {
            k: copy.deepcopy(distribution[k])
            for k in ["record", "observed_current_period_paid", "outstanding_requested_amount", "payment_approval"]
        }
        return d

    def private_to_lending(self, private):
        d = fixture("lending-policy")
        sid = import_common(d, private, d["household_id"])
        account = private["result"]["account_liquidity"][0]
        schedule = account["schedule"]
        known = [x for x in schedule if x["committed_balance"] is not None]
        complete = len(known) == len(schedule) and account["opening_cash_after_reserve"] is not None
        negative = [x for x in known if Decimal(x["committed_balance"]) < 0]
        amount = (
            str(max((max(-Decimal(x["committed_balance"]), Decimal(0)) for x in known), default=Decimal(0)))
            if complete
            else None
        )
        needed = negative[0]["date"] if complete and negative else "2026-09-24"
        d["funding_need"] = dict(
            amount=amount,
            needed_by=needed,
            purpose="Additional funding for the account's dated known obligations; all original account cash and reserve already included upstream",
            purpose_category="securities-purchase",
            source_ids=[sid],
        )
        d["liquid_resources"]["source_ids"] += [sid]
        d["funding_schedule_lineage"] = dict(
            account_id=account["account"]["account_id"],
            schedule=copy.deepcopy(schedule),
            opening_cash_after_reserve=account["opening_cash_after_reserve"],
            method="Peak known-obligation deficit funded by first shortfall date; forecast calls excluded and source account cash not reused",
        )
        return d

    def construction_to_comparison(self, construction, unknown_cost=False):
        d = fixture("comparison-economics")
        sid = import_common(d, construction, d["household_id"])
        if unknown_cost:
            d["security_economics"]["EQ-B"]["expense_ratio_bps"] = None
        for candidate in construction["result"]["candidates"]:
            holdings = []
            for h in candidate["holdings"] + [
                dict(
                    security_id="CASH",
                    weight=candidate["cash_weight"],
                    amount=candidate["cash_amount"],
                    source_ids=[sid],
                )
            ]:
                sec = h["security_id"]
                row = copy.deepcopy(d["security_economics"][sec])
                row.update(
                    holding_id=candidate["candidate_id"] + "-" + sec,
                    security_id=sec,
                    weight=h["weight"],
                    market_value=h["amount"],
                )
                row["source_ids"] = sorted(set(row["source_ids"] + h["source_ids"] + [sid]))
                holdings.append(row)
            d["proposals"].append(
                dict(
                    proposal_id=candidate["candidate_id"],
                    currency=snapshot(construction)["currency"],
                    portfolio_value=snapshot(construction)["portfolio_value"],
                    holdings=holdings,
                    source_ids=[sid, "p4-comparison-economics"],
                    **d["model_costs"][candidate["model_id"]],
                )
            )
        return d

    def comparison_to_recommendation(self, comparison, construction):
        d = fixture("recommendation-policy")
        sid = import_common(d, comparison, d["household_id"])
        origins = {x["artifact_id"]: x for x in (construction, comparison)}
        issues = d.pop("upstream_issues")
        d["handoff_issue_register"] = copy.deepcopy(issues)
        result = comparison["result"]
        cost_summary = [
            dict(
                proposal_id=p["proposal_id"],
                portfolio_value=p["portfolio_value"],
                ongoing_cost_bps=p["metrics"]["ongoing_cost_bps"],
                ongoing_cost_amount=p["metrics"]["ongoing_cost_amount"],
                first_year_cost_amount=p["metrics"]["first_year_cost_amount"],
                cost_components=p["metrics"]["cost_components"],
                weighted_expense_bps=p["metrics"]["weighted_expense_bps"],
            )
            for p in result["proposals"]
        ]
        descriptions = {
            "costs": {
                "cost_components": json.dumps(cost_summary, sort_keys=True),
                "cost_comparison": json.dumps(result["pairwise_differences"], sort_keys=True),
            },
            "strategy_review": {
                "risks": json.dumps(issues, sort_keys=True),
                "features": "Model-derived allocations from "
                + construction["artifact_id"]
                + ". No implementation or candidate selection.",
                "costs": json.dumps(cost_summary, sort_keys=True),
            },
            "alternatives": {
                "available_alternatives": json.dumps([p["proposal_id"] for p in result["proposals"]]),
                "rationale": "Both supplied candidates retained for professional comparison. No winner or recommendation is inferred from lower cost.",
            },
        }
        for check, kinds in descriptions.items():
            record = dict(
                check_id=check,
                assessment="documented",
                reviewed_by="Synthetic investment analyst reviewing generated comparison",
                recorded_on=DATE,
                source_ids=[sid],
                items=[],
                unresolved_issues=[],
            )
            for kind, description in kinds.items():
                record["items"].append(
                    dict(
                        item_id=check + "-" + kind,
                        kind=kind,
                        description=description,
                        subject_id=d["recommendation"]["recommendation_id"],
                        source_ids=[sid],
                    )
                )
            for issue in issues:
                if issue["status"] != "unresolved":
                    continue
                selected_check = "costs" if "cost" in issue["code"] else "strategy_review"
                if selected_check != check:
                    continue
                origin = origins[issue["artifact_id"]]
                record["unresolved_issues"].append(
                    dict(
                        code=issue["code"],
                        message=issue["message"],
                        source_ids=issue["source_ids"],
                        origin="upstream-artifact",
                        upstream_artifact=dict(
                            skill=origin["skill"], artifact_id=origin["artifact_id"], input_hash=origin["input_hash"]
                        ),
                    )
                )
            d["evidence"].append(record)
        d["recommendation"]["source_ids"] += [sid]
        return d

    def assert_recommendation_edge(self, comparison, construction, recommendation):
        self.assertEqual(recommendation["household_id"], comparison["household_id"])
        doc = snapshot(recommendation)
        self.assertEqual(doc["handoff_issue_register"], issues_from(comparison))
        registry = {s["source_id"]: s for s in recommendation["sources"]}
        for source in comparison["sources"] + [artifact_source(comparison)]:
            self.assertEqual(registry.get(source["source_id"]), source)
        origin_map = {x["artifact_id"]: x for x in (construction, comparison)}
        carried = [issue for check in recommendation["result"]["checks"] for issue in check["unresolved_issues"]]
        for issue in issues_from(comparison):
            if issue["status"] != "unresolved":
                continue
            match = next(
                (
                    x
                    for x in carried
                    if x["upstream_artifact"]["artifact_id"] == issue["artifact_id"]
                    and x["code"] == issue["code"]
                    and x["message"] == issue["message"]
                ),
                None,
            )
            self.assertIsNotNone(match)
            self.assertEqual(match["source_ids"], issue["source_ids"])
            origin = origin_map[issue["artifact_id"]]
            self.assertEqual(match["upstream_artifact"]["input_hash"], origin["input_hash"])
        self.assertEqual(recommendation["result"]["determination"], "not-made")

    def test_01_discovery_reconciliation_risk_ips_chain(self):
        discovery, recon, risk, ips = self.planning_chain()
        self.assertEqual(discovery["status"], "review-ready")
        self.assertEqual(
            recon["result"]["totals"],
            dict(
                currency="USD",
                basis="household-share",
                assets="720000.00",
                liabilities="90000.00",
                net_worth="630000.00",
                partial=False,
            ),
        )
        self.assertEqual(
            risk["result"]["metrics"],
            dict(capacity_loss_pct=10.0, willingness_loss_amount=180000.0, liquidity_shortfall=65000.0),
        )
        self.assertEqual(
            {x["code"] for x in risk["findings"]}, {"willingness_capacity_conflict", "liquidity_shortfall"}
        )
        self.assertEqual(ips["status"], "needs-data")
        self.assertIsNone(ips["result"]["effective_date"])
        for issue in issues_from(risk):
            self.assertIn(issue["message"], ips["result"]["draft_markdown"])

    def test_02_generated_ips_review_followup_chain(self):
        discovery, recon, risk, ips = self.planning_chain()
        review = self.compute(REVIEW, self.ips_to_review(ips, recon, discovery))
        self.assertEqual(review["reviews"][0]["status"], "draft-review")
        pack = review["reviews"][0]["review_pack"]
        self.assertEqual(pack["portfolio_summary"]["total_value"], 720000)
        follow = self.compute(FOLLOWUP, self.review_to_followup(review))
        self.assert_review_edge(ips, review)
        self.assert_followup_edge(review, follow)
        self.assertEqual(follow["client"]["household_id"], HH)
        self.assertEqual(follow["prior_artifact_id"], review["artifact_id"])
        self.assertEqual(follow["crm_write_status"], "not-written")
        self.assertEqual(snapshot(follow)["handoff_issue_register"], issues_from(ips))
        self.assertEqual(len(follow["action_items"]), len(pack["open_actions"]))
        for issue in issues_from(risk):
            self.assertIn(issue["artifact_id"], follow["client_communication"]["body"])
            self.assertIn(issue["message"], follow["client_communication"]["body"])
            self.assertIn(issue["code"], follow["client_communication"]["body"])
        registry = {x["citation"] for x in follow["source_inventory"]}
        self.assertTrue(all(a["citation"] in registry for a in follow["action_items"]))
        self.assertTrue(all(a["status"] == "pending" for a in follow["approvals"]))

    def test_03_family_trust_service_unresolved_chain(self):
        family = self.compute(FAMILY, fixture("family"))
        self.assertIn("legal-authority-boundary", {x["code"] for x in family["findings"]})
        trust = self.compute(TRUST, self.family_to_trust(family))
        service = self.compute(SERVICE, self.trust_to_service(trust))
        self.assert_common_edge(family, trust, "family:P4-COUNCIL")
        self.assert_common_edge(trust, service, "trust:P4-TRUST")
        self.assertEqual(service["household_id"], "P4-HH-BEN")
        self.assertEqual(trust["status"], "needs-data")
        self.assertEqual(service["status"], "needs-data")
        self.assertIsNone(snapshot(service)["requests"][0]["details"]["amount"])
        self.assertEqual(
            trust["result"]["cash_reconciliation"][0]["components"]["total"]["expected_closing"], "49000.00"
        )
        self.assertTrue(
            any(
                x["artifact_id"] == family["artifact_id"] and x["code"] == "legal-authority-boundary"
                for x in service["result"]["upstream_issues"]
            )
        )
        self.assertEqual(snapshot(service)["accounts"][0]["owner_party_ids"], ["TRUST-ENTITY"])

    def test_04_private_ledger_to_liquidity_chain(self):
        private = self.compute(PRIVATE, fixture("private"))
        lending = self.compute(LENDING, self.private_to_lending(private))
        self.assert_common_edge(private, lending)
        account = private["result"]["account_liquidity"][0]
        self.assertEqual(account["opening_cash_after_reserve"], "18000.00")
        self.assertEqual(account["horizon_committed_balance"], "-8000.00")
        self.assertEqual(account["horizon_forecast_balance"], "-15000.00")
        self.assertEqual(lending["result"]["funding_need"]["amount"], "8000.00")
        self.assertEqual(lending["result"]["funding_need"]["needed_by"], "2026-09-24")
        cash, sale = lending["result"]["liquidity_alternatives"]
        self.assertEqual(cash["net_proceeds"], "0.00")
        self.assertEqual(cash["funding_gap"], "8000.00")
        self.assertEqual(sale["net_proceeds"], "8700.00")
        self.assertEqual(sale["funding_gap"], "0.00")
        self.assertEqual(lending["status"], "needs-data")
        self.assertIsNone(lending["result"]["selected_option"])

    def test_05_attributed_resolution_survives_family_trust_service(self):
        family = self.compute(FAMILY, fixture("family"))
        trust = self.compute(TRUST, self.family_to_trust(family, resolved=True))
        service = self.compute(SERVICE, self.trust_to_service(trust))
        self.assert_common_edge(family, trust, "family:P4-COUNCIL")
        self.assert_common_edge(trust, service, "trust:P4-TRUST")
        self.assertEqual(trust["status"], "review-ready")
        self.assertEqual(service["status"], "review-ready")
        # 8000 requested -1000 paid before period -3000 settled this period =4000.
        self.assertEqual(snapshot(service)["requests"][0]["details"]["amount"], 4000.0)
        issue = next(x for x in service["result"]["upstream_issues"] if x["code"] == "legal-authority-boundary")
        self.assertEqual(issue["status"], "resolved")
        self.assertEqual(issue["resolution"], fixture("subject-map")["resolution"])
        self.assertEqual(snapshot(service)["distribution_lineage"]["payment_approval"], "not-given")

    def test_06_resolution_label_without_evidence_does_not_clear(self):
        family = self.compute(FAMILY, fixture("family"))
        d = self.family_to_trust(family)
        d["upstream_issues"][0]["status"] = "resolved"
        code, _ = self.cli(TRUST, "calculate_or_transform.py", d)
        self.assertNotEqual(code, 0)
        d = self.family_to_trust(family, resolved=True)
        d["upstream_issues"][0]["resolution"]["source_ids"] = []
        out = self.compute(TRUST, d)
        self.assertEqual(out["status"], "needs-data")
        self.assertIsNone(out["result"]["distribution_requests"][0]["outstanding_requested_amount"])

    def test_07_unconfirmed_account_never_becomes_complete_assets(self):
        discovery, recon, risk, ips = self.planning_chain(unconfirmed=True)
        self.assertTrue(recon["result"]["totals"]["partial"])
        self.assertEqual(recon["result"]["totals"]["assets"], "25000.00")
        self.assertIsNone(snapshot(risk)["dimensions"]["loss_capacity"].get("investable_assets"))
        self.assertIsNone(risk["result"]["metrics"]["capacity_loss_pct"])
        self.assertEqual(ips["status"], "needs-data")
        self.assertTrue(
            any(
                x["artifact_id"] == recon["artifact_id"] and x["code"] == "account-unreconciled"
                for x in ips["result"]["upstream_issues"]
            )
        )
        with self.assertRaisesRegex(ValueError, "complete included-account"):
            self.ips_to_review(ips, recon, discovery)

    def test_08_missing_private_evidence_does_not_become_zero_funding(self):
        d = fixture("private")
        d["coverage"]["movements_complete"] = False
        private = self.compute(PRIVATE, d)
        lending = self.compute(LENDING, self.private_to_lending(private))
        self.assert_common_edge(private, lending)
        self.assertIsNone(lending["result"]["funding_need"]["amount"])
        self.assertTrue(all(x["funding_gap"] is None for x in lending["result"]["liquidity_alternatives"]))
        self.assertEqual(lending["status"], "needs-data")

    def test_09_wrong_household_and_collection_subject_are_blocked(self):
        discovery = self.compute(DISCOVERY, fixture("discovery"))
        d = fixture("risk-assessments")
        d["household_id"] = "P4-OTHER-HH"
        with self.assertRaisesRegex(ValueError, "subject"):
            import_common(d, discovery, d["household_id"])
        family = self.compute(FAMILY, fixture("family"))
        mapping = fixture("subject-map")
        mapping["household_id"] = "P4-HH-OTHER"
        with self.assertRaisesRegex(ValueError, "mapping"):
            self.family_to_trust(family, mapping=mapping)
        # The real beneficiary ID must never be replaced with the family collection marker.
        mapping = fixture("subject-map")
        mapping["household_id"] = family["household_id"]
        with self.assertRaisesRegex(ValueError, "mapping"):
            self.family_to_trust(family, mapping=mapping)

    def test_10_conflicting_source_id_is_not_overwritten(self):
        discovery = self.compute(DISCOVERY, fixture("discovery"))
        d = fixture("risk-assessments")
        d["sources"].append({**discovery["sources"][0], "reference": "synthetic:different-record"})
        with self.assertRaisesRegex(ValueError, "conflicting source"):
            import_common(d, discovery, HH)

    def test_11_downstream_input_issue_drop_is_caught_by_cross_artifact_assertion(self):
        # A self-consistent downstream artifact alone cannot prove an upstream issue was retained.
        private = self.compute(PRIVATE, fixture("private"))
        d = self.private_to_lending(private)
        d["upstream_issues"] = []
        dropped = self.compute(LENDING, d)
        with self.assertRaises(AssertionError):
            self.assert_common_edge(private, dropped)

    def test_12_output_issue_identity_source_action_tampering_fails(self):
        private = self.compute(PRIVATE, fixture("private"))
        lending = self.compute(LENDING, self.private_to_lending(private))
        mutations = []
        d = copy.deepcopy(lending)
        d["result"]["upstream_issues"] = []
        mutations.append(d)
        d = copy.deepcopy(lending)
        d["household_id"] = "OTHER-HH"
        mutations.append(d)
        d = copy.deepcopy(lending)
        d["sources"][0]["reference"] = "rewritten"
        mutations.append(d)
        d = copy.deepcopy(lending)
        d["action_taken"] = True
        mutations.append(d)
        d = copy.deepcopy(lending)
        d["result"]["funding_need"]["amount"] = "0.00"
        mutations.append(d)
        for d in mutations:
            with self.subTest(mutation=d):
                code, _ = self.cli(LENDING, "validate_output.py", d)
                self.assertNotEqual(code, 0)

    def test_13_internal_family_handoff_requires_disclosure_scope(self):
        family = self.compute(FAMILY, fixture("family"))
        mapping = fixture("subject-map")
        mapping["allowed_source_ids"] = []
        with self.assertRaisesRegex(ValueError, "disclosure scope"):
            self.family_to_trust(family, mapping=mapping)

    def test_14_legacy_rendered_action_drop_is_caught_even_with_hidden_register(self):
        discovery, recon, risk, ips = self.planning_chain()
        review = self.compute(REVIEW, self.ips_to_review(ips, recon, discovery))
        d = self.review_to_followup(review)
        removed = d["action_items"].pop(0)
        d["discussion_points"] = [x for x in d["discussion_points"] if x["summary"] != removed["description"]]
        d["client_communication"]["key_points"] = [
            x for x in d["client_communication"]["key_points"] if x["text"] != removed["description"]
        ]
        out = self.compute(FOLLOWUP, d)
        self.assertEqual(snapshot(out)["handoff_issue_register"], issues_from(ips))
        with self.assertRaises(AssertionError):
            self.assert_followup_edge(review, out)

    def test_15_rebound_wrong_subject_cannot_pass_cross_artifact_check(self):
        private = self.compute(PRIVATE, fixture("private"))
        d = self.private_to_lending(private)
        d["household_id"] = "WRONG-HOUSEHOLD"
        d["handoff_inputs"][0]["target_household_id"] = "WRONG-HOUSEHOLD"
        out = self.compute(LENDING, d)
        with self.assertRaises(AssertionError):
            self.assert_common_edge(private, out)

    def test_16_original_source_drop_cannot_hide_behind_artifact_citation(self):
        private = self.compute(PRIVATE, fixture("private"))
        d = self.private_to_lending(private)
        d["sources"] = [x for x in d["sources"] if x["source_id"] != "p4-private-record"]
        for issue in d["upstream_issues"]:
            issue["source_ids"] = [s for s in issue["source_ids"] if s != "p4-private-record"]
        out = self.compute(LENDING, d)
        with self.assertRaises(AssertionError):
            self.assert_common_edge(private, out)

    def test_17_changed_upstream_facts_change_downstream_amounts(self):
        raw = fixture("discovery")
        raw["goals"][0]["target_amount"] = 100000
        discovery = self.compute(DISCOVERY, raw)
        recon = self.compute(RECON, self.discovery_to_recon(discovery))
        risk = self.compute(RISK, self.recon_to_risk(recon, discovery))
        ips = self.compute(IPS, self.risk_to_ips(risk))
        self.assertEqual(risk["result"]["metrics"]["liquidity_shortfall"], 75000)
        profile = next(s for s in ips["result"]["sections"] if s["key"] == "risk_profile")
        liquidity = next(x for x in profile["content"]["dimensions"] if x["dimension"] == "liquidity")
        self.assertEqual(json.loads(liquidity["assessment"])["required_amount"], 100000)
        liquidity_section = next(x for x in ips["result"]["sections"] if x["key"] == "liquidity")
        self.assertEqual(liquidity_section["content"]["reserve_amount"], 100000)
        self.assertEqual(liquidity_section["content"]["events"][0]["amount"], 100000)
        raw = fixture("private")
        raw["accounts"][0]["available_cash"] = 23000
        private = self.compute(PRIVATE, raw)
        lending = self.compute(LENDING, self.private_to_lending(private))
        self.assertEqual(lending["result"]["funding_need"]["amount"], "7000.00")
        self.assertEqual(lending["result"]["liquidity_alternatives"][0]["funding_gap"], "7000.00")

    def test_18_construction_comparison_recommendation_chain(self):
        construction = self.compute(CONSTRUCTION, fixture("construction"))
        comparison = self.compute(COMPARISON, self.construction_to_comparison(construction))
        recommendation = self.compute(RECOMMENDATION, self.comparison_to_recommendation(comparison, construction))
        self.assert_common_edge(construction, comparison)
        self.assert_recommendation_edge(comparison, construction, recommendation)
        holdings = {h["security_id"]: h for h in construction["result"]["candidates"][0]["holdings"]}
        self.assertEqual(holdings["EQ-A"]["weight"], 0.35)
        self.assertEqual(holdings["EQ-B"]["weight"], 0.30)
        self.assertEqual(holdings["EQ-A"]["amount"], 140000)
        metrics = [p["metrics"] for p in comparison["result"]["proposals"]]
        self.assertEqual([m["ongoing_cost_bps"] for m in metrics], [80, 68])
        self.assertEqual([m["first_year_cost_amount"] for m in metrics], [3400, 3020])
        self.assertEqual(comparison["result"]["pairwise_differences"][0]["first_year_cost_amount"], -380)
        self.assertEqual(metrics[0]["exposures"]["issuer_id"]["max_weight"], 0.65)
        checks = {x["check_id"]: x for x in recommendation["result"]["checks"]}
        costs = json.loads(next(x["description"] for x in checks["costs"]["items"] if x["kind"] == "cost_components"))
        self.assertEqual([x["first_year_cost_amount"] for x in costs], [3400, 3020])
        self.assertTrue(any(x["code"] == "model-review" for x in checks["strategy_review"]["unresolved_issues"]))
        self.assertTrue(any(x["code"] == "cost-review" for x in checks["costs"]["unresolved_issues"]))
        self.assertEqual(checks["costs"]["status"], "incomplete")
        self.assertEqual(checks["customer_profile"]["status"], "missing")
        self.assertEqual(recommendation["status"], "needs-data")
        self.assertIsNone(comparison["result"]["selected_proposal"])
        self.assertIsNone(construction["result"]["selected_candidate"])

    def test_19_unknown_cost_survives_comparison_and_recommendation(self):
        construction = self.compute(CONSTRUCTION, fixture("construction"))
        comparison = self.compute(COMPARISON, self.construction_to_comparison(construction, unknown_cost=True))
        recommendation = self.compute(RECOMMENDATION, self.comparison_to_recommendation(comparison, construction))
        self.assert_recommendation_edge(comparison, construction, recommendation)
        self.assertTrue(all(p["metrics"]["first_year_cost_amount"] is None for p in comparison["result"]["proposals"]))
        costs = next(c for c in recommendation["result"]["checks"] if c["check_id"] == "costs")
        components = json.loads(next(x["description"] for x in costs["items"] if x["kind"] == "cost_components"))
        self.assertTrue(all(x["first_year_cost_amount"] is None for x in components))
        self.assertEqual(recommendation["status"], "needs-data")

    def test_20_per_check_issue_loss_caught_despite_hidden_origin_register(self):
        construction = self.compute(CONSTRUCTION, fixture("construction"))
        comparison = self.compute(COMPARISON, self.construction_to_comparison(construction))
        d = self.comparison_to_recommendation(comparison, construction)
        for record in d["evidence"]:
            record["unresolved_issues"] = []
        recommendation = self.compute(RECOMMENDATION, d)
        with self.assertRaises(AssertionError):
            self.assert_recommendation_edge(comparison, construction, recommendation)


if __name__ == "__main__":
    unittest.main(verbosity=2)
