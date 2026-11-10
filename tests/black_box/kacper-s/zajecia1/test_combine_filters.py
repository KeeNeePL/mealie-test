"""Black-box unit tests for QueryFilterBuilder.combine_filters (KacperS), cases KS-11 .. KS-19."""

import pytest
from fastapi import HTTPException

from mealie.services.query_filter.builder import QueryFilterBuilder

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
