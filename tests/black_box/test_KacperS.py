"""
Black-box unit tests — KacperS.

Test cases are designed only from each function's signature, name and docstring
(see tests/black_box/KacperS.md). Tested functions:

- create_recipe_slug                    (KS-01 .. KS-10)
- QueryFilterBuilder.combine_filters    (KS-11 .. KS-19)
- PlanRulesDay.from_date                (KS-20 .. KS-28)
"""

import datetime
import locale
import re

import pytest
from fastapi import HTTPException

from mealie.schema.meal_plan.plan_rules import PlanRulesDay
from mealie.schema.recipe.recipe import create_recipe_slug
from mealie.services.query_filter.builder import QueryFilterBuilder

# A URL-safe slug: lowercase letters/digits separated by single hyphens, no hyphen at either end
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


# =====================================================================================
# create_recipe_slug(name: str, max_length: int = 250) -> str
# =====================================================================================


@pytest.mark.parametrize(
    "name, expected",
    [
        pytest.param("Pasta Fagioli", "pasta-fagioli", id="KS-01-ordinary-name"),
        pytest.param("SPAGHETTI Carbonara", "spaghetti-carbonara", id="KS-02-uppercase"),
        pytest.param("  Pasta    Fagioli  ", "pasta-fagioli", id="KS-03-extra-whitespace"),
        pytest.param("Żurek łódzki z jajkiem", "zurek-lodzki-z-jajkiem", id="KS-04-polish-characters"),
        pytest.param("Chili!!! @ Home #1", "chili-home-1", id="KS-05-special-characters"),
    ],
)
def test_create_recipe_slug_valid_names(name: str, expected: str):
    slug = create_recipe_slug(name)

    assert slug == expected
    assert SLUG_PATTERN.match(slug)


@pytest.mark.parametrize(
    "name, max_length",
    [
        pytest.param("a" * 300, 250, id="KS-06-longer-than-default-max-length"),
        pytest.param("Spaghetti Carbonara z boczkiem", 10, id="KS-07-custom-max-length"),
    ],
)
def test_create_recipe_slug_is_truncated(name: str, max_length: int):
    slug = create_recipe_slug(name, max_length=max_length)

    assert 0 < len(slug) <= max_length
    # truncation must not leave a dangling hyphen and must keep the start of the full slug
    assert SLUG_PATTERN.match(slug)
    assert create_recipe_slug(name, max_length=10_000).startswith(slug)


def test_create_recipe_slug_exactly_max_length_is_not_truncated():
    """KS-08: a name whose slug has exactly `max_length` characters stays unchanged."""
    name = "b" * 250

    assert create_recipe_slug(name) == name


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("", id="KS-09-empty-name"),
        pytest.param("!!! ??? ###", id="KS-10-only-special-characters"),
    ],
)
def test_create_recipe_slug_invalid_name_raises_value_error(name: str):
    with pytest.raises(ValueError):
        create_recipe_slug(name)


# =====================================================================================
# QueryFilterBuilder.combine_filters(*filter_strings: str | None) -> str
# =====================================================================================

FILTER_NAME = 'name = "Pasta Fagioli"'
FILTER_DATE = 'createdAt >= "2021-02-22"'
FILTER_TAGS = 'tags.name CONTAINS ALL ["Easy", "Cajun"]'
FILTER_OR = 'name = "Pasta Fagioli" OR name = "Grandma\'s Brisket"'


def test_combine_filters_single_filter():
    """KS-11: a single filter is returned (it is the only part of the result)."""
    result = QueryFilterBuilder.combine_filters(FILTER_NAME)

    assert FILTER_NAME in result
    assert "AND" not in result


@pytest.mark.parametrize(
    "filters",
    [
        pytest.param((FILTER_NAME, FILTER_DATE), id="KS-12-two-filters"),
        pytest.param((FILTER_NAME, FILTER_DATE, FILTER_TAGS), id="KS-13-three-filters"),
    ],
)
def test_combine_filters_joins_with_and(filters: tuple[str, ...]):
    result = QueryFilterBuilder.combine_filters(*filters)

    for f in filters:
        assert f in result
    assert result.count(" AND ") == len(filters) - 1
    # the order of the given filters is kept
    positions = [result.index(f) for f in filters]
    assert positions == sorted(positions)


