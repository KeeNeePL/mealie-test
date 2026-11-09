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
| 2 | `UnitConverter.can_convert(unit, to_unit) -> bool` | `unit_utils.py` | Czy dwie jednostki są ze sobą zgodne |
| 3 | `UnitConverter.convert(quantity: float, unit, to_unit) -> tuple[float, Unit]` | `unit_utils.py` | Przeliczanie ilości na inną jednostkę |

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
| B-06 | `can_convert` | objętość → objętość | `"cup", "milliliter"` | `True` | poprawne | PASS |
| B-07 | `can_convert` | masa → masa | `"gram", "kilogram"` | `True` | poprawne | PASS |
| B-08 | `can_convert` | ounce traktowane jako fl oz | `"ounce", "cup"` | `True` | brzegowe | PASS |
| B-09 | `can_convert` | masa → objętość | `"gram", "liter"` | `False` | niepoprawne | PASS |
| B-10 | `can_convert` | nieznana jednostka | `"foo", "gram"` | `False` | niepoprawne | PASS |
| B-11 | `convert` | kg → g | `1, "kilogram", "gram"` | `(1000, gram)` | poprawne | PASS |
| B-12 | `convert` | cup → ml | `1, "cup", "milliliter"` | `(≈236.588, milliliter)` | poprawne | PASS |
| B-13 | `convert` | ilość 0 | `0, "gram", "kilogram"` | `(0, kilogram)` | brzegowe | PASS |
| B-14 | `convert` | jednostki nieprzeliczalne | `1, "gram", "liter"` | `DimensionalityError` | niepoprawne | PASS |
| B-15 | `convert` | nieznana jednostka | `1, "foo", "gram"` | `UnitNotFound` | niepoprawne | PASS |

**Podsumowanie:** 15 przypadków, 10 PASS, 5 FAIL. Wszystkie błędy dotyczą `parse_amount`: nie oddziela jednostki od nazwy produktu i nie obsługuje tekstu bez ilości ani pustego stringa (rzuca wyjątki zamiast zwrócić ilość 0).

## Pokrycie kodu (coverage.py)

**Poprawki testów:** nie były potrzebne, wszystkie 15 testów się uruchamia (5 FAIL to wykryte błędy, nie błędy testów). Nie dopisano nowych testów.

**Uruchomienie** (pokrycie dla każdego przypadku osobno przez `--cov-context=test` z `pytest-cov`):

```bash
uv run pytest tests/black_box/test_basia.py \
  --cov=mealie/services/parser_services/brute --cov=mealie/services/parser_services/parser_utils \
  --cov-context=test --cov-report=term-missing
```

### Osiągnięte pokrycie

| Funkcja | Pokryte linie | Pokrycie | Niewykonane linie |
|---|---|---|---|
| `parse_amount` | 21 / 28 | 75% | 67–68, 71, 76–77, 83–84 |
| `UnitConverter.can_convert` | 7 / 7 | 100% | — |
| `UnitConverter.convert` | 6 / 6 | 100% | — |
| `UnitConverter.parse` (pomocnicza) | 8 / 9 | 89% | 80 |
| `UnitConverter._resolve_ounce` (pomocnicza) | 7 / 8 | 88% | 59 |
| **Razem (5 funkcji)** | **49 / 58** | **84%** | |

Pokrycie całych plików jest niższe (`process.py` 36%, `unit_utils.py` 62%), bo zawierają też funkcje spoza zakresu testów.

### Przypadek z największym pokryciem

**B-01** (`"2 cups flour"`): 19 linii, czyli 68% `parse_amount`. Tyle samo pokrywają B-02 i B-03 (ta sama ścieżka, inna gałąź ułamek / liczba dziesiętna). Najmniej pokrywają B-04, B-05 (9 linii, bo kończą się wyjątkiem) i B-15 (8 linii).

### Niewykonane linie i brakujące przypadki

| Linie | Co nie zostało wykonane | Przypadek, który należałoby dodać |
|---|---|---|
| `process.py` 67–68, 71 | tekst zaczyna się od ułamka unicode | `parse_amount("½ cup sugar")` → ilość `0.5` |
| `process.py` 76–77 | liczba mieszana z ułamkiem unicode | `parse_amount("1½ cups flour")` → ilość `1.5` |
| `process.py` 83–84 | zakres / nawias po ilości (jednostka zaczyna się od `-` lub `(`) | `parse_amount("2-3 eggs")` → `unit=""`, `note="2-3 eggs"` |
| `unit_utils.py` 59 | ounce jako **druga** jednostka obok objętości | `can_convert("cup", "ounce")` → `True` |
| `unit_utils.py` 80 | wejście jest już obiektem `pint.Unit` | `convert(1, ureg.kilogram, "gram")` → `1000` |

Sprawdzono poza zestawem testów, że te wejścia wykonują wskazane linie.

### Wnioski

- Funkcje `can_convert` i `convert` są pokryte w 100%, a wszystkie ich testy przechodzą, więc przeliczanie jednostek jest dobrze sprawdzone.
- `parse_amount` ma najniższe pokrycie (75%) i wszystkie 5 błędów. Przypadki projektowane czarnoskrzynkowo (z sygnatury) nie trafiły w ułamki unicode i zakresy typu `2-3`, które obsługuje kod.
- Wysokie pokrycie nie oznacza poprawności: B-01..B-03 wykonują 68% `parse_amount`, a mimo to wykazały błąd w wyniku. Coverage pokazuje, czego nie sprawdzono, a nie że kod działa.
- Dodanie 5 przypadków z tabeli wyżej dałoby 100% pokrycia linii testowanych funkcji.
