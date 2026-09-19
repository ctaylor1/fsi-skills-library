#!/usr/bin/env python3
"""Native source-bound output CLI."""
import domain
from payment_foundation import main

if __name__ == "__main__":
    raise SystemExit(main(domain, "output"))
