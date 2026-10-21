# Method and supported scope

Calculate a supplied gross asset NAV with sourced haircuts, liabilities, costs, tax leakage and dilution; does not appraise assets or assure completeness.

The domain helper validates structural, finite-number, basis and method conditions before computation; the separately retained original is required for complete output reconstruction. Supplied economic bounds and source metadata are evidence inputs, not institutional endorsements. Negative equity and failed funding checks remain visible. Professional acceptance remains not established.

Adjusted asset value is sum(gross value times one minus haircut); equity subtracts full liabilities, disposal costs, tax leakage and preferred claims once. Asset values must be gross of liabilities. Asset and liability inventories are supplied; no inference of completeness.
