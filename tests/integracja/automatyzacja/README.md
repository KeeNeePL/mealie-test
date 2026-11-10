# Zadanie 2: automatyzacja testów integracyjnych (Wariant A)

**Autor:** Kacper M.
**Data:** 09.11.2026
**Podstawa:** scenariusze z Zadania 1, [`tests/integracja/basia.md`](../basia.md)
**Plik z testami:** [`test_integracja_automatyczna.py`](test_integracja_automatyczna.py)

## Wybór wariantu i uzasadnienie

Wybraliśmy **Wariant A: automatyzację testu integracyjnego**, bo badany system ma do tego gotowe warunki:

- Backend Mealie to aplikacja FastAPI. `TestClient` wysyła do niej prawdziwe zapytania HTTP w tym samym procesie, więc test przechodzi tę samą drogę co interfejs: kontroler → serwis → repozytorium → baza.
- Projekt ma gotowe środowisko testowe (`tests/conftest.py`). Każde uruchomienie dostaje nową, tymczasową bazę SQLite w `tests/.temp`, a fixture `unique_user_fn_scoped` tworzy dla każdego testu nowego użytkownika z własną, pustą grupą. Dzięki temu testy są od siebie odizolowane i można je powtarzać.
- Scenariusze z Zadania 1 były wykonywane ręcznie przez API, więc każdy krok da się zamienić na wywołanie HTTP z asercją. Nie trzeba niczego klikać w przeglądarce.

## Co sprawdzamy

Sprawdzamy, czy **dwa lub więcej elementów systemu poprawnie przekazują sobie dane**, a nie czy pojedyncza funkcja działa (to był zakres testów czarnoskrzynkowych).

### Integracja I-1: parser składników ↔ baza jednostek i produktów

Użytkownik wpisuje składnik jako tekst, np. `"2 cups flour"`. Parser `brute` dzieli go na ilość (`2`), jednostkę (`cups`) i produkt (`flour`). Potem `DataMatcher` szuka w bazie jednostki i produktu, które pasują do tych słów.

**Punkt obserwacji:** `id` jednostki i produktu w odpowiedzi parsera musi być równe `id` rekordów, które test wcześniej zapisał w bazie. Jeśli są równe, to parser i baza naprawdę się „dogadały”: tekst został zamieniony na konkretne rekordy, a nie tylko na napisy.

### Integracja I-2: lista zakupów ↔ przeliczanie jednostek ↔ baza

Gdy na listę zakupów trafia drugi raz ten sam produkt, `ShoppingListService` sprawdza, czy pozycje da się połączyć. Pobiera jednostki z bazy, prosi `UnitConverter` (biblioteka pint) o przeliczenie i zapisuje połączoną pozycję.

**Punkt obserwacji:** pola `createdItems` i `updatedItems` w odpowiedzi (czy serwis utworzył nową pozycję, czy zaktualizował istniejącą) oraz `quantity` i `unitId` pozycji odczytanej z bazy po operacji.

## Przypadki testowe

| ID | Test | Dane wejściowe | Oczekiwany wynik | Wynik |
|---|---|---|---|---|
| 1a-krok1 | `test_1a_parser_dopasowuje_jednostke_i_produkt_z_bazy` | `"2 cups flour"` | 200, `quantity = 2`, `unit.id` = id `cup` z bazy, `food.id` = id `flour` z bazy | PASS |
| 1a-krok2 | j.w. | `"1/2 cup flour"` | 200, `quantity = 0.5`, ta sama jednostka i produkt z bazy | PASS |
| 1b-krok1 | `test_1b_krok1_produkt_spoza_bazy_nie_dostaje_id` | `"salt"` | 200, brak ilości i jednostki, `food.name = "salt"`, brak `food.id` (nie ma go w bazie) | PASS |
| 1b-krok2 | `test_1b_krok2_pusty_tekst_zwraca_blad_walidacji` | `""` | 422 (błąd walidacji) | **XFAIL (BR-01)**: otrzymano 500 |
| 2a | `test_2a_zgodne_jednostki_sa_laczone_z_przeliczeniem` | 1 cup flour + 2 tablespoon flour | druga pozycja nie powstaje (`updatedItems`), na liście 1 pozycja: **1.125 cup** | PASS |
| 2b | `test_2b_jednostki_nieprzeliczalne_daja_osobne_pozycje` | 500 gram flour + 1 liter flour | 2 osobne pozycje (masy nie da się dodać do objętości) | PASS |
| 2c | `test_2c_nieistniejaca_jednostka_jest_odrzucana` | 1 flour z losowym `unitId` | 404/422, pozycja nie jest zapisana | **XFAIL (BR-02)**: otrzymano 201 |

