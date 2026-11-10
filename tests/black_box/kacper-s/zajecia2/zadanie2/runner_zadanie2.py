"""
Runs the team's black-box test suite once and saves the results as JSON.

Usage (from anywhere inside the repository):
    python runner_zadanie2.py OUTPUT_DIR [--coverage]

Always writes:
    outcomes.json   - {test node id: {"outcome": "passed" | "failed" | "skipped", "message": str}}

With --coverage also writes (statement + branch coverage, one coverage context per test):
    coverage.json   - standard `coverage json` report (with per-function data)
    per_test.json   - {test node id: {source file: {"lines": [...], "arcs": [[from, to], ...]}}}
"""

import json
import re
import os
import sys
from pathlib import Path

# Python 3.12+ uses the `sysmon` core by default, which cannot record per-test contexts
os.environ.setdefault("COVERAGE_CORE", "ctrace")

import coverage  # noqa: E402
import pytest  # noqa: E402

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "mealie").is_dir())
sys.path.insert(0, str(ROOT))

# The whole team's black-box tests
TEST_PATHS = [
    "tests/black_box/kacper-s/zajecia1",  # KacperS: create_recipe_slug, combine_filters, from_date
    "tests/black_box/test_basia.py",  # Basia: parse_amount, UnitConverter.can_convert / convert
    "tests/black_box/kacper",  # KacperM: clean_image, clean_ingredients, clean_duration
]

# Source files that contain the tested functions
MEASURED = [
    "mealie/schema/recipe/recipe.py",
    "mealie/services/query_filter/builder.py",
    "mealie/schema/meal_plan/plan_rules.py",
    "mealie/services/parser_services/brute/process.py",
    "mealie/services/parser_services/parser_utils/unit_utils.py",
    "mealie/services/scraper/cleaner.py",
]


class ResultPlugin:
    """Collects the outcome (and failure message) of every test and switches coverage contexts."""

    def __init__(self, cov: coverage.Coverage | None):
        self.cov = cov
        self.results: dict[str, dict[str, str]] = {}

    def pytest_runtest_setup(self, item):
        if self.cov:
            self.cov.switch_context(item.nodeid)

    def pytest_runtest_teardown(self, item):
        if self.cov:
            self.cov.switch_context("")

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
            message = ""
            if report.failed:
                crash = getattr(report.longrepr, "reprcrash", None)
                message = crash.message if crash else str(report.longrepr)[-500:]
            elif report.skipped and isinstance(report.longrepr, tuple):
                message = report.longrepr[2]
            self.results[report.nodeid] = {"outcome": report.outcome, "message": message}


def main() -> int:
    out_dir = Path(sys.argv[1])
    with_coverage = "--coverage" in sys.argv[2:]
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(ROOT)

    cov = None
    if with_coverage:
        cov = coverage.Coverage(data_file=None, branch=True, include=[str(ROOT / m) for m in MEASURED], config_file=False)
        cov.start()

    plugin = ResultPlugin(cov)
    pytest.main([*TEST_PATHS, "--noconftest", "-q", "-p", "no:cacheprovider", "-W", "ignore"], plugins=[plugin])

    if cov:
        cov.stop()
        cov.json_report(outfile=str(out_dir / "coverage.json"), pretty_print=True)

        data = cov.get_data()
        per_test: dict[str, dict[str, dict[str, list]]] = {}
        for ctx in sorted(data.measured_contexts()):
            if not ctx:  # "" = import time / outside of tests
                continue
            data.set_query_contexts([f"^{re.escape(ctx)}$"])  # the argument is a regex
            for file in data.measured_files():
                lines = data.lines(file) or []
                if not lines:
                    continue
                rel = Path(file).resolve().relative_to(ROOT).as_posix()
                per_test.setdefault(ctx, {})[rel] = {"lines": sorted(lines), "arcs": sorted(data.arcs(file) or [])}
        data.set_query_contexts(None)
        (out_dir / "per_test.json").write_text(json.dumps(per_test), encoding="utf-8")

    (out_dir / "outcomes.json").write_text(json.dumps(plugin.results, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
