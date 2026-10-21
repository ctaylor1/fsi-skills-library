"""Additional source/profile checks for supplied-rule specialist reviews.

No built-in legal, clinical, coding, actuarial or payment authority is conferred.
Existing Phase 4 runtime and contracts remain unchanged.
"""

from design_support import Review, text
from workflow_contract import iso_date

VERSION = "insurance-specialist/1.0"


def reject_floating_evidence(value):
    """Reject parsed floats throughout native data, including superseded records.

    A fractional JSON token may have already rounded to a whole float; source
    preservation requires exact strings even for evidence not used in arithmetic.
    """
    if isinstance(value, float):
        raise ValueError("data requires JSON integer tokens or exact decimal strings; floats lose source precision")
    if isinstance(value, dict):
        for child in value.values():
            reject_floating_evidence(child)
    elif isinstance(value, list):
        for child in value:
            reject_floating_evidence(child)


class SpecialistReview(Review):
    def __init__(self, doc, method):
        reject_floating_evidence(doc["data"])
        super().__init__(doc, method)
        self.fields(self.data, ("owner", "market", "program", "product"))
        for field in ("market", "program", "product"):
            allowed = self.profile.get(field + "s")
            self.need(
                isinstance(allowed, list) and all(text(x) for x in allowed) and self.data.get(field) in allowed,
                "specialist-profile",
                "Reviewed profile must expressly include the actual " + field,
            )
        self.fields(self.profile, ("rule_basis", "limitations"))
        self.scope_valid = self.clear

    def num(self, row, key, **options):
        value = row.get(key)
        if isinstance(value, float):
            raise ValueError(
                key + ": supply a JSON integer or exact decimal text; floating-point tokens lose source precision"
            )
        return super().num(row, key, **options)

    def applicable(self, row, when, label="Rule"):
        """Known inclusive policy dates must cover the actual service/event basis."""
        self.evidence(row, label)
        self.fields(row, ("version", "reviewed_by"))
        start = self.date(row, "effective_from", future=True)
        end = self.date(row, "effective_to", future=True)
        valid = start is not None and end is not None and when is not None
        if isinstance(when, str):
            when = iso_date(when)
        return self.need(
            valid and start <= when <= end,
            "rule-period",
            label + " dates must cover the actual event/service period",
            row,
        )


def scoped_profile_example(
    method, *, line="health", market="US-TEST", program="synthetic-commercial", product="synthetic-product"
):
    """Synthetic fixture helper only; never a rule pack or production default."""
    return {
        "profile_id": "SYNTHETIC-ONLY",
        "version": "1",
        "reviewed_by": "Fictional method owner",
        "source_refs": ["SYNTHETIC-SOURCE"],
        "jurisdictions": ["US-TEST"],
        "lines_of_business": [line],
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "method": method,
        "markets": [market],
        "programs": [program],
        "products": [product],
        "rule_basis": "Explicitly supplied fictional sandbox method; no adopted legal rule",
        "limitations": "Synthetic test evidence only; actual institution applicability unverified",
    }
