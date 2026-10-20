# Unit testy czarnoskrzynkowe — KacperS

**Funkcjonalność:** logowanie, adresy przepisów, wyszukiwanie i planer posiłków
**Pliki źródłowe:**
- `mealie/core/security/hasher.py`
- `mealie/core/security/tokens.py`
- `mealie/schema/recipe/recipe.py`
- `mealie/services/query_filter/builder.py`
- `mealie/schema/meal_plan/plan_rules.py`

**Plik z testami:** `tests/black_box/test_KacperS.py`

Użytkownik loguje się hasłem i dostaje token sesji. Każdy przepis ma własny adres (slug) tworzony z nazwy. Przepisy filtruje się zapytaniami (wyszukiwarka, książki kucharskie, reguły planera), a planer przypisuje posiłki do dni tygodnia.

## Funkcje do przetestowania (5)

| # | Funkcja | Plik | Rola w systemie |
|---|---|---|---|
| 1 | `Hasher.verify(password: str, hashed: str) -> bool` (hasher z `get_hasher()`, hash przez `Hasher.hash`) | `hasher.py` | Sprawdzanie hasła przy logowaniu |
| 2 | `create_access_token(data: dict, expires_delta: timedelta \| None = None) -> tuple[str, timedelta]` | `tokens.py` | Token sesji po zalogowaniu |
| 3 | `create_recipe_slug(name: str, max_length: int = 250) -> str` | `recipe.py` | Adres URL przepisu tworzony z nazwy |
| 4 | `QueryFilterBuilder.combine_filters(*filter_strings: str \| None) -> str` | `builder.py` | Łączenie filtrów wyszukiwania przepisów |
| 5 | `PlanRulesDay.from_date(date: datetime.date)` | `plan_rules.py` | Dzień tygodnia dla posiłku w planerze |

## Co zrobić

1. Dla każdej funkcji przygotuj **3–5 przypadków testowych** na podstawie samego wejścia i wyjścia:
   - poprawne dane (dobre hasło, zwykła nazwa przepisu, jeden / kilka filtrów, zwykła data),
   - przypadki brzegowe (pusta nazwa, nazwa dłuższa niż `max_length`, same `None` w filtrach, przełom roku),
   - niepoprawne dane (złe hasło, polskie znaki i znaki specjalne w nazwie, błędna składnia filtra).
2. Przy wynikach losowych (hash, token) testuj **właściwości** wyniku, a nie konkretną wartość (np. `verify(x, hash(x))` daje `True`, zwrócony czas ważności równa się podanemu).
3. Wpisz przypadki do tabeli poniżej (ta tabela idzie do dokumentacji).
4. Zaimplementuj testy w `tests/black_box/test_KacperS.py` w `pytest` (`@pytest.mark.parametrize`, ID przypadku jako `id=`).
5. Uruchom: `uv run pytest tests/black_box/test_KacperS.py -v`
6. Uzupełnij kolumnę *Wynik* (`PASS` / `FAIL` + opis rozbieżności).
7. Własny branch (np. `tests/KacperS`) i PR do `mealie-next`.

## Przypadki testowe

Zaimplementowane funkcje: #3 `create_recipe_slug`, #4 `combine_filters`, #5 `PlanRulesDay.from_date`.

