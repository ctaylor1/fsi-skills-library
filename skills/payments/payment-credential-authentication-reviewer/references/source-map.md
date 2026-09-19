# Sources and freshness

Reviewed 2026-09-18. Recheck standards/provider rules before institutional use and
on a protocol, product, region or consent-flow change. Public sources orient the
review; current authorized implementation requirements and actual provider records
are necessary. Do not redistribute restricted scheme specifications.

- [EMVCo tokenisation](https://www.emvco.com/emv-technologies/payment-tokenisation/): domain restrictions and network-token roles; public index lists framework v2.4 published July 2026. The helper claims no conformance to that specification.
- [EMVCo 3DS](https://www.emvco.com/emv-technologies/3-d-secure/): consumer authentication message context; use the deployed version and actual final response.
- [FIDO passkeys](https://fidoalliance.org/passkeys/): relying-party-bound authentication credentials; sign-in evidence does not itself establish exact payment consent.
- [Visa Account Updater FAQ](https://developer.visa.com/capabilities/vau/vau-faq): updated credential information and authorization result are separate; participation, consent/opt-out and legal terms require review.

Priority: immutable provider/issuer event and credential registry records, scoped
consent/authority policy and professional applicability review, then public orientation.
Register provenance and effective/review dates; artifacts and reviewers are not
authenticated by this package. Privacy and secrets controls apply during extraction.
