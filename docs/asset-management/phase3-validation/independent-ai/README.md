# Independent investment AI workflow forward exercise

Reviewer: independent agent that authored the AM data adapter, not this AI adapter. Date: 2026-10-04.

The reviewer constructed a new investment-research evidence-indexing assistant, six held-out risk cases and a separate two-job paired automation assessment directly from the documented native contracts. Package fixtures and goldens were not used as expected outputs. All records are synthetic. The exercise invokes native review scripts; it does not run a model or a live tool.

## Verified results

All 15 scenarios met independently stated expectations and every emitted output passed detached-original reconstruction. The complete six-episode case reports exact cost 0.21, mean cost 0.035, mean latency 350 ms and nearest-rank p95 of 600 ms. A tool-level timeout is counted once at episode level. Separate paired economics yields 30 projected capacity hours, annual cash net 200 and 24-month simple payback; those remain shared-owner projections with no causal claim.

The partial-evidence case retains all 6 requested cases while observing 5, labels 3 outcomes confirmed correct, reports 1 label error among 4 known labels, leaves total cost unknown when one cost is absent, and distinguishes partial known cost 0.12. Missing latency withholds mean and p95.

Adversarial cases preserve the boundary between matching text and safe execution: a prohibited write, unauthorized read, cross-portfolio read, timeout without stopping, excessive retries, answer after a denied call and a cost overrun cannot become a review candidate. Future-known data, train/test identity overlap, common label/output source, mixed prompt versions and fabricated shared economics fail validation.

`report.json` retains the 15 expected outcomes and actual observations. Each request/output remains separately available. Re-run with `python3 -B docs/asset-management/phase3-validation/independent-ai/evaluate.py`.

## Practitioner assessment and limits

The skill makes the human investment boundary, neutral-research owner, scoped read tools, independent label record and fixed experiment versions clear. Its output is useful for a controlled review because denominators, missing cases, cost/latency coverage, unsafe effects and source/label assurance remain explicit. The template and references distinguish design targets, supplied observations and institution-owned deployment acceptance.

No actionable defect was observed in this exercise. The finite checks do not prove semantic train/test independence, vendor model training isolation, label quality, actual entitlement enforcement, source truth, production readiness or general model quality. Those remain separately stated acceptance obligations. All native action/deployment flags remain false; no external source or production system was accessed.
