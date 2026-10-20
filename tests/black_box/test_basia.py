import pytest
from pint.errors import DimensionalityError

from mealie.services.parser_services.brute.process import parse_amount
from mealie.services.parser_services.parser_utils.string_utils import extract_quantity_from_string
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
    "source, expected",
    [
        pytest.param("2 cups", (2, "cups"), id="B-06"),
        pytest.param("1/2 cup", (0.5, "cup"), id="B-07"),
        pytest.param("1 1/2 cup", (1.5, "cup"), id="B-08"),
        pytest.param("½ cup", (0.5, "cup"), id="B-09"),
        pytest.param("", (0, ""), id="B-10"),
        pytest.param("salt", (0, "salt"), id="B-11"),
    ],
)
def test_extract_quantity_from_string(source, expected):
    qty, rest = extract_quantity_from_string(source)
    assert qty == pytest.approx(expected[0])
    assert rest.strip() == expected[1]


@pytest.mark.parametrize(
    "unit, to_unit, expected",
    [
        pytest.param("cup", "milliliter", True, id="B-12"),
        pytest.param("gram", "kilogram", True, id="B-13"),
        pytest.param("ounce", "cup", True, id="B-14"),
        pytest.param("gram", "liter", False, id="B-15"),
        pytest.param("foo", "gram", False, id="B-16"),
    ],
)
def test_can_convert(unit, to_unit, expected):
    assert uc.can_convert(unit, to_unit) is expected


@pytest.mark.parametrize(
    "qty, unit, to_unit, expected",
    [
        pytest.param(1, "kilogram", "gram", 1000, id="B-17"),
        pytest.param(1, "cup", "milliliter", 236.588, id="B-18"),
        pytest.param(0, "gram", "kilogram", 0, id="B-19"),
    ],
)
def test_convert(qty, unit, to_unit, expected):
    value, out_unit = uc.convert(qty, unit, to_unit)
    assert value == pytest.approx(expected, rel=1e-3)
    assert str(out_unit) == to_unit


@pytest.mark.parametrize(
    "unit, to_unit, error",
    [
        pytest.param("gram", "liter", DimensionalityError, id="B-20"),
        pytest.param("foo", "gram", UnitNotFound, id="B-21"),
    ],
)
def test_convert_invalid(unit, to_unit, error):
    with pytest.raises(error):
        uc.convert(1, unit, to_unit)


@pytest.mark.parametrize(
    "q1, u1, q2, u2, expected_qty, expected_unit",
    [
        pytest.param(1, "cup", 2, "tablespoon", 1.125, "cup", id="B-22"),
        pytest.param(500, "gram", 1, "kilogram", 1500, "gram", id="B-23"),
        pytest.param(1, "cup", 0, "cup", 1, "cup", id="B-24"),
    ],
)
def test_merge(q1, u1, q2, u2, expected_qty, expected_unit):
    qty, unit = uc.merge(q1, u1, q2, u2)
    assert qty == pytest.approx(expected_qty)
    assert str(unit) == expected_unit


@pytest.mark.parametrize(
    "u1, u2, error",
    [
        pytest.param("gram", "liter", DimensionalityError, id="B-25"),
        pytest.param("foo", "gram", UnitNotFound, id="B-26"),
    ],
)
def test_merge_invalid(u1, u2, error):
    with pytest.raises(error):
        uc.merge(1, u1, 1, u2)
