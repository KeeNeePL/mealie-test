"""
Controlled code changes (mutants) for the team's tested functions, and a helper that applies one,
runs the whole test suite and ALWAYS restores the original source afterwards.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "mealie").is_dir())
RUNNER = Path(__file__).with_name("runner_zadanie2.py")

RECIPE = "mealie/schema/recipe/recipe.py"
BUILDER = "mealie/services/query_filter/builder.py"
PLAN_RULES = "mealie/schema/meal_plan/plan_rules.py"
PROCESS = "mealie/services/parser_services/brute/process.py"
UNITS = "mealie/services/parser_services/parser_utils/unit_utils.py"
CLEANER = "mealie/services/scraper/cleaner.py"


@dataclass(frozen=True)
class Mutant:
    id: str
    owner: str
    function: str
    file: str
    original: str  # exact source fragment; must occur exactly once in the file
    mutated: str
    description: str


MUTANTS: list[Mutant] = [
    # ---------------------------------------------------------------- KacperS: create_recipe_slug
    Mutant("M01", "KacperS", "create_recipe_slug", RECIPE,
           "    if len(generated_slug) > max_length:",
           "    if len(generated_slug) >= max_length:",
           "`>` → `>=` przy sprawdzaniu długości"),
    Mutant("M02", "KacperS", "create_recipe_slug", RECIPE,
           "        generated_slug = generated_slug[:max_length]",
           "        generated_slug = generated_slug[:max_length - 1]",
           "obcięcie o 1 znak za dużo (`max_length - 1`)"),
    Mutant("M03", "KacperS", "create_recipe_slug", RECIPE,
           "def create_recipe_slug(name: str, max_length: int = 250) -> str:",
           "def create_recipe_slug(name: str, max_length: int = 251) -> str:",
           "zmiana domyślnej wartości granicznej 250 → 251"),
    Mutant("M04", "KacperS", "create_recipe_slug", RECIPE,
           "    if not generated_slug:\n        raise SlugError",
           "    if generated_slug:\n        raise SlugError",
           "zanegowany warunek pustego sluga"),
    Mutant("M05", "KacperS", "create_recipe_slug", RECIPE,
           '        raise SlugError("Recipe name cannot be empty or contain only special characters")',
           '        return ""',
           "zamiast wyjątku zwracany pusty napis"),
    # ---------------------------------------------------------------- KacperS: combine_filters
    Mutant("M06", "KacperS", "combine_filters", BUILDER,
           "            if not filter_string:\n                continue",
           "            if filter_string is None:\n                continue",
           "pomijane tylko `None`, a nie pusty napis"),
    Mutant("M07", "KacperS", "combine_filters", BUILDER,
           "            if not filter_string:\n                continue",
           "            if not filter_string:\n                break",
           "`continue` → `break` (pierwszy pusty filtr kończy pętlę)"),
    Mutant("M08", "KacperS", "combine_filters", BUILDER,
           '        return " AND ".join(parts)',
           '        return " OR ".join(parts)',
           "`AND` → `OR` przy łączeniu filtrów"),
    Mutant("M09", "KacperS", "combine_filters", BUILDER,
           "                raise HTTPException(status_code=400, detail=str(e)) from e",
           "                raise HTTPException(status_code=500, detail=str(e)) from e",
           "kod błędu 400 → 500"),
    Mutant("M10", "KacperS", "combine_filters", BUILDER,
           '            parts.append(f"({filter_string})")',
           "            parts.append(filter_string)",
           "brak nawiasów wokół każdego filtra"),
    # ---------------------------------------------------------------- KacperS: from_date
    Mutant("M11", "KacperS", "from_date", PLAN_RULES,
           'return PlanRulesDay[(date.strftime("%A").lower())]',
           'return PlanRulesDay[(date.strftime("%a").lower())]',
           "pełna nazwa dnia `%A` → skrót `%a`"),
    Mutant("M12", "KacperS", "from_date", PLAN_RULES,
           "        except KeyError:\n            return PlanRulesDay.unset",
           "        except (KeyError, AttributeError):\n            return PlanRulesDay.unset",
           "szerszy `except` — błędny typ wejścia daje `unset` zamiast wyjątku"),
    Mutant("M13", "KacperS", "from_date", PLAN_RULES,
           "        except KeyError:\n            return PlanRulesDay.unset",
           "        except KeyError:\n            return None",
           "zmiana zwracanej wartości `unset` → `None`"),
    # ---------------------------------------------------------------- Basia: parse_amount
    Mutant("M14", "Basia", "parse_amount", PROCESS,
           "        if end >= len(ing_str):\n            return False",
           "        if end > len(ing_str):\n            return False",
           "`>=` → `>` w warunku końca napisu"),
    Mutant("M15", "Basia", "parse_amount", PROCESS,
           "    amount = 0.0\n    unit = \"\"\n    note = \"\"\n\n    did_check_frac = False",
           "    amount = 1.0\n    unit = \"\"\n    note = \"\"\n\n    did_check_frac = False",
           "wartość początkowa ilości 0.0 → 1.0"),
    Mutant("M16", "Basia", "parse_amount", PROCESS,
           '            amount = float(ing_str[:end].replace(",", "."))',
           "            amount = float(ing_str[:end])",
           "brak zamiany przecinka dziesiętnego na kropkę"),
    Mutant("M17", "Basia", "parse_amount", PROCESS,
           '    if unit.startswith("(") or unit.startswith("-"):',
           '    if unit.startswith("(") and unit.startswith("-"):',
           "`or` → `and` w warunku alternatywnej jednostki"),
    Mutant("M18", "Basia", "parse_amount", PROCESS,
           "    if end > 0:\n        if \"/\" in ing_str[:end]:",
           "    if end >= 0:\n        if \"/\" in ing_str[:end]:",
           "`>` → `>=` (napis bez liczby traktowany jak liczba)"),
    # ---------------------------------------------------------------- Basia: can_convert
    Mutant("M19", "Basia", "can_convert", UNITS,
           "        if not (isinstance(unit, Unit) and isinstance(to_unit, Unit)):\n            return False",
           "        if not (isinstance(unit, Unit) and isinstance(to_unit, Unit)):\n            return True",
           "nieznana jednostka: `False` → `True`"),
    Mutant("M20", "Basia", "can_convert", UNITS,
           "        if not (isinstance(unit, Unit) and isinstance(to_unit, Unit)):",
           "        if not (isinstance(unit, Unit) or isinstance(to_unit, Unit)):",
           "`and` → `or` przy sprawdzaniu, czy obie jednostki są znane"),
    Mutant("M21", "Basia", "can_convert", UNITS,
           "        unit, to_unit = self._resolve_ounce(unit, to_unit)\n        return unit.is_compatible_with(to_unit)",
           "        return unit.is_compatible_with(to_unit)",
           "usunięte rozpoznawanie uncji jako uncji objętości"),
    # ---------------------------------------------------------------- Basia: convert
    Mutant("M22", "Basia", "convert", UNITS,
           "        unit = self.parse(unit, strict=True)\n        to_unit = self.parse(to_unit, strict=True)\n        unit, to_unit = self._resolve_ounce(unit, to_unit)\n\n        qty",
           "        unit = self.parse(unit, strict=False)\n        to_unit = self.parse(to_unit, strict=True)\n        unit, to_unit = self._resolve_ounce(unit, to_unit)\n\n        qty",
           "`strict=True` → `False` dla jednostki źródłowej"),
    Mutant("M23", "Basia", "convert", UNITS,
           "        return float(converted.magnitude), converted.units",
           "        return int(converted.magnitude), converted.units",
           "`float` → `int` (utrata części ułamkowej)"),
    Mutant("M24", "Basia", "convert", UNITS,
           "        return float(converted.magnitude), converted.units",
           "        return float(converted.magnitude), to_unit",
           "zwracana jednostka docelowa zamiast jednostki wyniku"),
    Mutant("M25", "Basia", "convert", UNITS,
           "        qty = quantity * unit\n        converted",
           "        qty = abs(quantity) * unit\n        converted",
           "ilość brana z wartością bezwzględną"),
    # ---------------------------------------------------------------- KacperM: clean_image
    Mutant("M26", "KacperM", "clean_image", CLEANER,
           "    if not image:\n        return [default]",
           "    if image is None:\n        return [default]",
           "domyślny obrazek tylko dla `None`, a nie dla pustych wartości"),
    Mutant("M27", "KacperM", "clean_image", CLEANER,
           "            return [x for x in image if x]",
           "            return list(image)",
           "lista napisów bez odfiltrowania pustych wartości"),
    Mutant("M28", "KacperM", "clean_image", CLEANER,
           '            return [x["url"] for x in image if "url" in x]',
           '            return [x["url"] for x in image]',
           "brak sprawdzenia klucza `url` w każdym słowniku"),
    Mutant("M29", "KacperM", "clean_image", CLEANER,
           '            logger.exception(f"Unexpected type for image: {type(image)}, {image}")\n            return [default]',
           '            logger.exception(f"Unexpected type for image: {type(image)}, {image}")\n            return []',
           "nieobsługiwany typ: `[default]` → `[]`"),
    # ---------------------------------------------------------------- KacperM: clean_ingredients
    Mutant("M30", "KacperM", "clean_ingredients", CLEANER,
           "        case None:\n            return default or []",
           "        case None:\n            return default",
           "brak zamiany `None` na pustą listę"),
    Mutant("M31", "KacperM", "clean_ingredients", CLEANER,
           "                if isinstance(ing, dict):",
           "                if not isinstance(ing, dict):",
           "zanegowane sprawdzenie typu składnika"),
    Mutant("M32", "KacperM", "clean_ingredients", CLEANER,
           "ingredients.splitlines() if ingredient.strip()]",
           "ingredients.splitlines()]",
           "puste linie nie są odrzucane"),
    Mutant("M33", "KacperM", "clean_ingredients", CLEANER,
           "        case _:\n            raise TypeError(f\"Unexpected type for ingredients",
           "        case _:\n            return []\n            raise TypeError(f\"Unexpected type for ingredients",
           "nieobsługiwany typ: zamiast `TypeError` pusta lista"),
    # ---------------------------------------------------------------- KacperM: clean_duration
    Mutant("M34", "KacperM", "clean_duration", CLEANER,
           "            seconds = float(time_entry) * 60  # type: ignore",
           "            seconds = float(time_entry) * 61  # type: ignore",
           "mnożnik minut 60 → 61"),
    Mutant("M35", "KacperM", "clean_duration", CLEANER,
           "    if not 0 < seconds <= MAX_DURATION_SECONDS:",
           "    if not 0 <= seconds <= MAX_DURATION_SECONDS:",
           "`0 <` → `0 <=` (dolna granica)"),
    Mutant("M36", "KacperM", "clean_duration", CLEANER,
           "    if not 0 < seconds <= MAX_DURATION_SECONDS:",
           "    if not 0 < seconds < MAX_DURATION_SECONDS:",
           "`<=` → `<` (górna granica)"),
    Mutant("M37", "KacperM", "clean_duration", CLEANER,
           "        case bool():\n            return None\n",
           "",
           "usunięta obsługa wartości logicznych (`True` liczone jako 1 minuta)"),
    Mutant("M38", "KacperM", "clean_duration", CLEANER,
           "        case {\"minValue\": value}:\n            return clean_duration(value)",
           "        case {\"minValue\": value}:\n            return None",
           "zmiana zwracanej wartości dla `{\"minValue\": ...}`"),
]


@contextmanager
def applied(m: Mutant) -> Iterator[None]:
    """Puts the mutant into the source file and always restores the original bytes."""
    path = ROOT / m.file
    original = path.read_bytes()
    text = original.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"  
    old, new = m.original.replace("\n", newline), m.mutated.replace("\n", newline)
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{m.id}: fragment found {count} times in {m.file}, expected exactly 1")
    try:
        path.write_bytes(text.replace(old, new).encode("utf-8"))
        yield
    finally:
        path.write_bytes(original)
    if path.read_bytes() != original:
        raise RuntimeError(f"{m.id}: {m.file} was not restored!")


def run_suite(out_dir: Path, coverage: bool = False) -> dict:
    """Runs the whole suite in a fresh process (and a fresh bytecode cache, so the current source is used)."""
    env = {**os.environ, "PYTHONPYCACHEPREFIX": tempfile.mkdtemp(prefix="pyc_"), "PYTHONIOENCODING": "utf-8"}
    args = [sys.executable, str(RUNNER), str(out_dir)] + (["--coverage"] if coverage else [])
    proc = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    outcomes = out_dir / "outcomes.json"
    if not outcomes.exists():
        raise RuntimeError(proc.stdout[-3000:] + proc.stderr[-3000:])
    result = {"outcomes": json.loads(outcomes.read_text(encoding="utf-8"))}
    if coverage:
        result["cov"] = json.loads((out_dir / "coverage.json").read_text(encoding="utf-8"))
        result["per_test"] = json.loads((out_dir / "per_test.json").read_text(encoding="utf-8"))
    return result


def normalize(message: str) -> str:
    """Removes memory addresses (`at 0x7f...`), which differ between runs."""
    return re.sub(r"0x[0-9A-Fa-f]+", "0x…", message)


def compare(baseline: dict, mutant: dict) -> list[dict]:
    """Tests whose result differs from the baseline: PASS<->FAIL, or a FAIL with a different message."""
    changed = []
    for node, base in baseline.items():
        now = mutant.get(node, {"outcome": "missing", "message": ""})
        if base["outcome"] != now["outcome"]:
            kind = f"{base['outcome']} → {now['outcome']}"
        elif base["outcome"] == "failed" and normalize(base["message"]) != normalize(now["message"]):
            kind = "failed, inny komunikat"
        else:
            continue
        changed.append({"node": node, "kind": kind, "before": base["message"], "after": now["message"]})
    return changed


def git_diff_is_clean(files: list[str]) -> bool:
    proc = subprocess.run(["git", "diff", "--quiet", "--", *files], cwd=ROOT)
    return proc.returncode == 0
