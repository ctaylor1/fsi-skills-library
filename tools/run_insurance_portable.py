#!/usr/bin/env python3
"""Run pinned Insurance package checks in isolated temporary installations.

This is a software portability check, not a security sandbox or institutional
acceptance. Repository commands are trusted code, but their launch syntax is
restricted and all package bytes are checked before and after execution.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path, PurePosixPath
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from insurance_readiness_lib import package_snapshot, portfolio_snapshot, stable_hash


REPO = Path(__file__).resolve().parents[1]
OUTPUT_LIMIT = 16_384
MANIFEST = "evals/evals.json"


def _relative_path(value: object) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("path must be a nonempty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {".", ".."} for part in value.split("/")):
        raise ValueError("absolute paths and traversal are unsupported")
    return Path(*path.parts)


def command_argv(command: object, install: Path) -> list[str]:
    """Parse only a Python script invocation; never invoke a shell."""
    if not isinstance(command, str) or not command.strip():
        raise ValueError("command must be a nonempty string")
    # Reject operators even when quoted: these manifests do not need shell syntax.
    if any(character in command for character in ";&|<>`$\n\r"):
        raise ValueError("shell operators and substitutions are unsupported")
    tokens = shlex.split(command, posix=True)
    if len(tokens) < 2 or tokens[0] not in {"python", "python3"}:
        raise ValueError("only python/python3 scripts/... commands are supported")
    script = _relative_path(tokens[1])
    if script.parts[0] != "scripts" or script.suffix != ".py":
        raise ValueError("command must name a Python file under scripts/")
    script_path = install / script
    if not script_path.resolve().is_relative_to((install / "scripts").resolve()):
        raise ValueError("script escapes the installed scripts directory")
    if not script_path.is_file() or script_path.is_symlink():
        raise ValueError("script does not exist as an installed regular file")
    for argument in tokens[2:]:
        # Options such as --selftest are allowed. Path-like values must remain
        # within the installation, including --input=evals/files/input.json.
        value = argument.split("=", 1)[1] if argument.startswith("-") and "=" in argument else argument
        if "\\" in value or Path(value).is_absolute() or ".." in value.split("/"):
            raise ValueError("argument path traversal or escape is unsupported")
        if "/" in value and not (install / value).resolve().is_relative_to(install.resolve()):
            raise ValueError("argument path escapes the installation")
    return [sys.executable, "-B", str(script), *tokens[2:]]


def _manifest_entries(manifest: object) -> tuple[list[dict], list[dict], list[str]]:
    checks: list[dict] = []
    planned: list[dict] = []
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return checks, planned, ["eval manifest must be an object"]
    seen: set[str] = set()
    for collection in ("evals", "planned_natural_language_evals"):
        entries = manifest.get(collection, [] if collection != "evals" else None)
        if not isinstance(entries, list):
            errors.append(f"{collection} must be a list")
            continue
        for position, entry in enumerate(entries):
            label = f"{collection}[{position}]"
            if not isinstance(entry, dict):
                errors.append(f"{label} must be an object")
                continue
            identifier = entry.get("id")
            if not isinstance(identifier, str) or not identifier.strip():
                errors.append(f"{label} must have a nonempty string id")
            elif identifier in seen:
                errors.append(f"duplicate eval id: {identifier}")
            else:
                seen.add(identifier)
            if "command" in entry and collection == "evals":
                checks.append(entry)
                if not isinstance(entry["command"], str) or not entry["command"].strip():
                    errors.append(f"{label}.command must be a nonempty string")
                if type(entry.get("expect_exit")) is not int:
                    errors.append(f"{label}.expect_exit must be an integer (not boolean)")
                contains = entry.get("expect_contains", [])
                if not isinstance(contains, list) or any(not isinstance(value, str) for value in contains):
                    errors.append(f"{label}.expect_contains must be a list of strings")
            else:
                if "command" in entry:
                    errors.append(f"{label} is planned but declares a command")
                reason = (
                    "planned evaluation; not executed" if collection != "evals" else "no executable command declared"
                )
                planned.append({"eval": entry, "execution_status": "not-run", "reason": reason})
    if not checks:
        errors.append("manifest must declare at least one executable command")
    return checks, planned, errors


def _base_check(check: dict) -> dict:
    return {
        "id": check.get("id"),
        "command": check.get("command"),
        "expect_exit": check.get("expect_exit"),
        "expected_exit": check.get("expect_exit"),
        "expect_contains": check.get("expect_contains", []),
        "actual_exit": None,
        "exit_matched": False,
        "contains_checks": [],
        "executed": False,
        "passed": False,
        "status": "failed",
        "timed_out": False,
        "stdout": "",
        "stderr": "",
        "output_truncated": False,
        "error": None,
    }


def _bounded_read(stream) -> tuple[str, bool]:
    stream.seek(0)
    value = stream.read(OUTPUT_LIMIT + 1)
    return value[:OUTPUT_LIMIT].decode("utf-8", errors="replace"), len(value) > OUTPUT_LIMIT


def _stream_contains(stream, needle: str) -> bool:
    """Search the full stream without retaining unbounded output in memory."""
    if not needle:
        return True
    encoded = needle.encode("utf-8")
    stream.seek(0)
    tail = b""
    while chunk := stream.read(65536):
        value = tail + chunk
        if encoded in value:
            return True
        tail = value[-(len(encoded) - 1) :] if len(encoded) > 1 else b""
    return False


def _execute(check: dict, install: Path, timeout: float) -> dict:
    result = _base_check(check)
    started = time.monotonic()
    try:
        argv = command_argv(check["command"], install)
        result["argv"] = argv
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            process = subprocess.Popen(
                argv,
                cwd=install,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                shell=False,
                start_new_session=(os.name == "posix"),
            )
            result["executed"] = True
            try:
                result["actual_exit"] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                result["timed_out"] = True
                result["error"] = f"command exceeded {timeout:g} seconds"
                if os.name == "posix":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    process.kill()
                result["actual_exit"] = process.wait()
            result["exit_matched"] = result["actual_exit"] == check["expect_exit"]
            result["contains_checks"] = [
                {"value": value, "matched": _stream_contains(stdout, value) or _stream_contains(stderr, value)}
                for value in check.get("expect_contains", [])
            ]
            result["stdout"], out_truncated = _bounded_read(stdout)
            result["stderr"], err_truncated = _bounded_read(stderr)
            result["output_truncated"] = out_truncated or err_truncated
            result["passed"] = (
                not result["timed_out"]
                and result["exit_matched"]
                and all(item["matched"] for item in result["contains_checks"])
            )
    except (OSError, ValueError) as error:
        result["error"] = f"{type(error).__name__}: {error}"
    result["status"] = "passed" if result["passed"] else "failed"
    result["duration_seconds"] = round(time.monotonic() - started, 6)
    return result


def _hash_record(snapshot: dict) -> dict:
    return {"content_sha256": snapshot["content_sha256"], "files": snapshot["files"]}


def _execute_pinned(check: dict, install: Path, source: Path, expected: dict, timeout: float) -> dict:
    """Do not run the next command against files changed by an earlier command."""
    result = _base_check(check)
    integrity = {}
    try:
        for location, path in (("copy", install), ("source", source)):
            actual = _hash_record(package_snapshot(path))
            integrity[f"{location}_content_sha256_before"] = actual["content_sha256"]
            if actual != expected:
                raise ValueError(f"{location} package changed before command execution")
        result = _execute(check, install, timeout)
        for location, path in (("copy", install), ("source", source)):
            actual = _hash_record(package_snapshot(path))
            integrity[f"{location}_content_sha256_after"] = actual["content_sha256"]
            if actual != expected:
                raise ValueError(f"{location} package mutated during command execution")
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["error"] = f"{type(error).__name__}: {error}"
        result["passed"] = False
        result["status"] = "failed"
    result.update(integrity)
    return result


def run_package(root: Path, pinned: dict, timeout: float) -> dict:
    """Execute one package and retain evidence of every integrity comparison."""
    result = {
        "name": pinned.get("name"),
        "path": pinned.get("path"),
        "content_sha256": pinned.get("content_sha256"),
        "checks": [],
        "planned_unexecuted": [],
        "checks_manifest_sha256": None,
        "checks_manifest_file_sha256": pinned.get("files", {}).get(MANIFEST),
        "source_before": None,
        "source_after": None,
        "copy_before": None,
        "copy_after": None,
        "software_checks_passed": False,
        "errors": [],
    }
    source = None
    try:
        source = root / _relative_path(pinned["path"])
        if source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
            raise ValueError("source package escapes the repository")
        expected = _hash_record(pinned)
        result["source_before"] = _hash_record(package_snapshot(source))
        if result["source_before"] != expected:
            raise ValueError("source package does not match pinned snapshot before copying")
        with tempfile.TemporaryDirectory(prefix="insurance-portable-") as temporary:
            install = Path(temporary) / "install"
            shutil.copytree(source, install, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
            result["copy_before"] = _hash_record(package_snapshot(install))
            if result["copy_before"] != expected:
                raise ValueError("installed copy does not match pinned snapshot")
            manifest = json.loads((install / MANIFEST).read_text(encoding="utf-8"))
            result["checks_manifest_sha256"] = stable_hash(manifest)
            if (
                pinned.get("checks_manifest_sha256", result["checks_manifest_sha256"])
                != result["checks_manifest_sha256"]
            ):
                raise ValueError("check manifest does not match pinned manifest hash")
            checks, planned, errors = _manifest_entries(manifest)
            result["planned_unexecuted"] = planned
            result["errors"].extend(errors)
            for check in checks:
                if errors:
                    record = _base_check(check)
                    record["error"] = "invalid eval manifest; command not executed"
                else:
                    record = _execute_pinned(check, install, source, expected, timeout)
                result["checks"].append(record)
            result["copy_after"] = _hash_record(package_snapshot(install))
            if result["copy_after"] != expected:
                result["errors"].append("installed package mutated during execution")
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["errors"].append(f"{type(error).__name__}: {error}")
    finally:
        if source is not None:
            try:
                result["source_after"] = _hash_record(package_snapshot(source))
                if result["source_after"] != _hash_record(pinned):
                    result["errors"].append("source package changed during execution")
            except (OSError, ValueError, KeyError, TypeError) as error:
                result["errors"].append(f"source after check failed: {error}")
    result["software_checks_passed"] = (
        bool(result["checks"]) and not result["errors"] and all(check["passed"] for check in result["checks"])
    )
    return result


def run_portfolio(root: Path, snapshot: dict, workers: int = 4, timeout: float = 60) -> dict:
    """Run exactly the scoped portfolio pinned by insurance_readiness_lib."""
    if type(workers) is not int or not 1 <= workers <= 8:
        raise ValueError("workers must be an integer from 1 to 8")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or not 0 < timeout <= 60
    ):
        raise ValueError("timeout must be greater than zero and at most 60 seconds")
    root = Path(root).resolve()
    report = {
        "schema_version": "portable-insurance/1.0",
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "source_snapshot_sha256_before": None,
        "source_snapshot_sha256_after": None,
        "software_checks_passed": False,
        "packages": [],
        "errors": [],
        "institution_acceptance": "not-established",
        "action_taken": False,
        "workers": workers,
        "timeout_seconds": timeout,
        "isolation": "temporary package copy; no repository siblings; not a security sandbox",
    }
    try:
        current = portfolio_snapshot(root)
        report["source_snapshot_sha256_before"] = current["snapshot_sha256"]
        if current != snapshot:
            raise ValueError("source portfolio does not match the supplied pinned snapshot")
        if not isinstance(snapshot.get("packages"), list) or not snapshot["packages"]:
            raise ValueError("snapshot must contain a nonempty package list")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # executor.map preserves snapshot order while installations run independently.
            report["packages"] = list(
                executor.map(lambda package: run_package(root, package, timeout), snapshot["packages"])
            )
    except (OSError, ValueError, KeyError, TypeError) as error:
        report["errors"].append(f"{type(error).__name__}: {error}")
    finally:
        try:
            after = portfolio_snapshot(root)
            report["source_snapshot_sha256_after"] = after["snapshot_sha256"]
            if after != snapshot:
                report["errors"].append("source portfolio changed from the pinned snapshot")
        except (OSError, ValueError, KeyError, TypeError) as error:
            report["errors"].append(f"source portfolio after check failed: {error}")
    checks = [check for package in report["packages"] for check in package["checks"]]
    report["command_count"] = len(checks)
    report["executed_count"] = sum(check["executed"] for check in checks)
    report["passed_count"] = sum(check["passed"] for check in checks)
    report["failed_count"] = len(checks) - report["passed_count"]
    report["planned_unexecuted_count"] = sum(len(package["planned_unexecuted"]) for package in report["packages"])
    report["software_checks_passed"] = (
        bool(report["packages"])
        and not report["errors"]
        and all(package["software_checks_passed"] for package in report["packages"])
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO)
    parser.add_argument("--output", type=Path, required=True, help="new JSON report file; overwrites are refused")
    parser.add_argument("--workers", type=int, choices=range(1, 9), default=4)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= 60:
        parser.error("--timeout must be greater than zero and at most 60 seconds")
    if os.path.lexists(args.output):
        parser.error("--output already exists; choose a new report file")
    if not args.output.parent.is_dir():
        parser.error("--output parent directory must already exist")
    try:
        snapshot = portfolio_snapshot(args.root.resolve())
        report = run_portfolio(args.root, snapshot, workers=args.workers, timeout=args.timeout)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"portable runner failed: {error}", file=sys.stderr)
        return 1
    print(f"{report['passed_count']}/{report['command_count']} commands passed; report: {args.output}")
    return 0 if report["software_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
