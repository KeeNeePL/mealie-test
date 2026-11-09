"""
Runs pytest under coverage.py and records WHICH test case executed WHICH line.

Usage (from the repository root):
    python tests/black_box/coverage_runner_zajecia2.py OUTPUT_DIR TEST_FILE [TEST_FILE ...]

Writes into OUTPUT_DIR:
    coverage.json   - standard `coverage json` report (line + branch, per function)
    contexts.json   - {test node id: {source file: [executed lines]}}
    outcomes.json   - {test node id: "passed" | "failed" | "skipped"}

Every test (also every parametrized case) gets its own coverage "context", so the per-case
contribution can be read back without running the tests one by one.
"""

import json
import os
import sys
from pathlib import Path

# Python 3.12+ uses the faster `sysmon` core by default, which cannot record per-test contexts
os.environ.setdefault("COVERAGE_CORE", "ctrace")

import coverage  # noqa: E402
import pytest  # noqa: E402

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "mealie").is_dir())
sys.path.insert(0, str(ROOT))

# Modules that contain the tested functions (and the parser they call internally)
MEASURED = [
    "mealie/schema/recipe/recipe.py",
    "mealie/schema/meal_plan/plan_rules.py",
    "mealie/services/query_filter/builder.py",
    "mealie/services/query_filter/keywords.py",
    "mealie/services/query_filter/operators.py",
]


class ContextPlugin:
    """Switches the coverage context to the node id of the currently running test."""

    def __init__(self, cov: coverage.Coverage):
        self.cov = cov
        self.outcomes: dict[str, str] = {}

    def pytest_runtest_setup(self, item):
        self.cov.switch_context(item.nodeid)

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
            self.outcomes[report.nodeid] = report.outcome

    def pytest_runtest_teardown(self, item):
        self.cov.switch_context("")


def main() -> int:
    out_dir = Path(sys.argv[1])
    test_files = sys.argv[2:]
    out_dir.mkdir(parents=True, exist_ok=True)

    cov = coverage.Coverage(
        data_file=None,
        branch=True,
        include=[str(ROOT / m) for m in MEASURED],
        config_file=False,
    )
    plugin = ContextPlugin(cov)
    cov.start()
    pytest.main([*test_files, "--noconftest", "-q", "-p", "no:cacheprovider"], plugins=[plugin])
    cov.stop()

    data = cov.get_data()
    cov.json_report(outfile=str(out_dir / "coverage.json"), pretty_print=True)

    contexts: dict[str, dict[str, list[int]]] = {}
    for file in data.measured_files():
        rel = Path(file).resolve().relative_to(ROOT).as_posix()
        for line, ctxs in data.contexts_by_lineno(file).items():
            for ctx in ctxs:
                if ctx:  # "" = import time / outside of tests
                    contexts.setdefault(ctx, {}).setdefault(rel, []).append(line)
    for per_file in contexts.values():
        for lines in per_file.values():
            lines.sort()

    (out_dir / "contexts.json").write_text(json.dumps(contexts, indent=1), encoding="utf-8")
    (out_dir / "outcomes.json").write_text(json.dumps(plugin.outcomes, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
