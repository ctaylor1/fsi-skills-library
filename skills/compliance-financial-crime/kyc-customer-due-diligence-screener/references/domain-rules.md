# Domain Rules — kyc-customer-due-diligence-screener

Explainable CDD **signals** and how they map to a **recommended review track**. Thresholds
and lists (UBO percentage, coverage target, higher-risk countries/industries, required
fields/documents) are **configuration** — versioned, owned by the Financial Crime / FIU
standard — not hard-coded judgments, and never tuned to an individual customer. The firm's
CIP/CDD program, the applicable AML rules (e.g., US BSA/CIP and the beneficial-ownership
requirement), and sanctions/PEP program standards take precedence over anything here.

Every signal is a **potential indicator or allegation**, never an adjudicated finding. The
skill recommends and evidences; a qualified analyst adjudicates and decides.

## Signal taxonomy

| Signal | Fires when (default config) | Evidence attached |
| ------ | --------------------------- | ----------------- |
| `missing_required_field` | A configured required KYC field is absent/blank for the customer type | Each missing field (record citation) |
| `missing_required_document` | A configured required document type is not on file | Each missing document type |
| `expired_document` | A document's `expiry_date` is before `as_of` | The expired document(s) |
| `unverified_identity` | No document carries `verified: true` | Note + identity citation |
| `identity_mismatch` | An `identity_checks` row has `match: false` (attribute did not reconcile across sources) | The unreconciled attribute(s) |
| `high_risk_jurisdiction` | Customer or any beneficial-owner `country` is on the configured higher-risk list | Party + country |
| `high_risk_industry` | Entity `industry` is on the configured higher-risk list (entity only) | Industry |
| `pep_flag` | One or more PEP indicators present (potential match) | Each PEP indicator |
| `sanctions_potential_match` | One or more potential sanctions/watchlist name matches present | Each potential match |
| `adverse_media_flag` | One or more adverse-media indicators present (allegation) | Each item |
| `ownership_over_100` | Declared beneficial ownership sums > 100% (data-quality gap; entity only) | The owners |
| `ubo_below_coverage` | Identified ownership < configured coverage target (default 75%; entity only) | The owners |
| `ubo_unverified` | A beneficial owner at/above the UBO threshold (default 25%) is not verified (entity only) | The unverified owner(s) |

Signals are **additive and independent**; the output reports each that fired with its own
evidence. There is no opaque composite "risk score" and no automated risk rating.

## Recommended-track mapping (deterministic, documented)

Implemented identically in `scripts/calculate_or_transform.py` (`recommended_track`) and
`scripts/validate_output.py` (`_expected_track`). Precedence, highest first:

| Recommended track | Rule |
| ----------------- | ---- |
| **Escalate-For-Adjudication** | `sanctions_potential_match` fired — a specialist + human must adjudicate the match before anything proceeds |
| **EDD-Recommended** | any elevated-risk signal fired (`high_risk_jurisdiction`, `high_risk_industry`, `pep_flag`, `adverse_media_flag`, `ubo_below_coverage`, `ubo_unverified`) |
| **Remediate-First** | only completeness/identity/data-quality gaps fired (`missing_required_field`, `missing_required_document`, `expired_document`, `unverified_identity`, `identity_mismatch`, `ownership_over_100`) |
| **Standard-CDD** | no signal fired |

The track is a **triage recommendation for a human analyst**. It is not a CDD/KYC decision,
a customer risk rating, or a sanctions/PEP disposition, and it never triggers a system-of-
record write, a filing, or a customer action.

## Hard boundaries (fail closed)

- Never approve, reject, onboard, exit/off-board, or otherwise decide the customer
  relationship, and never state or imply the CDD outcome is decided.
- Never adjudicate or **clear** a sanctions/watchlist or PEP potential match — route it to
  the specialist adjudicator and a human.
- Never state a customer **is** a criminal, sanctioned party, terrorist, or money launderer;
  describe indicators/allegations factually and attribute conclusions to the analyst.
- Never set, update, or write a **customer risk rating** or any system of record.
- Never draft or file a SAR/regulatory report, and never close the case.
- Never tune thresholds/lists to the individual; use only the versioned config.

## Benign-explanation prompts (include whenever a risk signal fired)

A legitimate business model in a higher-risk industry; a PEP relationship with fully
documented source of wealth/funds; adverse media referring to a different person of the same
name (entity-resolution error); an ownership-coverage gap explained by a documented nominee
or trust structure pending evidence; a not-yet-verified owner whose verification is simply in
progress. The pack must invite the analyst to weigh these before any conclusion.
