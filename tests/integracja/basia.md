# Testy integracyjne

**Autor:** Barbara Dereń
**Data utworzenia:** 09.11.2026

## Wybrane elementy i punkty integracji

| Integracja | Elementy | Sposób komunikacji |
|---|---|---|
| I-1 | parser składników (`brute`) ↔ baza jednostek i produktów | parser zwraca tekst jednostki/produktu, `DataMatcher` dopasowuje go do rekordów w bazie |
| I-2 | lista zakupów (`ShoppingListService`) ↔ przeliczanie jednostek (`UnitConverter`, pint) ↔ baza | serwis pobiera jednostki z bazy, łączy pozycje przez `merge_quantity_and_unit` i zapisuje wynik |

**Konfiguracja testowa:** lokalny backend (Python 3.14.10, `PRODUCTION=False`), SQLite w katalogu tymczasowym, domyślny administrator `changeme@example.com`. Testy manualne wykonane przez zapytania HTTP do API (to samo, co wysyła interfejs).

**Wspólny stan początkowy:** w bazie są jednostki `cup`, `tablespoon`, `gram`, `liter` (każda z `standardUnit` = nazwa, `standardQuantity` = 1) i produkt `flour`. Użytkownik jest zalogowany.

---

## Scenariusz 1: „Rozpoznanie składnika i dopasowanie do bazy” (I-1)

### Przypadek 1a: poprawny tekst składnika (happy path)

**Warunek wstępny:** wspólny stan początkowy.
**Dane wejściowe:** `"2 cups flour"`, `"1/2 cup flour"`, parser `brute`.

| Nr | Krok | Oczekiwany rezultat | Rzeczywisty rezultat |
|---|---|---|---|
| 1 | `POST /api/parser/ingredient` z `"2 cups flour"` | HTTP 200, `quantity=2`, `unit` = jednostka `cup` z bazy (z `id`), `food` = `flour` z bazy (z `id`) | zgodny |
| 2 | `POST /api/parser/ingredient` z `"1/2 cup flour"` | HTTP 200, `quantity=0.5`, `unit` = `cup` z bazy, `food` = `flour` z bazy | zgodny |

**Gdzie obserwować integrację:** pola `ingredient.unit.id` i `ingredient.food.id` w odpowiedzi muszą być równe `id` rekordów z `GET /api/units` i `GET /api/foods`.
**Wynik:** PASS

### Przypadek 1b: tekst bez ilości i pusty tekst (błędne dane)

**Warunek wstępny:** wspólny stan początkowy.
**Dane wejściowe:** `"salt"`, `""`, parser `brute`.

| Nr | Krok | Oczekiwany rezultat | Rzeczywisty rezultat |
|---|---|---|---|
| 1 | `POST /api/parser/ingredient` z `"salt"` | HTTP 200, `quantity=0`, brak jednostki, `food` = `salt` bez `id` (brak w bazie) | zgodny |
| 2 | `POST /api/parser/ingredient` z `""` | HTTP 422 (błąd walidacji) albo pusty wynik | **HTTP 500 Internal Server Error**, w logu `IndexError` (zob. BR-01) |

**Gdzie obserwować integrację:** kod HTTP odpowiedzi, log serwera.
**Wynik:** FAIL (krok 2)

---

## Scenariusz 2: „Łączenie pozycji na liście zakupów” (I-2)

### Przypadek 2a: zgodne jednostki (happy path)

**Warunek wstępny:** wspólny stan początkowy, nowa pusta lista zakupów.
**Dane wejściowe:** `1 cup flour`, `2 tablespoon flour`.

| Nr | Krok | Oczekiwany rezultat | Rzeczywisty rezultat |
|---|---|---|---|
| 1 | `POST /api/households/shopping/lists` (`name="S2a"`) | HTTP 201, pusta lista | zgodny |
| 2 | `POST /api/households/shopping/items`: 1 × `cup`, `flour` | HTTP 201, pozycja w `createdItems` | zgodny |
| 3 | `POST /api/households/shopping/items`: 2 × `tablespoon`, `flour` | HTTP 201, nowa pozycja **nie** powstaje, istniejąca jest w `updatedItems` | zgodny |
| 4 | `GET /api/households/shopping/lists/{id}` | jedna pozycja: `1.125 cup flour` (1 cup + 2 tbsp = 1 + 0.125) | zgodny: `1.125 cup flour` |

**Gdzie obserwować integrację:** `updatedItems` w kroku 3 (serwis połączył pozycje), `quantity` i `unit` w kroku 4 (wynik przeliczenia przez pint zapisany w bazie).
**Wynik:** PASS

