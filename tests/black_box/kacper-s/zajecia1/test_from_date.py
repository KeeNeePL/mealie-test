"""Black-box unit tests for PlanRulesDay.from_date (KacperS), cases KS-20 .. KS-28."""

import datetime
import locale

import pytest

from mealie.schema.meal_plan.plan_rules import PlanRulesDay


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
