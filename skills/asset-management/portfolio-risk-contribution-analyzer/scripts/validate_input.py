#!/usr/bin/env python3
"""Deterministic input validation for portfolio-risk-contribution-analyzer.

Validates a risk-contribution-input file before the packet is built. Fails closed on
structural problems (missing portfolio/weights/covariance, non-numeric or non-square
covariance, degenerate/negative variance on the diagonal, mismatched covariance order,
missing approved-engine total or methodology version); warns on data-quality gaps that
weaken the packet (missing provenance/citation, weights that do not sum to one, negative
weights, covariance that violates the Cauchy-Schwarz bound, no prior review baseline).

Input schema (JSON): see references/source-map.md. Key fields:
  portfolio_id, as_of (YYYY-MM-DD), config_version, currency, units, risk_measure,
  methodology{name,version,provenance,citation}, grouping_dimension,
  reconciliation{tolerance_rel}, materiality{pcr_abs_threshold,total_risk_rel_threshold},
  positions[ {position_id, instrument_id, issuer, sector, asset_class,
              weight->{value,provenance,citation}} ],
  covariance{order[position_id...], matrix[[...]], provenance, citation},
  approved_engine{total_risk->{value,provenance,citation}},
  prior_review{packet_id, as_of, total_risk, positions[{position_id,pcr,trc}]}

Usage:
  python validate_input.py risk_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("portfolio_id", "as_of", "config_version", "methodology",
                "positions", "covariance", "approved_engine")


def _v(node):
    try:
        import math
        value = node.get("value") if isinstance(node, dict) else node
        if isinstance(value, bool): return None
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, AttributeError):
        return None


def _prov_cite(node):
    if isinstance(node, dict):
        return (node.get("provenance") or "").strip(), (node.get("citation") or "").strip()
    return "", ""


def _validate_legacy(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    # methodology / version provenance (required for a Model & calculate artifact)
    method = doc.get("methodology") or {}
    if not (method.get("name") or "").strip():
        errors.append("methodology.name is required")
    if not (method.get("version") or "").strip():
        errors.append("methodology.version is required (version provenance)")
    mprov, mcite = _prov_cite(method)
    if not mprov or not mcite:
        warnings.append("methodology has no provenance/citation — validate_output will reject the pack")

    # positions
    positions = doc.get("positions") or []
    if not isinstance(positions, list) or not positions:
        errors.append("positions must be a non-empty list")
        return errors, warnings
    pos_ids = []
    weights = []
    for i, p in enumerate(positions):
        pid = p.get("position_id")
        if not pid:
            errors.append(f"positions[{i}] missing position_id")
            pid = f"#{i}"
        pos_ids.append(pid)
        wv = _v(p.get("weight"))
        weights.append(wv)
        if wv is None:
            errors.append(f"position {pid} weight is not numeric")
        prov, cite = _prov_cite(p.get("weight"))
        if not prov:
            warnings.append(f"position {pid} weight has no provenance — validate_output will reject the pack")
        if not cite:
            warnings.append(f"position {pid} weight has no citation — validate_output will reject the pack")
        if wv is not None and wv < 0:
            warnings.append(f"position {pid} weight {wv} is negative (long/short book) — contributions can be negative; confirm intended")
    if len(set(pos_ids)) != len(pos_ids):
        errors.append("duplicate position_id values in positions")
    if all(w is not None for w in weights):
        s = sum(weights)
        if abs(s - 1.0) > 1e-6:
            warnings.append(f"weights sum to {round(s, 6)} (not 1.0) — confirm cash/leverage treatment")

    # covariance
    cov = doc.get("covariance") or {}
    matrix = cov.get("matrix")
    order = cov.get("order", pos_ids)
    cprov, ccite = _prov_cite(cov)
    if not cprov or not ccite:
        warnings.append("covariance has no provenance/citation — validate_output will reject the pack")
    n = len(pos_ids)
    if not isinstance(matrix, list) or len(matrix) != n or any(
            not isinstance(row, list) or len(row) != n for row in matrix):
        errors.append(f"covariance.matrix must be a square {n}x{n} matrix matching positions count")
        return errors, warnings
    if list(order) != list(pos_ids):
        errors.append("covariance.order must match the positions order exactly "
                      "(position_id sequence); reorder before running")
    # numeric + symmetry + diagonal + Cauchy-Schwarz
    numeric = True
    for a in range(n):
        for b in range(n):
            if _v(matrix[a][b]) is None:
                errors.append(f"covariance[{a}][{b}] is not numeric")
                numeric = False
    if numeric:
        for a in range(n):
            if float(matrix[a][a]) <= 0.0:
                errors.append(f"covariance diagonal [{a}][{a}]={matrix[a][a]} must be > 0 (positive variance)")
        for a in range(n):
            for b in range(a + 1, n):
                if abs(float(matrix[a][b]) - float(matrix[b][a])) > 1e-9:
                    errors.append(f"covariance not symmetric at [{a}][{b}] vs [{b}][{a}] — engine will use the [order][order] cell")
                if float(matrix[a][a]) > 0 and float(matrix[b][b]) > 0:
                    if float(matrix[a][b]) ** 2 > float(matrix[a][a]) * float(matrix[b][b]) + 1e-12:
                        errors.append(f"covariance[{a}][{b}] violates the Cauchy-Schwarz bound "
                                        f"(|cov| > sqrt(var_a*var_b)); the matrix may not be valid")

    if doc.get("risk_measure") not in {"annualized_volatility", "volatility"}:
        errors.append("only annualized volatility is implemented; unsupported risk_measure")
    if doc.get("covariance", {}).get("horizon") != "annualized":
        errors.append("covariance.horizon must explicitly be annualized")
    if numeric and not errors:
        # LDL decomposition with zero-pivot checks accepts valid semidefinite matrices.
        work = [[float(v) for v in row] for row in matrix]
        tol = max(max(abs(v) for v in row) for row in work) * 1e-10
        for k in range(n):
            pivot = work[k][k]
            if pivot < -tol:
                errors.append("covariance must be positive semidefinite"); break
            if abs(pivot) <= tol:
                if any(abs(work[j][k]) > tol for j in range(k + 1, n)):
                    errors.append("covariance must be positive semidefinite"); break
                continue
            for i in range(k + 1, n):
                for j in range(k + 1, n):
                    work[i][j] -= work[i][k] * work[k][j] / pivot
    # approved engine total (reconciliation anchor)
    ae = doc.get("approved_engine") or {}
    if "total_risk" not in ae:
        errors.append("approved_engine.total_risk is required (reconciliation anchor)")
    elif _v(ae["total_risk"]) is None:
        errors.append("approved_engine.total_risk value is not numeric")
    else:
        aprov, acite = _prov_cite(ae["total_risk"])
        if not aprov or not acite:
            warnings.append("approved_engine.total_risk has no provenance/citation — validate_output will reject the pack")

    if _v((doc.get("approved_engine") or {}).get("total_risk")) is not None and _v(doc["approved_engine"]["total_risk"]) <= 0:
        errors.append("approved engine volatility must be positive")
    if float((doc.get("reconciliation") or {}).get("tolerance_rel", .01)) < 0:
        errors.append("reconciliation tolerance cannot be negative")
    if (doc.get("prior_review") or {}).get("as_of", "") >= doc.get("as_of", ""):
        errors.append("prior_review must predate current as_of")
    # prior review (optional; enables the material-change section)
    prior = doc.get("prior_review")
    if not prior:
        warnings.append("no prior_review supplied — the material-change section will be limited to a 'no prior baseline' note")
    else:
        if _v(prior.get("total_risk")) is None:
            warnings.append("prior_review.total_risk is missing/non-numeric — total-risk change cannot be measured")
        if not isinstance(prior.get("positions"), list):
            warnings.append("prior_review.positions missing — per-position change cannot be measured")

    return errors, warnings


def validate(doc: dict):
    """Validate finite source data and real ISO dates before package-specific checks."""
    import math
    from datetime import datetime
    errors = []
    def walk(value, path="input", key=""):
        if isinstance(value, str) and value.strip().lower() in {"nan", "inf", "infinity", "-inf", "+inf", "-infinity", "+infinity"}:
            errors.append(f"{path}: non-finite numeric string")
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f"{path}: non-finite number")
        if isinstance(value, dict):
            for k, v in value.items(): walk(v, f"{path}.{k}", k)
        elif isinstance(value, list):
            for i, v in enumerate(value): walk(v, f"{path}[{i}]", key)
        elif value not in (None, "") and (key in {"as_of", "prior_as_of", "date", "valuation_date", "run_date", "forecast_start", "effective_date", "holdings_as_of", "prices_as_of", "bucket_dates", "effective_from", "effective_to"}):
            try: datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError: errors.append(f"{path}: invalid ISO date/timestamp")
    if not isinstance(doc, dict): return ["input must be an object"], []
    walk(doc)
    if errors: return errors, []
    try:
        native_errors, warnings = _validate_legacy(doc)
        return native_errors, warnings
    except (TypeError, ValueError, KeyError, AttributeError, OverflowError) as exc:
        return [f"malformed input: {exc}"], []


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "risk_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
