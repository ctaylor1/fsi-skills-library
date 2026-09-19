#!/usr/bin/env python3
from book_review import SKILL, validate as validate_input, build
from wealth_workflow import run_cli, validate_result


def validate(out):
    return validate_result(out, SKILL, build)


if __name__ == "__main__":
    raise SystemExit(run_cli("output", validate_input, build, validate, __file__))
