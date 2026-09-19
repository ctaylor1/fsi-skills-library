"""Native offline regional_domain entrypoint."""
import regional_domain
from payment_foundation import main

if __name__ == "__main__":
    raise SystemExit(main(regional_domain, "calculate"))
