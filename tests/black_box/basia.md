# Unit testy czarnoskrzynkowe — Basia

**Funkcjonalność:** rozpoznawanie składników i przeliczanie jednostek
**Pliki źródłowe:**
- `mealie/services/parser_services/brute/process.py`
- `mealie/services/parser_services/parser_utils/string_utils.py`
- `mealie/services/parser_services/parser_utils/unit_utils.py`

**Plik z testami:** `tests/black_box/test_basia.py`

Mealie zamienia tekst składnika (np. „2 1/2 cup flour”) na ilość, jednostkę i produkt. Na tej podstawie skaluje przepisy i łączy te same produkty na liście zakupów (np. 1 cup + 2 tbsp mąki → jedna pozycja).

## Funkcje do przetestowania (5)

| # | Funkcja | Plik | Rola w systemie |
|---|---|---|---|
| 1 | `parse_amount(ing_str) -> tuple[float, str, str]` | `brute/process.py` | Wyciąga ilość i jednostkę z tekstu składnika |
| 2 | `extract_quantity_from_string(source_str: str) -> tuple[float, str]` | `string_utils.py` | Odczytuje ilość z tekstu (liczby, ułamki, liczby mieszane) |
| 3 | `UnitConverter.can_convert(unit, to_unit) -> bool` | `unit_utils.py` | Czy dwie jednostki są ze sobą zgodne |
| 4 | `UnitConverter.convert(quantity: float, unit, to_unit) -> tuple[float, Unit]` | `unit_utils.py` | Przeliczanie ilości na inną jednostkę |
| 5 | `UnitConverter.merge(quantity_1, unit_1, quantity_2, unit_2) -> tuple[float, Unit]` | `unit_utils.py` | Łączenie dwóch ilości (lista zakupów) |

## Co zrobić

1. Dla każdej funkcji przygotuj **3–5 przypadków testowych** na podstawie samego wejścia i wyjścia:
   - poprawne dane (liczba całkowita, ułamek `1/2`, liczba mieszana `1 1/2`, typowe jednostki),
   - przypadki brzegowe (0, pusty string, tekst bez ilości),
   - niepoprawne dane (nieznana jednostka, jednostki nieprzeliczalne np. gram → litr).
2. Wpisz przypadki do tabeli poniżej (ta tabela idzie do dokumentacji).
3. Zaimplementuj testy w `tests/black_box/test_basia.py` w `pytest` (`@pytest.mark.parametrize`, ID przypadku jako `id=`). Floaty porównuj przez `pytest.approx`.
4. Uruchom: `uv run pytest tests/black_box/test_basia.py -v`
5. Uzupełnij kolumnę *Wynik* (`PASS` / `FAIL` + opis rozbieżności).
6. Własny branch (np. `tests/basia`) i PR do `mealie-next`.

## Przypadki testowe

| ID | Funkcja | Opis przypadku | Wejście | Oczekiwane wyjście | Typ | Wynik |
|---|---|---|---|---|---|---|
| B-01 | `parse_amount` | liczba całkowita + jednostka | `"2 cups flour"` | `(2.0, "cups", "flour")` | poprawne | FAIL — ilość OK, ale zwraca `unit="cups flour"`, `note=""` (jednostka nie oddzielona od reszty) |
| B-02 | `parse_amount` | ułamek | `"1/2 cup sugar"` | `(0.5, "cup", "sugar")` | poprawne | FAIL — ilość OK, `unit="cup sugar"`, `note=""` |
| B-03 | `parse_amount` | liczba dziesiętna | `"1.5 kg potatoes"` | `(1.5, "kg", "potatoes")` | poprawne | FAIL — ilość OK, `unit="kg potatoes"`, `note=""` |
| B-04 | `parse_amount` | tekst bez ilości | `"salt"` | `(0.0, "", "salt")` | brzegowe | FAIL — rzuca `ValueError` |
| B-05 | `parse_amount` | pusty string | `""` | `(0.0, "", "")` | brzegowe | FAIL — rzuca `IndexError` |
| B-06 | `extract_quantity_from_string` | liczba całkowita | `"2 cups"` | `(2, "cups")` | poprawne | PASS |
| B-07 | `extract_quantity_from_string` | ułamek | `"1/2 cup"` | `(0.5, "cup")` | poprawne | PASS |
| B-08 | `extract_quantity_from_string` | liczba mieszana | `"1 1/2 cup"` | `(1.5, "cup")` | poprawne | PASS |
| B-09 | `extract_quantity_from_string` | ułamek unicode | `"½ cup"` | `(0.5, "cup")` | poprawne | PASS |
| B-10 | `extract_quantity_from_string` | pusty string | `""` | `(0, "")` | brzegowe | PASS |
| B-11 | `extract_quantity_from_string` | tekst bez ilości | `"salt"` | `(0, "salt")` | brzegowe | PASS |
| B-12 | `can_convert` | objętość → objętość | `"cup", "milliliter"` | `True` | poprawne | PASS |
| B-13 | `can_convert` | masa → masa | `"gram", "kilogram"` | `True` | poprawne | PASS |
| B-14 | `can_convert` | ounce traktowane jako fl oz | `"ounce", "cup"` | `True` | brzegowe | PASS |
| B-15 | `can_convert` | masa → objętość | `"gram", "liter"` | `False` | niepoprawne | PASS |
| B-16 | `can_convert` | nieznana jednostka | `"foo", "gram"` | `False` | niepoprawne | PASS |
| B-17 | `convert` | kg → g | `1, "kilogram", "gram"` | `(1000, gram)` | poprawne | PASS |
| B-18 | `convert` | cup → ml | `1, "cup", "milliliter"` | `(≈236.588, milliliter)` | poprawne | PASS |
| B-19 | `convert` | ilość 0 | `0, "gram", "kilogram"` | `(0, kilogram)` | brzegowe | PASS |
| B-20 | `convert` | jednostki nieprzeliczalne | `1, "gram", "liter"` | `DimensionalityError` | niepoprawne | PASS |
| B-21 | `convert` | nieznana jednostka | `1, "foo", "gram"` | `UnitNotFound` | niepoprawne | PASS |
| B-22 | `merge` | 1 cup + 2 tbsp | `1, "cup", 2, "tablespoon"` | `(1.125, cup)` | poprawne | PASS |
| B-23 | `merge` | 500 g + 1 kg | `500, "gram", 1, "kilogram"` | `(1500, gram)` | poprawne | PASS |
| B-24 | `merge` | dodanie zera | `1, "cup", 0, "cup"` | `(1, cup)` | brzegowe | PASS |
| B-25 | `merge` | jednostki nieprzeliczalne | `1, "gram", 1, "liter"` | `DimensionalityError` | niepoprawne | PASS |
| B-26 | `merge` | nieznana jednostka | `1, "foo", 1, "gram"` | `UnitNotFound` | niepoprawne | PASS |

**Podsumowanie:** 26 przypadków, 21 PASS, 5 FAIL. Wszystkie błędy dotyczą `parse_amount`: nie oddziela jednostki od nazwy produktu i nie obsługuje tekstu bez ilości ani pustego stringa (rzuca wyjątki zamiast zwrócić ilość 0).
