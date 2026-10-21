# Evaluator arithmetic correction — original case 12 retained

The original pre-run case 12 expectation says the direct blocked sum is `50.00000000000000000000000000%`, although the two raw stakes are `19.9999999999999999999999999999` and `30`. The generator used Python Decimal's default 28-digit context to format that expectation, rounding the correct sum upward. Its next pre-run expectation explicitly says below 50. Original expectation and output files have been retained unchanged.

The exact decimal sum is `49.9999999999999999999999999999`. It can be proved without decimal-context rounding by adding exact `fractions.Fraction` values or using a sufficient local Decimal precision. The native result preserved that exact string, kept the observation below 50, and did not clear the transaction. The native method passes this arithmetic check. The pre-run numerical wording failure belongs to the evaluator and cannot count as a package failure or an initially correct oracle.
