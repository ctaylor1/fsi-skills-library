"""Small strict readers: absent domain evidence is a finding; malformed values fail."""

import math
from decimal import Decimal
from wealth_contract import nonempty, source_errors, iso_date


class Check:
    def __init__(self, doc):
        self.doc, self.errors, self.findings = doc, [], []

    def gap(self, path, message, code="missing-evidence"):
        self.findings.append({"code": code, "path": path, "message": message})

    def obj(self, value, path):
        if value is None:
            self.gap(path, "Required object is absent")
            return {}
        if not isinstance(value, dict):
            self.errors.append(f"{path} must be an object")
            return {}
        return value

    def rows(self, value, path, empty=False):
        if value is None:
            self.gap(path, "Required list is absent")
            return []
        if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
            self.errors.append(f"{path} must be a list of objects")
            return []
        if not value and not empty:
            self.gap(path, "Required list is empty")
        return value

    def text(self, value, path):
        if value is None or value == "":
            self.gap(path, "Required text is absent")
            return None
        if not nonempty(value):
            self.errors.append(f"{path} must be nonempty text")
            return None
        if value.strip().casefold() in {"tbd", "unknown", "not supplied", "not provided", "n/a"}:
            self.gap(path, "Placeholder text is not substantive evidence")
            return None
        return value

    def number(self, value, path, lo=0, hi=1e12, integer=False):
        if value is None:
            self.gap(path, "Required number is absent")
            return None
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not lo <= value <= hi
            or (integer and not isinstance(value, int))
        ):
            self.errors.append(f"{path} must be {'integer' if integer else 'finite number'} in [{lo},{hi}]")
            return None
        return value

    def amount(self, value, path, lo=0, hi=1e12):
        result = self.number(value, path, lo, hi)
        if result is not None and Decimal(str(result)) * 100 != (Decimal(str(result)) * 100).to_integral_value():
            self.errors.append(f"{path} must contain whole cents")
        return result

    def choice(self, value, path, choices):
        if value is None:
            self.gap(path, "Required selection is absent")
            return None
        if not isinstance(value, str) or value not in choices:
            self.errors.append(f"{path} must select one of {sorted(choices)}")
            return None
        return value

    def date(self, value, path):
        if value is None:
            self.gap(path, "Required date is absent")
            return None
        result = iso_date(value)
        if result is None:
            self.errors.append(f"{path} must be YYYY-MM-DD")
        return result

    def sources(self, row, path):
        for message in source_errors(row.get("source_ids"), self.doc):
            self.gap(path + ".source_ids", message, "source-gap")

    def strings(self, value, path, empty=False):
        if value is None:
            self.gap(path, "Required string list is absent")
            return []
        if not isinstance(value, list) or any(not nonempty(x) for x in value):
            self.errors.append(f"{path} must be a list of nonempty strings")
            return []
        if len(set(value)) != len(value):
            self.errors.append(f"{path} contains duplicates")
        if not value and not empty:
            self.gap(path, "Required string list is empty")
        return value

    def unique(self, rows, key, path):
        seen = set()
        for i, row in enumerate(rows):
            value = self.text(row.get(key), f"{path}[{i}].{key}")
            if value is not None:
                if value in seen:
                    self.errors.append(f"{path} duplicate {key}: {value}")
                seen.add(value)
        return seen

    def upstream(self):
        """Preserve attributed handoff issues; a caller status is not automatic resolution."""
        issues = self.rows(self.doc.get("upstream_issues"), "upstream_issues", empty=True)
        for index, issue in enumerate(issues):
            path = f"upstream_issues[{index}]"
            for field in ("artifact_id", "code", "message"):
                self.text(issue.get(field), path + "." + field)
            status = self.choice(issue.get("status"), path + ".status", {"unresolved", "resolved"})
            self.sources(issue, path)
            if status == "unresolved":
                self.findings.append(
                    {
                        "code": "upstream-unresolved",
                        "path": path,
                        "message": f"Upstream {issue.get('code', 'issue')} from {issue.get('artifact_id', 'unknown artifact')}: {issue.get('message', 'details not supplied')}",
                        "origin_artifact_id": issue.get("artifact_id"),
                        "origin_code": issue.get("code"),
                        "origin_status": status,
                        "source_ids": issue.get("source_ids"),
                    }
                )
            elif status == "resolved":
                resolution = self.obj(issue.get("resolution"), path + ".resolution")
                for field in ("owner", "reference"):
                    self.text(resolution.get(field), path + ".resolution." + field)
                resolved_on = self.date(resolution.get("as_of"), path + ".resolution.as_of")
                self.sources(resolution, path + ".resolution")
                if resolved_on and resolved_on > iso_date(self.doc["as_of"]):
                    self.gap(
                        path + ".resolution.as_of",
                        "Resolution is future-dated relative to the request",
                        "upstream-resolution-date",
                    )
        return issues

    def ready(self, path):
        return not any(
            x["path"] == path or x["path"].startswith(path + ".") or x["path"].startswith(path + "[")
            for x in self.findings
        )


def all_sources(value):
    ids = set()
    if isinstance(value, dict):
        raw_ids = value.get("source_ids")
        if isinstance(raw_ids, list):
            ids.update(x for x in raw_ids if isinstance(x, str))
        for k, v in value.items():
            if k != "source_ids":
                ids.update(all_sources(v))
    elif isinstance(value, list):
        for row in value:
            ids.update(all_sources(row))
    return sorted(ids)