### Jak test spełnia wymagania polecenia

| Wymaganie | Realizacja w kodzie |
|---|---|
| Przygotowuje wymagany stan | fixture `stan`: nowy użytkownik (nowa grupa), przez API tworzy jednostki `cup`, `tablespoon`, `gram`, `liter` (`standardUnit` = nazwa, `standardQuantity` = 1) i produkt `flour`. Testy z listą zakupów tworzą nową pustą listę (`nowa_lista`). |
| Sprawdza rezultat integracji | porównanie `id` zwróconych przez parser z `id` z bazy (I-1), odczyt listy z bazy po połączeniu pozycji (I-2) |
| Jednoznaczne asercje | konkretne kody HTTP, konkretne `id`, `quantity == pytest.approx(1.125)`, dokładna liczba pozycji |
| Da się uruchomić ponownie | każdy test ma własnego użytkownika i grupę, nie zależy od kolejności ani od danych z innych testów. Sprawdzone: kilka uruchomień pod rząd daje ten sam wynik. |
| Sprząta dane / izolowane środowisko | oba naraz: po każdym teście fixture usuwa listy, produkt i jednostki przez API i sprawdza, że grupa jest pusta. Cała baza jest tymczasowa i znika po zakończeniu sesji testów. |

### Znane błędy w testach (`xfail`)

Przypadki 1b-krok2 i 2c sprawdzają **poprawne** zachowanie, którego system dziś nie ma. Test wysyła zapytanie, a jeśli odpowiedź jest błędna, wywołuje `pytest.xfail("...")` z opisem tego, co faktycznie przyszło:

- dopóki błąd istnieje, test kończy się wynikiem `XFAIL` (spodziewana porażka, znany błąd), a cały zestaw nie świeci się na czerwono;
- w podsumowaniu pytest od razu widać rzeczywistą odpowiedź, np. `oczekiwano 422, otrzymano 500 Internal Server Error`;
- po naprawie błędu warunek nie zajdzie, wykonają się zwykłe asercje i test będzie `PASSED`;
- jeśli test padnie z innego powodu (np. awaria przygotowania stanu), wynik to zwykły `FAILED`, a nie `XFAIL`.

Wynik jest taki sam jak u Basi w Zadaniu 1: 500 dla pustego tekstu i 201 z zapisaną pozycją dla nieistniejącej jednostki.

## Narzędzie

- **pytest 9.1** z wtyczkami projektu
- **FastAPI `TestClient`** (Starlette + httpx) wysyła zapytania HTTP do aplikacji
- istniejące fixture'y Mealie: `api_client`, `unique_user_fn_scoped` oraz stałe ścieżek z `tests/utils/api_routes`

## Instrukcja uruchomienia

Z katalogu głównego repozytorium (Python 3.14, zainstalowane zależności w `.venv`):

```bash
# Windows (PowerShell)
.venv\Scripts\python -m pytest tests\integracja\automatyzacja -vv

# Windows (Git Bash)
.venv/Scripts/python -m pytest tests/integracja/automatyzacja -vv

# Linux / macOS
.venv/bin/python -m pytest tests/integracja/automatyzacja -vv

# albo, jeśli zależności są zsynchronizowane przez uv:
uv run pytest tests/integracja/automatyzacja -vv
```

`-vv` (podwójne) jest potrzebne, bo `pyproject.toml` dodaje domyślnie `-q`, które znosi pojedyncze `-v`. Z `-vv` każdy test jest wypisany w osobnej linii z wynikiem. Podsumowanie na końcu pokazuje powód każdego `XFAIL`.

Nie trzeba uruchamiać serwera ani bazy. Testy same tworzą aplikację i tymczasową bazę SQLite.

## Wynik testu

