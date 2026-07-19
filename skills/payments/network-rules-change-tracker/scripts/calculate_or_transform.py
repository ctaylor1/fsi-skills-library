#!/usr/bin/env python3
"""Deterministic network-rules change-tracking engine for network-rules-change-tracker.

Reads a monitoring-run file (see validate_input.py), and for each card-network / payment-
scheme bulletin: checks bulletin authenticity and version, extracts obligations and effective
dates, maps each obligation to the product/process/control/contract/system inventories,
scores implementation readiness against the effective date, checks owner traceability,
deduplicates against previously-open alerts, checks bulletin-feed freshness, and packages a
severity-ranked alert queue.

IMPORTANT — this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor (R3 decision support). It
computes and packages alerts and a triage severity for a human payments compliance / product /
operations reviewer. It NEVER adopts a rule, accepts or closes an obligation, changes a
control / procedure / contract / system, files or attests anything, or writes any system of
record. Bands and thresholds are versioned configuration (see references/domain-rules.md),
never tuned per-bulletin and never an adjudication.

Usage:
  python calculate_or_transform.py run.json | --selftest
Prints the monitoring pack JSON to stdout.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; no network rule was adopted, no obligation was accepted, "
              "closed, filed, or attested, no product, procedure, control, contract, or system "
              "was changed, and no system of record was updated. Network-rule changes require "
              "human payments compliance, product, and operations review and adjudication.")
SEVERITY_QUEUE = {"High": "network-rules-escalation",
                  "Medium": "network-rules-review-queue",
                  "Low": "network-rules-watchlist"}
DOMAIN_TO_INV = {"product": "products", "process": "processes", "control": "controls",
                 "contract": "contracts", "system": "systems"}
DEFAULT_BANDS = {"critical": 30, "high": 60, "medium": 120}


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def expected_severity(category: str, status: str, breach_type: str) -> str:
    """Deterministic severity tie-out (mirrored in validate_output.py)."""
    if category == "freshness":
        return "Low"
    if category == "authenticity":
        return "High"
    if category == "readiness":
        if breach_type in ("overdue", "critical"):
            return "High"
        if breach_type == "high":
            return "Medium"
        return "Low"  # medium band
    if category in ("mapping", "ownership"):
        return "Medium"
    return "Low" if status == "WARN" else "Medium"


def _fingerprint(bulletin_id, obligation_id, category, breach_type) -> str:
    return f"{bulletin_id}|{obligation_id or ''}|{category}|{breach_type}"


def _readiness_band(days, bands):
    """Deterministic readiness band from days-to-effective. None => on plan, no alert."""
    if days < 0:
        return "overdue"
    if days <= bands["critical"]:
        return "critical"
    if days <= bands["high"]:
        return "high"
    if days <= bands["medium"]:
        return "medium"
    return None


def _mk_alert(bulletin_id, network, obligation_id, category, breach_type, status,
              evidence, extra=None):
    severity = expected_severity(category, status, breach_type)
    alert = {
        "fingerprint": _fingerprint(bulletin_id, obligation_id, category, breach_type),
        "bulletin_id": bulletin_id,
        "network": network,
        "obligation_id": obligation_id or "",
        "category": category,
        "breach_type": breach_type,
        "status": status,
        "severity": severity,
        "queue": SEVERITY_QUEUE[severity],
        "is_duplicate": False,
        "unverified_source": False,
        "stale_input": False,
        "evidence": evidence,
    }
    if extra:
        alert.update(extra)
    return alert


def _authenticity(b, as_of, config_version, networks):
    """Bulletin-level authenticity/version check -> at most one alert."""
    bid = b.get("bulletin_id")
    network = b.get("network")
    trusted = set(networks or [])
    reason = None
    if trusted and network not in trusted:
        breach_type, reason = "untrusted_network", f"network {network!r} not in trusted publishers"
    elif b.get("signature_verified") is not True:
        breach_type, reason = "unverified", "bulletin signature not verified"
    elif not b.get("version") or not b.get("source_ref"):
        breach_type, reason = "unverified", "missing version or source_ref"
    else:
        return None
    ev = [{"bulletin_id": bid, "network": network, "reason": reason,
           "citation": f"feed:bulletin={bid};network={network}@{as_of}"},
          {"category": "authenticity",
           "citation": f"taxonomy:category=authenticity@{config_version}"}]
    return _mk_alert(bid, network, None, "authenticity", breach_type, "BREACH", ev,
                     {"reason": reason})


def _mapping(b, o, as_of, config_version, inventories):
    bid = b.get("bulletin_id")
    network = b.get("network")
    oid = o.get("obligation_id")
    domains = o.get("domains") or []
    impacts = o.get("impacts") or {}
    alerts = []

    # completeness: every declared domain must carry at least one concrete impact id
    unmapped = []
    for d in domains:
        inv_key = DOMAIN_TO_INV.get(d)
        if inv_key is None:
            continue
        if not impacts.get(inv_key):
            unmapped.append(d)
    if unmapped:
        ev = [{"obligation_id": oid, "unmapped_domains": sorted(unmapped),
               "citation": f"inventory:obligation={oid};domains={','.join(sorted(unmapped))}@{as_of}"},
              {"bulletin_id": bid,
               "citation": f"bulletin:bulletin={bid};obligation={oid}@{as_of}"},
              {"category": "mapping", "citation": f"taxonomy:category=mapping@{config_version}"}]
        alerts.append(_mk_alert(bid, network, oid, "mapping", "unmapped_domain", "BREACH", ev,
                                {"unmapped_domains": sorted(unmapped)}))

    # applicability: every referenced impact id must exist in the inventory of record
    dangling = []
    for inv_key in DOMAIN_TO_INV.values():
        known = set(inventories.get(inv_key) or [])
        for ref in impacts.get(inv_key) or []:
            if ref not in known:
                dangling.append(f"{inv_key}:{ref}")
    if dangling:
        ev = [{"obligation_id": oid, "dangling_references": sorted(dangling),
               "citation": f"inventory:obligation={oid};dangling={len(dangling)}@{as_of}"},
              {"bulletin_id": bid,
               "citation": f"bulletin:bulletin={bid};obligation={oid}@{as_of}"},
              {"category": "mapping", "citation": f"taxonomy:category=mapping@{config_version}"}]
        alerts.append(_mk_alert(bid, network, oid, "mapping", "dangling_reference", "BREACH", ev,
                                {"dangling_references": sorted(dangling)}))
    return alerts


def _ownership(b, o, as_of, config_version, owners):
    bid = b.get("bulletin_id")
    network = b.get("network")
    oid = o.get("obligation_id")
    owner = o.get("owner")
    registry = set(owners or [])
    breach_type = reason = None
    if not owner:
        breach_type, reason = "no_owner", "obligation has no assigned owner"
    elif registry and owner not in registry:
        breach_type, reason = "unknown_owner", f"owner {owner!r} not in owner registry"
    else:
        return None
    ev = [{"obligation_id": oid, "owner": owner or None, "reason": reason,
           "citation": f"inventory:obligation={oid};owner={owner or 'NONE'}@{as_of}"},
          {"category": "ownership", "citation": f"taxonomy:category=ownership@{config_version}"}]
    return _mk_alert(bid, network, oid, "ownership", breach_type, "BREACH", ev, {"reason": reason})


def _readiness(b, o, run_as_of, as_of, config_version, min_lead_days, bands):
    bid = b.get("bulletin_id")
    network = b.get("network")
    oid = o.get("obligation_id")
    impl = o.get("implementation") or {}
    status = impl.get("status") or "not_started"
    eff = _parse_date(b.get("effective_date"))
    if status == "complete" or run_as_of is None or eff is None:
        return None
    days = (eff - run_as_of).days
    band = _readiness_band(days, bands)
    if band is None:
        return None
    alert_status = "BREACH" if band in ("overdue", "critical") else "WARN"
    lead = o.get("required_lead_days")
    lead = int(_num(lead, min_lead_days))
    ev = [{"obligation_id": oid, "effective_date": b.get("effective_date"),
           "days_to_effective": days, "implementation_status": status,
           "required_lead_days": lead,
           "citation": f"tracker:bulletin={bid};obligation={oid};status={status}@{as_of}"},
          {"bulletin_id": bid, "effective_date": b.get("effective_date"),
           "citation": f"bulletin:bulletin={bid};effective={b.get('effective_date')}@{as_of}"},
          {"category": "readiness", "citation": f"taxonomy:category=readiness@{config_version}"}]
    return _mk_alert(bid, network, oid, "readiness", band, alert_status, ev,
                     {"effective_date": b.get("effective_date"),
                      "days_to_effective": days, "implementation_status": status})


def compute(doc: dict) -> dict:
    as_of = doc["as_of"]
    config_version = doc.get("config_version")
    run_as_of = _parse_date(as_of)
    networks = doc.get("networks") or []
    owners = doc.get("owners") or []
    inventories = doc.get("inventories") or {}
    min_lead_days = _num(doc.get("min_lead_days"), 60)
    bands = dict(DEFAULT_BANDS)
    bands.update({k: int(_num(v, DEFAULT_BANDS[k])) for k, v in (doc.get("readiness_bands") or {}).items() if k in DEFAULT_BANDS})
    open_fps = {a.get("fingerprint") for a in (doc.get("open_alerts") or [])}
    bulletins = doc.get("bulletins") or []

    # feed freshness (bulletin feed / inventory snapshot)
    feed_as_of = doc.get("feed_as_of")
    max_stale = doc.get("max_feed_staleness_days")
    feed_dt = _parse_date(feed_as_of)
    feed_staleness = None
    feed_stale = False
    if run_as_of and feed_dt:
        feed_staleness = (run_as_of - feed_dt).days
        if max_stale is not None and feed_staleness > int(max_stale):
            feed_stale = True
    data_freshness = [{"scope": "feed", "feed_as_of": feed_as_of,
                       "staleness_days": feed_staleness, "stale": feed_stale}]

    all_alerts = []
    unauthentic = set()
    obligation_count = 0

    for b in bulletins:
        bid = b.get("bulletin_id")
        auth = _authenticity(b, as_of, config_version, networks)
        if auth is not None:
            all_alerts.append(auth)
            unauthentic.add(bid)
        for o in (b.get("obligations") or []):
            obligation_count += 1
            all_alerts.extend(_mapping(b, o, as_of, config_version, inventories))
            own = _ownership(b, o, as_of, config_version, owners)
            if own is not None:
                all_alerts.append(own)
            rdy = _readiness(b, o, run_as_of, as_of, config_version, min_lead_days, bands)
            if rdy is not None:
                all_alerts.append(rdy)

    # freshness alert — never suppress; flag the stale feed explicitly
    if feed_stale:
        ev = [{"scope": "feed", "feed_as_of": feed_as_of, "staleness_days": feed_staleness,
               "citation": f"feed:snapshot=bulletins;feed_as_of={feed_as_of}@{as_of}"},
              {"category": "freshness", "citation": f"taxonomy:category=freshness@{config_version}"}]
        all_alerts.append(_mk_alert("FEED", "feed", None, "freshness", "freshness", "WARN", ev,
                                    {"staleness_days": feed_staleness, "limit": max_stale}))

    # propagate data-quality flags (surface, never drop)
    for a in all_alerts:
        if a["bulletin_id"] in unauthentic:
            a["unverified_source"] = True
        if feed_stale and a["category"] != "freshness":
            a["stale_input"] = True

    # deduplication against previously-open alerts
    new_alerts, still_open = [], []
    for a in all_alerts:
        if a["fingerprint"] in open_fps:
            a["is_duplicate"] = True
            still_open.append(a["fingerprint"])
        else:
            new_alerts.append(a["fingerprint"])

    # escalation packaging (severity buckets over all alerts)
    sev_counts = defaultdict(int)
    status_counts = defaultdict(int)
    for a in all_alerts:
        sev_counts[a["severity"]] += 1
        status_counts[a["status"]] += 1
    escalations = [{"severity": sev, "queue": SEVERITY_QUEUE[sev], "count": sev_counts[sev]}
                   for sev in ("High", "Medium", "Low") if sev_counts[sev]]

    return {
        "run_id": doc.get("run_id"),
        "as_of": as_of,
        "config_version": config_version,
        "data_freshness": data_freshness,
        "alerts": all_alerts,
        "new_alerts": new_alerts,
        "still_open": still_open,
        "summary": {
            "bulletins": len(bulletins),
            "obligations": obligation_count,
            "alerts_total": len(all_alerts),
            "new": len(new_alerts),
            "deduplicated": len(still_open),
            "warn": status_counts.get("WARN", 0),
            "breach": status_counts.get("BREACH", 0),
            "unauthentic_bulletins": sorted(unauthentic),
            "stale_feed": feed_stale,
        },
        "escalations": escalations,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
