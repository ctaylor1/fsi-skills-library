# Commercial-card primary basis

Reviewed 2026-09-18; owner corporate payments product and issuer operations; review due 2026-10-18.

[Visa Commercial Payment Controls](https://developer.visa.com/capabilities/visa-commercial-fraud-solutions/visa-commercial-payment-controls-vpc) documents commercial amount, velocity, merchant-category and other restrictions. [Visa B2B Virtual Account codes](https://developer.visa.com/pages/B2B-virtual-account-payment-method-codes) and [implementation guidance](https://developer.visa.com/capabilities/vpa/docs-how-to) distinguish provider-specific controls and account types. Use exact issuer/processor enablement and current API evidence; local policy checks are not Visa integration or universal network behavior.

Buyer/supplier/invoice binding, canonical economic identities, conservative reservation of held/pending exposure and unknown capacity are library conventions. Neither an authorization nor an MCC match establishes settlement or correct supplier payment. Credit, underwriting, liability contract, employee policy and rewards belong with card-program-designer and the accountable product/risk teams. This module sends no API request and handles no credential secret.
