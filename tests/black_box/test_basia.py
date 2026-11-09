import pytest
from pint.errors import DimensionalityError

from mealie.services.parser_services.brute.process import parse_amount
from mealie.services.parser_services.parser_utils.unit_utils import UnitConverter, UnitNotFound

uc = UnitConverter()


@pytest.mark.parametrize(
    "ing_str, expected",
    [
        pytest.param("2 cups flour", (2.0, "cups", "flour"), id="B-01"),
        pytest.param("1/2 cup sugar", (0.5, "cup", "sugar"), id="B-02"),
        pytest.param("1.5 kg potatoes", (1.5, "kg", "potatoes"), id="B-03"),
        pytest.param("salt", (0.0, "", "salt"), id="B-04"),
        pytest.param("", (0.0, "", ""), id="B-05"),
    ],
)
def test_parse_amount(ing_str, expected):
    amount, unit, note = parse_amount(ing_str)
    assert amount == pytest.approx(expected[0])
    assert (unit.strip(), note.strip()) == expected[1:]


@pytest.mark.parametrize(
    "unit, to_unit, expected",
    [
        pytest.param("cup", "milliliter", True, id="B-06"),
        pytest.param("gram", "kilogram", True, id="B-07"),
        pytest.param("ounce", "cup", True, id="B-08"),
        pytest.param("gram", "liter", False, id="B-09"),
        pytest.param("foo", "gram", False, id="B-10"),
    ],
)
def test_can_convert(unit, to_unit, expected):
    assert uc.can_convert(unit, to_unit) is expected


@pytest.mark.parametrize(
    "qty, unit, to_unit, expected",
    [
        pytest.param(1, "kilogram", "gram", 1000, id="B-11"),
        pytest.param(1, "cup", "milliliter", 236.588, id="B-12"),
        pytest.param(0, "gram", "kilogram", 0, id="B-13"),
    ],
)
def test_convert(qty, unit, to_unit, expected):
    value, out_unit = uc.convert(qty, unit, to_unit)
    assert value == pytest.approx(expected, rel=1e-3)
    assert str(out_unit) == to_unit


@pytest.mark.parametrize(
    "unit, to_unit, error",
    [
        pytest.param("gram", "liter", DimensionalityError, id="B-14"),
        pytest.param("foo", "gram", UnitNotFound, id="B-15"),
    ],
)
def test_convert_invalid(unit, to_unit, error):
    with pytest.raises(error):
        uc.convert(1, unit, to_unit)
