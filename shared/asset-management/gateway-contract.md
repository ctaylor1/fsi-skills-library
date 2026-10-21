# Investment data gateway contract 1.0

The optional `licensed_data_connector.py REQUEST.json --policy POLICY.json` client
performs two fixed, read-only HTTPS GETs. It is implemented in the data architecture
package. Other modernization skills consume historical evidence; they never open
a connection. An institution must implement or configure its approved gateway;
this repository includes no vendor account, live entitlement service or credentials.

## Separate deployment authority

The operator supplies a policy file held outside the requester's editable evidence
area. Neither a model-authored request nor a source document can amend this policy.
Its schema_version is `investment-data-gateway/1.0`; required fields are policy_id,
version, approval_reference, principal, base_url (HTTPS origin only),
approved_origins (exact origins), token_env, datasets keyed by dataset ID with
purposes/audiences lists, timeout_seconds (1–30), max_attempts (1–3), max_bytes
(1–2000000), and receipt_max_age_seconds (1–300). The administrator approves
the gateway's TLS identity, IAM principal, vendor contract, dataset purpose and
audience. Protect policy changes, credentials and output files with institutional
access controls. A JSON file cannot prove who approved it.

The client reads the bearer token only from the named environment variable.
It uses certificate/hostname validation, disables ambient proxies, forbids redirects,
never accepts caller-defined endpoints, and never logs the token. Approved GETs
may retry only bounded transient failures; permission denials and malformed or
unbound responses stop the read. There are no order, transfer or write operations.

## Wire protocol

The request has exactly seven nonempty string fields: request_id, dataset,
object_id, as_of, knowledge_cutoff, purpose and audience. Dates are YYYY-MM-DD.
The client adds a random nonce and SHA-256 of canonical JSON (sorted keys, compact
separators, finite numbers). Both `/v1/permissions` and `/v1/snapshots` receive
these fields as query parameters over the approved TLS connection. Gateways must
avoid recording sensitive query fields in unrestricted logs.

Permission response: repeat every request field, request_sha256, nonce and the
policy's principal; supply schema_version, `operation: read`, boolean `allowed`,
nonempty license_version, and UTC checked_at/expires_at. Only affirmative, exact,
fresh bindings allow the snapshot request. The gateway must enforce authorization
again when serving the snapshot; a separate permission check alone cannot prevent
revocation between requests. Snapshot response repeats the same binding fields
and version, and contains nonempty snapshot_id, a bounded list of object records,
and records_sha256. The client rechecks permission freshness after retrieval and
rejects content-hash or context mismatches. Server errors are not proof of access.

## Observability, limitations and recovery

Outputs retain request/policy/content/permission hashes, snapshot identity,
received_at and attempt statuses. Real network runs say
`live-approved-gateway-read`; injected test transports always say
`synthetic-transport`, with permission_verified_at_gateway false. These observations
trust the institution-approved gateway's identity and policy; they do not verify
vendor source truth, complete inventory or legal interpretation of a license.
Do not publish record payloads or raw permission metadata beyond their permitted
audience. Apply deployment retention and encryption controls.

Saved receipts are historical evidence only. A caller can edit an offline receipt;
the planners therefore never turn a supplied `allowed` or `verified` flag into
current authorization. A subsequent read needs another live check. Interrupted
reads deliver no successful snapshot. Restarting with a fresh request creates a
new nonce and trace; do not merge partially obtained records or silently substitute
a newer point-in-time cutoff. Institution acceptance must exercise real denied
access, license expiry, revocation, permission changes, provider downtime and
recovery, as well as approved historical queries and monitored failure alerts.
