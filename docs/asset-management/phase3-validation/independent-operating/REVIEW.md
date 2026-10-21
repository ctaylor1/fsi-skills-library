# Independent Phase 3 operating-model and gateway review

Review date: 2026-10-04. Reviewer authored the separate T04 package, not T05 or the gateway. No production requests, credentials or records were used. Runtime implementation files were not edited during this review.

## Fresh T05 forward exercise

Request: review a Fund C settlement service moving to a co-sourced operating model while retaining controller accountability, independent control checking, audit/exit/subcontractor rights and observed transition evidence.

The reviewer constructed the native operations request and AM request from documented schemas without reading or copying package golden fixtures. The observed UTC window contains one opening episode, three arrivals, two completions, one cancellation and one closing item. Independent expectations were written before checking AM output: conservation difference 0; both completed durations 4 hours; SLA fraction 0 at a 3-hour limit; completed mean cost 15 USD; mean human time 30 minutes; labor utilization 0.375; remaining backlog age 12 hours. These are observed episode measures, not service-improvement or staffing conclusions. A zero observed SLA fraction does not create authorization: the result only indicates readiness for owner review.

The real native operations CLI generated the upstream output. The real AM calculate and detached-output-validator CLIs then executed the fresh request and variants. `expectations.json`, the native input/output pair, individual AM inputs/outputs and `forward-results.json` retain the evidence.

All 11 cases passed their independently stated expectations: the fresh complete case, untested control, identical maker/checker, missing outsourcing right, open transition exception, different population, cyclic dependency, untested new control version, forged shared baseline, future rehearsal and unreconciled native baseline. No concrete T05 defect was found in these bounded exercises. This is not source authentication, a real institution pilot, model-wide behavioral assurance or professional acceptance.

## Gateway protocol probes

`gateway_probe.py` uses a fresh request, independently written deployment policy, synthetic bearer string, synthetic read transport and fixed clock. It never opens a network connection. The tests cover two fixed operations, synthetic access labeling, permission denial, wrong principal/nonce, expiry before and during retrieval, snapshot hash/context mismatches, bounded retries, numeric policy bounds, malformed policy allowlists and redirect rejection.

Initial result: 15 of 16 probes passed; see `gateway-probe-initial-results.json`. The candidate string-allowlist defect identified during code reading was repaired by the root agent before the actual probe executed, so the saved result verifies rejection of malformed lists and does not claim an executed pre-fix failure.

One concrete defect was reproduced: a gateway permission response containing an additional `debug_authorization` field with the supplied synthetic bearer credential was copied verbatim into the successful output's `permission_receipt`. At the reviewed revision, `shared/asset-management/licensed_data_connector.py` lines 175–180 returned the entire response without a credential-reflection guard. The CLI serializes that output. This violates the documented promise not to emit the bearer token and can persist a credential if a gateway includes diagnostic header metadata. The same boundary should protect snapshot records and other returned strings. The probe checks the presence of the synthetic credential without writing a real credential or including it in its result file.

Requested repair: withhold a response that reflects the credential, and maintain safe error messages; strict receipt-field validation can additionally reduce accidental metadata disclosure. Keep the initial failing evidence separate from subsequent successful reruns. A successful synthetic repair check does not verify TLS configuration or a real gateway's authentication and entitlement behavior.

## Repair verification

The root agent added credential-reflection rejection to the shared gateway. Re-running the unchanged protocol expectations now passes all 16 probes: the debug-credential response is withheld. `gateway-probe-initial-results.json` retains the original 15/16 result; `gateway-probe-results.json` records the repaired 16/16 result. The reviewer did not edit the gateway implementation.
