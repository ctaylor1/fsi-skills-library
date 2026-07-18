# Domain Rules — vulnerable-customer-support-assistant

Orientation references: the industry **vulnerability-drivers** framework widely adopted across
financial services (four drivers: Health, Life events, Resilience, Capability) and fair-treatment
/ consumer-protection expectations. The firm's own vulnerable-customer policy, its **approved
accommodations catalog**, and its **approved referral routes** take precedence and are versioned
contracts. At deployment, configure the jurisdiction pack (for example FCA FG21/1 guidance on the
fair treatment of vulnerable customers in the UK; ADA reasonable-accommodation and UDAAP
fair-treatment considerations in the US). Nothing here is legal or clinical advice.

## Vulnerability drivers (categories, not diagnoses)

A **driver** describes the *kind* of life circumstance a customer has signalled. It is a
support-context category — never a diagnosis or a determination about the person.

| Driver | What it covers (from the customer's own words) |
| ------ | ---------------------------------------------- |
| **Health** | Disclosed illness, disability, or an access/communication need |
| **Life events** | Bereavement, caring responsibilities, relationship breakdown, job loss, abuse |
| **Resilience** | Low financial resilience: income shock, arrears, difficulty keeping up |
| **Capability** | Low confidence/understanding, language barrier, digital exclusion |

## Signal → driver map (default; config-overridable)

Each signal must be a **quote the customer actually said/wrote**, with a `source_ref`. Signals
marked *sensitive* involve special-category data and require a captured consent status before
consent-dependent accommodations are applied. Signals marked *heightened* force a safeguarding
referral.

| Signal type | Driver | Sensitive | Heightened → route |
| ----------- | ------ | --------- | ------------------ |
| `bereavement` | Life events | no | — |
| `caring_responsibility` | Life events | no | — |
| `income_shock_job_loss` | Resilience | no | — |
| `financial_difficulty_arrears` | Resilience | no | — |
| `serious_illness` | Health | yes | — |
| `disability_access_need` | Health | no | — |
| `mental_health_disclosed` | Health | yes | — |
| `cognitive_or_memory_difficulty` | Capability | yes | — |
| `language_barrier` | Capability | no | — |
| `low_product_understanding` | Capability | no | — |
| `digital_exclusion` | Capability | no | — |
| `domestic_or_economic_abuse` | Life events | yes | `safeguarding-team` |
| `risk_of_harm` | Health | yes | `safeguarding-team` |

## Approved accommodations catalog (the ONLY accommodations that may be suggested)

Each accommodation is suggested only when a cited signal of an applicable type is present, and is
traced to that signal. Nothing outside this catalog may be suggested.

| Code | Accommodation | Applicable signal types | Consent |
| ---- | ------------- | ----------------------- | ------- |
| `ACC-COMMS-ALT` | Alternative communication format (large print, post, email) | disability_access_need, digital_exclusion, low_product_understanding | — |
| `ACC-EXTRA-TIME` | Allow extra time; avoid pressuring decisions | bereavement, serious_illness, mental_health_disclosed, cognitive_or_memory_difficulty, caring_responsibility, low_product_understanding | — |
| `ACC-THIRD-PARTY` | Register a trusted third party / authorized representative | cognitive_or_memory_difficulty, disability_access_need, serious_illness, mental_health_disclosed, caring_responsibility | required |
| `ACC-INTERPRETER` | Arrange interpreter / translation | language_barrier | — |
| `ACC-QUIET-CHANNEL` | Switch to the customer's preferred lower-stress channel | mental_health_disclosed, serious_illness, disability_access_need | — |
| `ACC-SPECIALIST-CALLBACK` | Offer a callback from a trained specialist | mental_health_disclosed, domestic_or_economic_abuse, risk_of_harm, cognitive_or_memory_difficulty | — |
| `ACC-FORBEARANCE-SIGNPOST` | Signpost the approved financial-difficulty / forbearance process | income_shock_job_loss, financial_difficulty_arrears | — |
| `ACC-EXTERNAL-SUPPORT-SIGNPOST` | Signpost approved external support organizations | bereavement, serious_illness, mental_health_disclosed, domestic_or_economic_abuse, caring_responsibility | — |

## Approved referral routes and priority

Only these routes may be suggested. The **primary** route is the highest-priority triggered:

1. `safeguarding-team` — any heightened signal (disclosed abuse or risk of harm).
2. `internal-vulnerability-specialist` — any sensitive signal, or two or more distinct drivers.
3. `financial-difficulty-team` — a Resilience driver present.
4. `external-support-signpost` — a Health or Life-events driver present (non-sensitive).

Any other triggered route is listed under **additional routes**. If none trigger, no referral is
suggested — accommodations alone may suffice, and the human decides.

## Hard boundaries (fail closed)

- No **diagnosis**, **capacity/fitness determination**, or **discriminatory service limitation**.
- No **financial, medical, or legal advice**.
- No **accommodation outside the approved catalog** and no **referral outside the approved routes**.
- No **suggestion without a cited signal**; no **system-of-record change or customer contact**.
- Heightened-risk signals **force** the safeguarding route and a time-sensitive human-review flag.

## Assessment — required contents

Durable `assessment_id`; observed signals (each cited); driver categories evidenced; suggested
accommodations (approved-catalog, each traced to its signal, with any `pending_consent` flag);
suggested referral (primary + additional approved routes) with supporting signals; consent status;
recorded `human_review_required` and `record_update: proposed` flags; the standing note.