### Przypadek 2b: jednostki nieprzeliczalne

**Warunek wstępny:** wspólny stan początkowy, nowa pusta lista zakupów.
**Dane wejściowe:** `500 gram flour`, `1 liter flour`.

| Nr | Krok | Oczekiwany rezultat | Rzeczywisty rezultat |
|---|---|---|---|
| 1 | dodanie `500 gram flour`, potem `1 liter flour` | HTTP 201 dla obu, bez błędu | zgodny |
| 2 | `GET /api/households/shopping/lists/{id}` | dwie osobne pozycje (masy nie da się dodać do objętości) | zgodny: `500 gram flour`, `1 liter flour` |

**Wynik:** PASS

### Przypadek 2c: nieistniejąca jednostka (błędne dane między elementami)

**Warunek wstępny:** wspólny stan początkowy, nowa pusta lista zakupów.
**Dane wejściowe:** pozycja `1 flour` z losowym `unitId`, którego nie ma w bazie.

| Nr | Krok | Oczekiwany rezultat | Rzeczywisty rezultat |
|---|---|---|---|
| 1 | `POST /api/households/shopping/items` z nieistniejącym `unitId` | HTTP 404 lub 422, pozycja nie jest zapisana | **HTTP 201**, pozycja zapisana |
| 2 | `GET /api/households/shopping/lists/{id}` | brak pozycji | pozycja z `unitId` = nieistniejące id, `unit=null`, `display="1 flour"` (zob. BR-02) |

**Gdzie obserwować integrację:** `unitId` i `unit` pozycji porównane z `GET /api/units`.
**Wynik:** FAIL

---

## Zgłoszenia błędów

### BR-01: pusty składnik powoduje błąd 500 w parserze

| Pole | Opis |
|---|---|
| Komponent | `mealie/services/parser_services/brute/process.py` (`parse` → `parse_amount(tokens[0])`), wywoływany przez `POST /api/parser/ingredient` |
| Komunikacja | kontroler API przekazuje tekst do parsera bez walidacji; parser zakłada co najmniej jeden token |
| Dane / konfiguracja | `{"parser": "brute", "ingredient": ""}`, konfiguracja jak wyżej |
| Kroki | 1. Zaloguj się. 2. Wyślij `POST /api/parser/ingredient` z pustym `ingredient`. |
| Oczekiwane | HTTP 422 albo pusty wynik |
| Rzeczywiste | HTTP 500, w logu `IndexError: list index out of range` |
| Naprawa | walidacja `ingredient` jako niepustego tekstu w `IngredientRequest` albo zwracanie pustego wyniku w `parse` dla pustego tekstu |

Ten sam problem wykazał test jednostkowy B-05 (`parse_amount("")` → `IndexError`).

### BR-02: pozycja listy zakupów z nieistniejącą jednostką jest zapisywana

| Pole | Opis |
|---|---|
| Komponent | `ShoppingListService` / repozytorium pozycji listy zakupów + baza SQLite |
| Komunikacja | API przyjmuje `unitId` bez sprawdzenia, czy jednostka istnieje; SQLite nie wymusza klucza obcego |
| Dane / konfiguracja | `{"shoppingListId": <id>, "quantity": 1, "foodId": <flour>, "unitId": <losowy UUID>}`, baza SQLite |
| Kroki | 1. Utwórz listę. 2. Dodaj pozycję z losowym `unitId`. 3. Pobierz listę. |
| Oczekiwane | HTTP 404/422, brak zapisu |
| Rzeczywiste | HTTP 201, w bazie zostaje `unitId` wskazujące na nieistniejący rekord, jednostka po cichu znika z wyświetlania |
| Naprawa | sprawdzanie istnienia `unitId` / `foodId` w serwisie przed zapisem albo włączenie kluczy obcych w SQLite (`PRAGMA foreign_keys=ON`) |

## Wnioski

- Ścieżki happy path działają: parser poprawnie dopasowuje jednostki i produkty z bazy, a lista zakupów łączy pozycje z przeliczeniem jednostek (1 cup + 2 tbsp = 1.125 cup).
- Błędy pojawiają się na granicach elementów przy niepoprawnych danych: żaden z elementów nie waliduje danych przekazywanych do kolejnego (pusty tekst do parsera, nieistniejące `unitId` do bazy).
- Test jednostkowy B-01 (`parse_amount("2 cups flour")`) nie przechodził, a w integracji ten sam tekst jest rozpoznany poprawnie. Pełny parser dzieli tekst na słowa przed wywołaniem `parse_amount`, więc błąd z testu jednostkowego nie przenosi się na działanie systemu.
