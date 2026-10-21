# Primary method provenance

All examples and sensitivities are synthetic supplied assumptions. No empirical
factor model, market data, portfolio weights, data service or source
authentication is bundled. Primary context checked 2026-10-20:

- [BIS: Monetary policy transmission, what is known and what changed](https://www.bis.org/speeches/20150616-monetary-policy-transmission-whats-known-and-whats-changed)
  describes expectations, asset-price and exchange-rate transmission and their
  economic dependence. This package preserves explicit hypotheses and alternate
  channels rather than infer a universal response sign.
- [BIS: Asset prices and macroeconomic outcomes](https://www.bis.org/publ/work676.pdf)
  provides research context for the relationship between assets and macro
  conditions. The package does not reproduce that empirical work or calibrate
  its sensitivities from it.
- [ICMA: Bond markets, structures and yield calculations](https://www.icmagroup.org/assets/documents/Media/Bondmarketsbook/Bond%20markets_structures%20and%20yield%20calculations.pdf)
  supplies the modified-duration price/yield sensitivity context. The package
  takes duration as a supplied input and uses only the first-order response;
  it does not price a bond or compute duration from its cash flows.

Linear sensitivity and first-order modified-duration arithmetic are documented
explicitly in domain-rules.md and independently tested with synthetic inputs.
Institutional validation must establish the suitability of supplied coefficients,
the size of shocks and the coverage of nonlinear and interacting effects.
