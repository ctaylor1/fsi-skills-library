"""Compute the documented financial review contract."""
from domain import check, compute, validate_output
from wealth_analysis import cli

if __name__ == "__main__":
    raise SystemExit(cli("compute", check, compute, validate_output, __file__))
