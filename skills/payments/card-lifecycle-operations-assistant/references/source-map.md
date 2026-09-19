# Source map

Reviewed 2026-09-18. The actual issuer, processor, card network and token-service
profiles govern event meanings, holds, presentment and operations eligibility.
Public orientation sources are not network rulebooks.

- [OCC Credit Card Lending](https://www.occ.gov/publications-and-resources/publications/comptrollers-handbook/files/credit-card-lending/pub-ch-credit-card.pdf): issuer/acquirer and card operations context.
- [Federal Reserve Regulation II commentary](https://www.federalreserve.gov/frrs/regulations/appendix-a-official-board-commentary-on-regulation-ii.htm): authorization, clearance and settlement are distinct network functions; this is not an event-code mapping for every network.
- [PCI Token Service Provider Standard](https://www.pcisecuritystandards.org/standards/token-service-provider-tsp/): EMV payment token service context; token state cannot be inferred from a merchant vault token or card-status label.
- [CFPB Regulation Z, section 1026.12](https://www.consumerfinance.gov/rules-policy/regulations/1026/12/): card-specific legal context only; the issuer-dispute workflow owns applicability and consumer clocks.

For US, EA and UK requests, use institution/issuer profiles explicitly covering the
participant and jurisdiction. The shared regional rail profiles provide orientation,
not issuer-specific hold-release logic. No fixed expiry duration or universal source
system is distributed. Licensed card rules remain in authorized distribution.
