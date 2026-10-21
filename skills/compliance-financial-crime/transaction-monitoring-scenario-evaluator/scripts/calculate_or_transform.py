#!/usr/bin/env python3
"""Portable entry point for the pinned shared scenario replay component."""
from scenario_replay import *
from scenario_replay import main
import sys

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
