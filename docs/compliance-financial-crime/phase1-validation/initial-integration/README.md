# Initial integration checks

These are retained failures from an intermediate integration state. The metadata check
found 15 enum mismatches, corrected to repository-supported values. The first portable
run found 25 commands requiring an unavailable `python` executable; affected CFC evals
now invoke `python3 -B`. It also repeated focused suites outside the manifest; the final
runner executes each suite once. These initial files are not final acceptance results.
