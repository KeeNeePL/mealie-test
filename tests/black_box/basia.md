# Unit testy czarnoskrzynkowe — Basia

**Funkcjonalność:** rozpoznawanie składników i przeliczanie jednostek
**Pliki źródłowe:**
- `mealie/services/parser_services/brute/process.py`
- `mealie/services/parser_services/parser_utils/string_utils.py`
- `mealie/services/parser_services/parser_utils/unit_utils.py`

**Plik z testami:** `tests/black_box/test_basia.py`

Mealie zamienia tekst składnika (np. „2 1/2 cup flour”) na ilość, jednostkę i produkt. Na tej podstawie skaluje przepisy i łączy te same produkty na liście zakupów (np. 1 cup + 2 tbsp mąki → jedna pozycja).

## Funkcje do przetestowania (3)

| # | Funkcja | Plik | Rola w systemie |
|---|---|---|---|
| 1 | `parse_amount(ing_str) -> tuple[float, str, str]` | `brute/process.py` | Wyciąga ilość i jednostkę z tekstu składnika |
| 3 | `UnitConverter.can_convert(unit, to_unit) -> bool` | `unit_utils.py` | Czy dwie jednostki są ze sobą zgodne |
| 4 | `UnitConverter.convert(quantity: float, unit, to_unit) -> tuple[float, Unit]` | `unit_utils.py` | Przeliczanie ilości na inną jednostkę |

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
| B-01 | | | | | | |