| ID | Funkcja | Opis przypadku | Wejście | Oczekiwane wyjście | Typ | Wynik |
|---|---|---|---|---|---|---|
| KS-01 | `create_recipe_slug` | Zwykła nazwa | `"Pasta Fagioli"` | `"pasta-fagioli"` | poprawne | PASS |
| KS-02 | `create_recipe_slug` | Wielkie litery | `"SPAGHETTI Carbonara"` | `"spaghetti-carbonara"` | poprawne | PASS |
| KS-03 | `create_recipe_slug` | Nadmiarowe spacje | `"  Pasta    Fagioli  "` | `"pasta-fagioli"` | brzegowe | PASS |
| KS-04 | `create_recipe_slug` | Polskie znaki | `"Żurek łódzki z jajkiem"` | `"zurek-lodzki-z-jajkiem"` | niepoprawne | PASS |
| KS-05 | `create_recipe_slug` | Znaki specjalne | `"Chili!!! @ Home #1"` | `"chili-home-1"` | niepoprawne | PASS |
| KS-06 | `create_recipe_slug` | Nazwa dłuższa niż domyślne `max_length` | `"a" * 300` | długość ≤ 250, poprawny slug | brzegowe | PASS |
| KS-07 | `create_recipe_slug` | Własne `max_length` ucinające w środku nazwy | `"Spaghetti Carbonara z boczkiem"`, `max_length=10` | długość ≤ 10, bez myślnika na końcu, początek pełnego sluga | brzegowe | FAIL: zwraca `"spaghetti-"` (myślnik na końcu adresu) |
| KS-08 | `create_recipe_slug` | Slug o długości dokładnie `max_length` | `"b" * 250` | `"b" * 250` (bez ucinania) | brzegowe | PASS |
| KS-09 | `create_recipe_slug` | Pusta nazwa | `""` | `ValueError` (wg docstringa) | brzegowe | FAIL: rzuca `SlugError`, który nie dziedziczy po `ValueError` (niezgodność z docstringiem) |
| KS-10 | `create_recipe_slug` | Same znaki specjalne | `"!!! ??? ###"` | `ValueError` (wg docstringa) | niepoprawne | FAIL: jak w KS-09, rzuca `SlugError` zamiast `ValueError` |
| KS-11 | `combine_filters` | Jeden filtr | `'name = "Pasta Fagioli"'` | wynik zawiera filtr, brak `AND` | poprawne | PASS |
| KS-12 | `combine_filters` | Dwa filtry | filtr nazwy, filtr daty | oba filtry, jedno ` AND `, kolejność zachowana | poprawne | PASS |
| KS-13 | `combine_filters` | Trzy filtry (w tym `CONTAINS ALL`) | nazwa, data, tagi | trzy filtry, dwa ` AND `, kolejność zachowana | poprawne | PASS |
| KS-14 | `combine_filters` | Brak argumentów | `()` | `""` | brzegowe | PASS |
| KS-15 | `combine_filters` | Same `None` | `None, None, None` | `""` | brzegowe | PASS |
| KS-16 | `combine_filters` | Same puste napisy | `"", None, ""` | `""` | brzegowe | PASS |
| KS-17 | `combine_filters` | Puste części pomiędzy filtrami | `None, f1, "", f2, None` | to samo co `combine_filters(f1, f2)` | brzegowe | PASS |
| KS-18 | `combine_filters` | Filtr z `OR` łączony z innym | `'a OR b'`, `c` | `(a OR b)` zgrupowane w nawiasie + ` AND ` | poprawne | PASS |
| KS-19a | `combine_filters` | Brak wartości | `'name = "Pasta"'`, `'name ='` | `HTTPException` 4xx | niepoprawne | FAIL: rzuca `IndexError` (w API dałoby to błąd 500) |
| KS-19b | `combine_filters` | Niezamknięty nawias | `'(name = "Pasta"'` | `HTTPException` 4xx | niepoprawne | PASS |
| KS-19c | `combine_filters` | Brak operatora | `'name = "Pasta"'`, `'name "Pasta"'` | `HTTPException` 4xx | niepoprawne | FAIL: brak błędu, zwraca `'(name = "Pasta") AND (name "Pasta")'` |
| KS-20 | `from_date` | Zwykła data | `date(2026, 10, 19)` | `monday` | poprawne | PASS |
| KS-21 | `from_date` | Ostatni dzień roku | `date(2025, 12, 31)` | `wednesday` | brzegowe | PASS |
| KS-22 | `from_date` | Pierwszy dzień roku | `date(2026, 1, 1)` | `thursday` | brzegowe | PASS |
| KS-23 | `from_date` | 29 lutego (rok przestępny) | `date(2024, 2, 29)` | `thursday` | brzegowe | PASS |
| KS-24a | `from_date` | Najmniejsza możliwa data | `date.min` (0001-01-01) | `monday` | brzegowe | PASS |
| KS-24b | `from_date` | Największa możliwa data | `date.max` (9999-12-31) | `friday` | brzegowe | PASS |
| KS-25 | `from_date` | `datetime` późnym wieczorem | `datetime(2026, 10, 18, 23, 59, 59)` | `sunday` | brzegowe | PASS |
| KS-26 | `from_date` | Tydzień na przełomie roku | 7 kolejnych dni od 2026-12-28 | 7 różnych dni, żaden nie `unset` | brzegowe | PASS |
| KS-27a | `from_date` | `None` zamiast daty | `None` | `TypeError` / `AttributeError` | niepoprawne | PASS |
| KS-27b | `from_date` | Data jako napis | `"2026-10-19"` | `TypeError` / `AttributeError` | niepoprawne | PASS |
| KS-28 | `from_date` | Serwer z polskimi ustawieniami regionalnymi (`LC_TIME`) | `date(2026, 10, 19)` przy locale `pl_PL` | `monday` | niepoprawne | FAIL: zwraca `unset` (wynik zależy od języka systemu) |

**Podsumowanie:** 32 przypadki, 26 PASS, 6 FAIL.

**Uruchomienie lokalnie na Windowsie:** pakiet `python-ldap` wymaga kompilatora C++, więc bez niego `tests/conftest.py` (importuje całą aplikację) się nie załaduje. Te testy nie potrzebują fikstur z conftestu:

```bash
uv sync --no-install-package python-ldap
uv run --no-sync pytest tests/black_box/test_KacperS.py -v --noconftest
```