Uruchomienie 09.11.2026, Windows 11, Python 3.14.4, pytest 9.1.1:

```
test_integracja_automatyczna.py::test_1a_parser_dopasowuje_jednostke_i_produkt_z_bazy[1a-krok1] PASSED [ 14%]
test_integracja_automatyczna.py::test_1a_parser_dopasowuje_jednostke_i_produkt_z_bazy[1a-krok2] PASSED [ 28%]
test_integracja_automatyczna.py::test_1b_krok1_produkt_spoza_bazy_nie_dostaje_id PASSED              [ 42%]
test_integracja_automatyczna.py::test_1b_krok2_pusty_tekst_zwraca_blad_walidacji XFAIL               [ 57%]
test_integracja_automatyczna.py::test_2a_zgodne_jednostki_sa_laczone_z_przeliczeniem PASSED          [ 71%]
test_integracja_automatyczna.py::test_2b_jednostki_nieprzeliczalne_daja_osobne_pozycje PASSED        [ 85%]
test_integracja_automatyczna.py::test_2c_nieistniejaca_jednostka_jest_odrzucana XFAIL                [100%]

=========================== short test summary info ===========================
XFAIL test_1b_krok2_pusty_tekst_zwraca_blad_walidacji - BR-01: oczekiwano 422, otrzymano 500 Internal Server Error (odpowiedź: 'Internal Server Error') - parser rzuca IndexError dla pustego tekstu
XFAIL test_2c_nieistniejaca_jednostka_jest_odrzucana - BR-02: oczekiwano 404/422, otrzymano 201 Created; w bazie zapisano 1 pozycję: ["unitId=<nieistniejące>, unit=None, display='1 flour'"]
======================== 5 passed, 2 xfailed in 5.11s =========================
```

Wyniki automatyczne są zgodne z wynikami ręcznymi z Zadania 1: ścieżki happy path działają, a oba błędy (BR-01, BR-02) nadal występują.

## Elementy rzeczywiste i atrapy

| Element | Rzeczywisty / atrapa |
|---|---|
| Endpointy API (`/api/parser/ingredient`, `/api/units`, `/api/foods`, `/api/households/shopping/...`) | rzeczywiste |
| Uwierzytelnianie (rejestracja, logowanie, token JWT) | rzeczywiste |
| Parser `brute` i `DataMatcher` | rzeczywiste |
| `ShoppingListService` i `UnitConverter` (pint) | rzeczywiste |
| Baza danych | rzeczywista SQLite, ale **tymczasowa** (`tests/.temp`), tworzona od zera dla sesji testów |
| Serwer HTTP (uvicorn) i sieć | **zastąpione** przez `TestClient`, który wywołuje aplikację ASGI w tym samym procesie |
| Frontend (Nuxt) | **pominięty**, zapytania idą prosto do API |

Poza serwerem HTTP nic nie jest mockowane. Wszystkie elementy biorące udział w integracji to prawdziwy kod Mealie.

## Ograniczenia automatyzacji

- **Tylko SQLite.** Produkcyjnie Mealie działa też na PostgreSQL, który wymusza klucze obce, więc BR-02 może się tam objawić inaczej (np. błędem 500 przy zapisie zamiast cichego 201). Testy nie sprawdzają tej różnicy.
- **Tylko parser `brute`.** Parsery `nlp` (model ML) i `openai` (zewnętrzne API) nie są testowane. `openai` wymagałby atrapy zewnętrznego serwisu.
- **Bez prawdziwego serwera i frontendu.** `TestClient` pomija uvicorn, sieć, CORS i przeglądarkę, więc błędy na tych warstwach nie zostaną wykryte.
- **Konfiguracja testowa różni się od produkcyjnej**: `conftest.py` ustawia `TESTING=True`, a każdy test działa w nowej, pustej grupie bez domyślnych jednostek i produktów.
- **Stała lista danych.** Testy sprawdzają dokładnie przypadki z Zadania 1 (np. cup + tablespoon), a nie wszystkie kombinacje jednostek.
- **`uv run` na Windows** może wymagać Microsoft C++ Build Tools (pakiet `python-ldap`), jeśli środowisko nie jest jeszcze zsynchronizowane. Wtedy trzeba uruchamiać przez `.venv/Scripts/python`.
