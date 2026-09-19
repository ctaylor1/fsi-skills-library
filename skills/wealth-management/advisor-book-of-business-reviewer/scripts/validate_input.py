#!/usr/bin/env python3
from book_review import SKILL, validate, build
from wealth_workflow import run_cli, validate_result


def validate_output(out):
    return validate_result(out, SKILL, build)


if __name__ == "__main__":
    raise SystemExit(run_cli("input", validate, build, validate_output, __file__))