@pytest.mark.parametrize(
    "filters",
    [
        pytest.param((), id="KS-14-no-arguments"),
        pytest.param((None, None, None), id="KS-15-only-none"),
        pytest.param(("", None, ""), id="KS-16-only-empty-strings"),
    ],
)
def test_combine_filters_only_empty_returns_empty_string(filters: tuple[str | None, ...]):
    assert QueryFilterBuilder.combine_filters(*filters) == ""


def test_combine_filters_ignores_empty_parts():
    """KS-17: None and "" between real filters are skipped — same result as without them."""
    with_empty = QueryFilterBuilder.combine_filters(None, FILTER_NAME, "", FILTER_DATE, None)
    without_empty = QueryFilterBuilder.combine_filters(FILTER_NAME, FILTER_DATE)

    assert with_empty == without_empty


def test_combine_filters_keeps_or_filter_grouped():
    """
    KS-18: combining `a OR b` with `c` must mean `(a OR b) AND c`.
    Without grouping, `a OR b AND c` would be read as `a OR (b AND c)`.
    """
    result = QueryFilterBuilder.combine_filters(FILTER_OR, FILTER_DATE)

    assert f"({FILTER_OR})" in result
    assert " AND " in result


@pytest.mark.parametrize(
    "filters",
    [
        pytest.param(('name = "Pasta"', "name ="), id="KS-19a-missing-value"),
        pytest.param(('(name = "Pasta"',), id="KS-19b-unbalanced-parenthesis"),
        pytest.param(('name = "Pasta"', 'name "Pasta"'), id="KS-19c-missing-operator"),
    ],
)
def test_combine_filters_invalid_syntax_raises_http_exception(filters: tuple[str, ...]):
    with pytest.raises(HTTPException) as exc_info:
        QueryFilterBuilder.combine_filters(*filters)

    assert 400 <= exc_info.value.status_code < 500


# =====================================================================================
# PlanRulesDay.from_date(date: datetime.date)
# =====================================================================================


@pytest.mark.parametrize(
    "date, expected",
    [
        pytest.param(datetime.date(2026, 10, 19), PlanRulesDay.monday, id="KS-20-ordinary-date"),
        pytest.param(datetime.date(2025, 12, 31), PlanRulesDay.wednesday, id="KS-21-last-day-of-year"),
        pytest.param(datetime.date(2026, 1, 1), PlanRulesDay.thursday, id="KS-22-first-day-of-year"),
        pytest.param(datetime.date(2024, 2, 29), PlanRulesDay.thursday, id="KS-23-leap-day"),
        pytest.param(datetime.date.min, PlanRulesDay.monday, id="KS-24a-min-date"),
        pytest.param(datetime.date.max, PlanRulesDay.friday, id="KS-24b-max-date"),
        pytest.param(
            datetime.datetime(2026, 10, 18, 23, 59, 59, tzinfo=datetime.UTC),
            PlanRulesDay.sunday,
            id="KS-25-datetime-late-evening",
        ),
    ],
)
def test_from_date_returns_weekday(date: datetime.date, expected: PlanRulesDay):
    assert PlanRulesDay.from_date(date) == expected


def test_from_date_full_week_gives_seven_distinct_days():
    """KS-26: 7 consecutive days map to 7 different days, never `unset`."""
    start = datetime.date(2026, 12, 28)  # a week that crosses the new year
    days = [PlanRulesDay.from_date(start + datetime.timedelta(days=i)) for i in range(7)]

    assert len(set(days)) == 7
    assert PlanRulesDay.unset not in days


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(None, id="KS-27a-none"),
        pytest.param("2026-10-19", id="KS-27b-date-as-string"),
    ],
)
def test_from_date_invalid_input_raises(value):
    with pytest.raises((TypeError, AttributeError)):
        PlanRulesDay.from_date(value)  # type: ignore[arg-type]


def _set_polish_time_locale() -> str:
    for name in ("pl_PL.UTF-8", "pl_PL.utf8", "pl_PL", "Polish_Poland.1250", "Polish"):
        try:
            return locale.setlocale(locale.LC_TIME, name)
        except locale.Error:
            continue
    pytest.skip("Polish locale is not available on this machine")


def test_from_date_does_not_depend_on_system_locale():
    """
    KS-28: the server can run with a Polish system locale; a Monday must still be `monday`.
    """
    original = locale.setlocale(locale.LC_TIME)
    try:
        _set_polish_time_locale()
        result = PlanRulesDay.from_date(datetime.date(2026, 10, 19))
    finally:
        locale.setlocale(locale.LC_TIME, original)

    assert result == PlanRulesDay.monday
