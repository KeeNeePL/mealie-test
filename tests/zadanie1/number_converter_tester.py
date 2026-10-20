import pytest

def convert_to_polish_name(number:int) -> str:
    pass

@pytest.mark.parametrize("number, expected", [
    (0, "zero"),
    (1, "jeden"),
    (2, "dwa"),
    (3, "trzy"),
    (4, "cztery"),
    (5, "pięć"),
    (6, "sześć"),
    (7, "siedem"),
    (8, "osiem"),
    (9, "dziewięć"),
    (10, "dziesięć"),
    (14, "czternaście"),
    (15, "piętnaście"),
    (16, "szesnaście"),
    (19, "dziewiętnaście"),
    (20, "dwadzieścia"),
    (21, "dwadzieścia jeden"),
    (30, "trzydzieści"),
    (40, "czterdzieści"),
    (50, "pięćdziesiąt"),
    (60, "sześćdziesiąt"),
    (90, "dziewięćdziesiąt"),
    (100, "sto"),
    (101, "sto jeden"),
    (200, "dwieście"),
    (300, "trzysta"),
    (500, "pięćset"),
    (1000, "tysiąc"),
    (1001, "tysiąc jeden"),
    (2000, "dwa tysiące"),
    (5000, "pięć tysięcy"),
    (10000, "dziesięć tysięcy"),
    (100000, "sto tysięcy"),
    (999999, "dziewięćset dziewięćdziesiąt dziewięć tysięcy dziewięćset dziewięćdziesiąt dziewięć")
    ],
)

def test_convert_valid_numbers(number, expected):
    assert convert_to_polish_name(number) == expected

@pytest.mark.parametrize("number", [-1, 1000000])
def test_convert_invalid_numbers(number):
    with pytest.raises(ValueError):
        convert_to_polish_name(number)