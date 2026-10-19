# Unit testy czarnoskrzynkowe — KacperM

**Funkcjonalność:** import przepisu z adresu URL
**Plik źródłowy:** `mealie/services/scraper/cleaner.py`
**Plik z testami:** `tests/black_box/test_kacperM.py`

Użytkownik wkleja link do przepisu, a Mealie pobiera dane ze strony i zamienia je na przepis. Dane ze stron przychodzą w bardzo różnych formatach (string, lista, słownik, puste wartości), więc te funkcje muszą je ujednolicić.

## Funkcje do przetestowania (5)

| # | Funkcja | Co odpowiada za w przepisie |
|---|---|---|
| 1 | `clean_ingredients(ingredients: list \| str \| None, default: list \| None = None) -> list[str \| dict]` | Lista składników |
| 2 | `clean_instructions(steps_object: list \| dict \| str, default: list \| None = None) -> list[dict]` | Kroki przygotowania |
| 3 | `clean_yield(yields: str \| list[str] \| None) -> tuple[float, float, str]` | Liczba porcji / wydajność |
| 4 | `clean_duration(time_entry: Any) -> int \| None` | Czas przygotowania |
| 5 | `clean_image(image: str \| list \| dict \| None = None, default: str = NO_IMAGE) -> list[str]` | Zdjęcie przepisu |

## Co zrobić

1. Dla każdej funkcji przygotuj **3–5 przypadków testowych** na podstawie samego wejścia i wyjścia:
   - poprawne dane (typowy przepis ze strony),
   - przypadki brzegowe (pusta lista, pusty string, `None`),
   - nietypowe dane (inny typ niż zwykle, np. słownik zamiast listy, tekst bez liczb).
2. Wpisz przypadki do tabeli poniżej (ta tabela idzie do dokumentacji).
3. Zaimplementuj testy w `tests/black_box/test_kacperM.py` w `pytest` (`@pytest.mark.parametrize`, ID przypadku jako `id=`).
4. Uruchom: `uv run pytest tests/black_box/test_kacperM.py -v`
5. Uzupełnij kolumnę *Wynik* (`PASS` / `FAIL` + opis rozbieżności).
6. Własny branch (np. `tests/kacperM`) i PR do `mealie-next`.

## Przypadki testowe

| ID | Funkcja | Opis przypadku | Wejście | Oczekiwane wyjście | Typ | Wynik |
|---|---|---|---|---|---|---|
| KM-01 | | | | | | |
