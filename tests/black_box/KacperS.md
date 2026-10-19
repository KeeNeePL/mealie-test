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

| ID | Funkcja | Opis przypadku | Wejście | Oczekiwane wyjście | Typ | Wynik |
|---|---|---|---|---|---|---|
| KS-01 | | | | | | |
