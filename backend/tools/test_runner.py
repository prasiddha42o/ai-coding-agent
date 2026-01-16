"""Detects and executes a repository's test suite (pytest / Jest / npm test).

Best-effort and deterministic — no LLM involved, this is mechanical tool
execution. It does not install the target repository's dependencies first
(auto-installing arbitrary third-party packages on every test run is its
own meaningful trust boundary, out of scope here) — if the runner or the
repo's own deps aren't already available in this environment, the run comes
back as an ERROR result with a clear explanation, not a silent false negative.
"""
import json
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from backend.core.config import get_settings
from backend.models.enums import TestRunner, TestStatus


@dataclass
class StackTraceEntry:
    test_name: str
    message: str
    trace: str | None = None


@dataclass
class TestRunResult:
    runner: TestRunner
    command: str
    status: TestStatus
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    duration_ms: int = 0
    output: str = ""
    stack_traces: list[StackTraceEntry] = field(default_factory=list)


def detect_runner(repo_root: Path, metadata: dict | None = None) -> TestRunner:
    package_json = repo_root / "package.json"
    if package_json.exists():
        try:
            package = json.loads(package_json.read_text(encoding="utf-8", errors="ignore"))
        except (json.JSONDecodeError, OSError):
            package = {}
        deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
        if "jest" in deps:
            return TestRunner.JEST
        if "test" in package.get("scripts", {}):
            return TestRunner.NPM

    has_pytest_files = (
        (repo_root / "pytest.ini").exists()
        or any(repo_root.glob("test_*.py"))
        or any(repo_root.glob("tests/**/*.py"))
        or any(repo_root.glob("**/test_*.py"))
    )
    if has_pytest_files or (metadata or {}).get("language") == "Python":
        return TestRunner.PYTEST

    return TestRunner.UNKNOWN


def run_tests(repo_root: Path, runner: TestRunner) -> TestRunResult:
    if runner == TestRunner.PYTEST:
        return _run_pytest(repo_root)
    if runner == TestRunner.JEST:
        return _run_jest(repo_root)
    if runner == TestRunner.NPM:
        return _run_npm_test(repo_root)
    return TestRunResult(
        runner=TestRunner.UNKNOWN,
        command="",
        status=TestStatus.SKIPPED,
        output="No supported test runner (pytest / Jest / npm test) was detected in this repository.",
    )


def _execute(command: list[str], cwd: Path) -> tuple[int, str, int]:
    settings = get_settings()
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=settings.command_timeout_seconds,
        )
        output = result.stdout + result.stderr
        returncode = result.returncode
    except FileNotFoundError:
        return 127, f"Command not found: {command[0]}", 0
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "") + "\n[test run timed out]"
        return 124, output, int((time.monotonic() - started) * 1000)
    return returncode, output, int((time.monotonic() - started) * 1000)


def _count(output: str, label: str) -> int:
    match = re.search(rf"(\d+) {label}", output)
    return int(match.group(1)) if match else 0


def _run_pytest(repo_root: Path) -> TestRunResult:
    if shutil.which("pytest"):
        command = ["pytest", "-q", "--tb=short"]
    elif shutil.which("python3"):
        command = ["python3", "-m", "pytest", "-q", "--tb=short"]
    else:
        return TestRunResult(
            runner=TestRunner.PYTEST,
            command="pytest",
            status=TestStatus.ERROR,
            output="Neither pytest nor python3 is available in this environment.",
        )

    returncode, output, duration_ms = _execute(command, repo_root)
    passed, failed = _count(output, "passed"), _count(output, "failed")
    skipped, errors = _count(output, "skipped"), _count(output, "error")

    if returncode == 5:  # pytest: no tests collected
        status = TestStatus.ERROR
    elif failed > 0 or errors > 0:
        status = TestStatus.FAILED
    elif returncode == 0:
        status = TestStatus.PASSED
    else:
        status = TestStatus.ERROR

    stack_traces = [
        StackTraceEntry(test_name=name, message=message.strip())
        for name, message in re.findall(r"^FAILED (\S+)(?: - (.*))?$", output, re.MULTILINE)
    ]

    return TestRunResult(
        runner=TestRunner.PYTEST,
        command=" ".join(command),
        status=status,
        passed_count=passed,
        failed_count=failed,
        skipped_count=skipped,
        duration_ms=duration_ms,
        output=output,
        stack_traces=stack_traces,
    )


def _run_jest(repo_root: Path) -> TestRunResult:
    if shutil.which("npx") is None:
        return TestRunResult(
            runner=TestRunner.JEST, command="npx jest", status=TestStatus.ERROR,
            output="npx is not available in this environment.",
        )

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        report_path = Path(tmp.name)

    command = ["npx", "--yes", "jest", "--json", f"--outputFile={report_path}"]
    returncode, output, duration_ms = _execute(command, repo_root)

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        report = None
    finally:
        report_path.unlink(missing_ok=True)

    if report is None:
        status = TestStatus.ERROR if returncode != 0 else TestStatus.PASSED
        return TestRunResult(
            runner=TestRunner.JEST, command=" ".join(command), status=status,
            duration_ms=duration_ms, output=output,
        )

    passed, failed, skipped = report.get("numPassedTests", 0), report.get("numFailedTests", 0), report.get("numPendingTests", 0)
    status = TestStatus.PASSED if report.get("success") else TestStatus.FAILED

    stack_traces = []
    for test_file in report.get("testResults", []):
        for assertion in test_file.get("assertionResults", []):
            if assertion.get("status") == "failed":
                stack_traces.append(
                    StackTraceEntry(
                        test_name=assertion.get("fullName", "unknown test"),
                        message="\n".join(assertion.get("failureMessages", []))[:2000],
                    )
                )

    return TestRunResult(
        runner=TestRunner.JEST,
        command=" ".join(command),
        status=status,
        passed_count=passed,
        failed_count=failed,
        skipped_count=skipped,
        duration_ms=duration_ms,
        output=output,
        stack_traces=stack_traces,
    )


def _run_npm_test(repo_root: Path) -> TestRunResult:
    if shutil.which("npm") is None:
        return TestRunResult(
            runner=TestRunner.NPM, command="npm test", status=TestStatus.ERROR,
            output="npm is not available in this environment.",
        )

    command = ["npm", "test", "--silent"]
    returncode, output, duration_ms = _execute(command, repo_root)
    # `npm test` delegates to an arbitrary script — no standard machine-readable
    # summary, so pass/fail is inferred from the exit code alone.
    status = TestStatus.PASSED if returncode == 0 else TestStatus.FAILED

    return TestRunResult(
        runner=TestRunner.NPM, command=" ".join(command), status=status,
        duration_ms=duration_ms, output=output,
    )
