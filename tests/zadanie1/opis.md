W pliku `number_converter_tester.py` przygotowano testy czarnoskrzynkowe
funkcji `convert_to_polish_name` z użyciem biblioteki `pytest`.

Sprawdzane są następujące przypadki:

- liczba `0`,
- liczby jednocyfrowe od `1` do `9`,
- wybrane liczby naście-: `10`, `14`, `15`, `16`, `19`,
- pełne dziesiątki oraz liczba złożona `21`,
- wybrane liczby setne: `100`, `101`, `200`, `300`, `500`,
- liczby tysięczne: `1000`, `1001`, `2000`, `5000`,
- większe liczby: `10000` i `100000`,
- maksymalna obsługiwana liczba `999999`,
- niepoprawne wartości spoza zakresu, czyli `-1` i `1000000`.

Dla poprawnych danych test porównuje zwróconą polską nazwę liczby
z oczekiwanym napisem. Dla wartości spoza zakresu sprawdza, czy funkcja
zgłasza wyjątek `ValueError`.