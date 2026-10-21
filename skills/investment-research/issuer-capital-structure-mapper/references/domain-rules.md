# Implemented method and limits

The native method inventories a supplied corporate debt schedule. It groups known principal by currency, type, supplied seniority, secured status and maturity year; computes eligible principal-weighted coupon and years to maturity; and totals scheduled amounts within two calendar years. It does not establish complete economic or legal capital structure, verify guarantees or structural subordination, convert currencies, price instruments, assess refinancing access, or recommend a transaction.

WAC = sum(principal × supplied coupon) / total principal, only for complete eligible inventory. WAM = sum(principal × actual days from economic as-of / 365.25) / total principal, only for complete dated inventory. Known-subset averages divide by only the known eligible principal. Near term includes dates from economic as-of through its two-calendar-year anniversary, inclusive. A negative years-to-maturity describes a past-due supplied date; it does not establish legal default.

Unknown principal, coupon, maturity and security must remain distinct from zero and unsecured. Currency totals never cross currencies. Validate exact output against the original schedule, including every contributing instrument and all buckets. Entity association and source authenticity remain analyst review responsibilities.

Economic dates/forecast periods do not establish when information was known. Where this native contract uses an intraday cutoff, source knowledge timestamps require timezones. A source reference and a reproducible hash do not prove content authenticity or licensed use.
