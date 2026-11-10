"""
Automatyzacja testów integracyjnych z Zadania 1 (tests/integracja/basia.md).

I-1: parser składników (brute) <-> baza jednostek i produktów (DataMatcher)
I-2: lista zakupów (ShoppingListService) <-> przeliczanie jednostek (UnitConverter, pint) <-> baza

Każdy test:
- przygotowuje stan przez API (nowy użytkownik = nowa grupa, własne jednostki, produkt, lista),
- sprawdza wynik integracji przez API,
- sprząta po sobie (fixture z `yield`, usuwa listę, jednostki i produkty),
- działa na tymczasowej bazie SQLite tworzonej przez tests/conftest.py.

Przypadki, które w Zadaniu 1 wykazały błędy (BR-01, BR-02), sprawdzają POPRAWNE zachowanie.
Dopóki błąd istnieje, test kończy się wynikiem XFAIL ("spodziewana porażka - znany błąd"),
a w podsumowaniu pytest widać, co dokładnie przyszło zamiast oczekiwanej odpowiedzi.
Po naprawie błędu test po prostu zacznie przechodzić (PASSED).

Uruchomienie (z katalogu głównego repozytorium, PowerShell):
    .venv\\Scripts\\python -m pytest tests\\integracja\\automatyzacja -v
"""

# --------------------------------------------------------------------------- #
# Importy
# --------------------------------------------------------------------------- #

# Generator - typ funkcji z `yield` (używany w adnotacji fixture `stan`)
from collections.abc import Generator

# dataclass - skrót do tworzenia klas, które tylko przechowują dane
# field     - pozwala ustawić opcje pola; u nas: wartość domyślną robioną od nowa dla każdego obiektu
from dataclasses import dataclass, field

# uuid4 - generuje losowy identyfikator; używamy go jako id jednostki, której NIE MA w bazie (test 2c)
from uuid import uuid4

import pytest

# TestClient - "przeglądarka" do testów: wysyła zapytania HTTP prosto do aplikacji FastAPI,
# bez uruchamiania prawdziwego serwera i bez sieci
from fastapi.testclient import TestClient

# app - cała aplikacja backendu Mealie (ta sama, którą uruchamia serwer)
from mealie.app import app

# api_routes - gotowe adresy endpointów, np. api_routes.units == "/api/units"
from tests.utils import api_routes

# TestUser - typ obiektu użytkownika testowego (ma m.in. token do logowania)
from tests.utils.fixture_schemas import TestUser

# --------------------------------------------------------------------------- #
# Dane testowe - wspólny stan początkowy z Zadania 1
# --------------------------------------------------------------------------- #

# Jednostki, które tworzymy w bazie przed każdym testem.
# Każda dostaje standardUnit = swoja nazwa i standardQuantity = 1, dzięki czemu
# UnitConverter (pint) wie, jak je przeliczać (np. że 1 cup = 16 tablespoon).
JEDNOSTKI = ["cup", "tablespoon", "gram", "liter"]

# Produkt, który tworzymy w bazie przed każdym testem.
PRODUKT = "flour"


@dataclass
class StanTestowy:
    """
    "Pudełko" na dane utworzone w bazie na potrzeby jednego testu.

    Test bierze stąd id jednostek i produktu, a fixture `stan` po teście
    przechodzi po tych polach i usuwa wszystko, co zostało utworzone.
    """

    # Zalogowany użytkownik testowy. `user.token` to nagłówek Authorization,
    # który dołączamy do każdego zapytania do API.
    user: TestUser

    # Słownik: nazwa jednostki -> pełny rekord zwrócony przez API po jej utworzeniu.
    # Np. jednostki["cup"]["id"] to prawdziwe id jednostki "cup" w bazie.
    # field(default_factory=dict) = każdy obiekt StanTestowy dostaje własny, nowy, pusty słownik {}
    # (gdyby było `= {}`, wszystkie obiekty dzieliłyby JEDEN słownik i testy mieszałyby sobie dane).
    jednostki: dict[str, dict] = field(default_factory=dict)

    # Rekord produktu "flour" zwrócony przez API, np. {"id": "...", "name": "flour", ...}
    produkt: dict = field(default_factory=dict)

    # Id list zakupów utworzonych w trakcie testu - żeby wiedzieć, co usunąć po teście.
    # Na początku pusta lista [], funkcja nowa_lista() dopisuje do niej kolejne id.
    listy: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Fixture - przygotowanie stanu przed testem i sprzątanie po teście
# --------------------------------------------------------------------------- #


# @pytest.fixture() - pytest wywoła tę funkcję automatycznie dla każdego testu,
# który ma parametr o nazwie `stan`. Puste nawiasy = nowa fixture dla KAŻDEGO testu.
#
# Parametry `api_client` i `unique_user_fn_scoped` to też fixture (z tests/conftest.py
# i tests/fixtures/fixture_users.py) - pytest sam je przygotuje i tu poda:
#   - api_client:            klient HTTP do aplikacji, podłączony do tymczasowej bazy SQLite,
#   - unique_user_fn_scoped: NOWY zarejestrowany i zalogowany użytkownik z własną, pustą grupą
#                            ("fn_scoped" = nowy dla każdego testu, więc testy na siebie nie wpływają).
@pytest.fixture()
def stan(api_client: TestClient, unique_user_fn_scoped: TestUser) -> Generator[StanTestowy]:
    """
    Stan początkowy: zalogowany użytkownik (nowa, pusta grupa), w bazie jednostki
    cup, tablespoon, gram, liter oraz produkt flour. Po teście wszystko jest usuwane.
    """
    user = unique_user_fn_scoped
    s = StanTestowy(user=user)

    # ===== CZĘŚĆ 1: PRZYGOTOWANIE (wykonuje się PRZED testem) =====

    # Tworzymy każdą jednostkę przez API: POST /api/units
    for nazwa in JEDNOSTKI:
        r = api_client.post(
            api_routes.units,
            json={"name": nazwa, "standardUnit": nazwa, "standardQuantity": 1},
            headers=user.token,  # bez tokenu API odpowie 401 (brak autoryzacji)
        )
        # 201 = "Created", rekord zapisany. Jeśli nie, test przerywa się z treścią odpowiedzi (r.text).
        assert r.status_code == 201, r.text
        # Zapamiętujemy odpowiedź API (zawiera m.in. nadane przez bazę "id")
        s.jednostki[nazwa] = r.json()

    # Tworzymy produkt "flour": POST /api/foods
    r = api_client.post(api_routes.foods, json={"name": PRODUKT}, headers=user.token)
    assert r.status_code == 201, r.text
    s.produkt = r.json()

    # ===== PAUZA: tu pytest uruchamia TEST i przekazuje mu `s` jako parametr `stan` =====
    # `yield` (w przeciwieństwie do `return`) nie kończy funkcji, tylko ją wstrzymuje.
    # Gdy test się skończy (nawet z błędem), pytest wraca tutaj i wykonuje dalszą część.
    yield s

    # ===== CZĘŚĆ 2: SPRZĄTANIE (wykonuje się PO teście) =====

    # Kolejność ma znaczenie: najpierw listy (razem z ich pozycjami), bo pozycje
    # odwołują się do produktu i jednostek; potem produkt i jednostki.
    for list_id in s.listy:
        api_client.delete(api_routes.households_shopping_lists_item_id(list_id), headers=user.token)
    api_client.delete(api_routes.foods_item_id(s.produkt["id"]), headers=user.token)
    for jednostka in s.jednostki.values():
        api_client.delete(api_routes.units_item_id(jednostka["id"]), headers=user.token)

    # Sprawdzamy, czy sprzątanie się udało: grupa użytkownika nie ma już jednostek ani produktów.
    # GET /api/units i /api/foods zwracają {"items": [...], ...} - lista musi być pusta.
    assert api_client.get(api_routes.units, headers=user.token).json()["items"] == []
    assert api_client.get(api_routes.foods, headers=user.token).json()["items"] == []


@pytest.fixture()
def klient_http(api_client: TestClient) -> TestClient:
    """
    Klient, który zachowuje się jak prawdziwa przeglądarka/curl: nieobsłużony wyjątek
    w aplikacji zwraca odpowiedź 500 zamiast przerywać test wyjątkiem Pythona.
    Zależy od `api_client`, żeby była ustawiona testowa sesja bazy danych.
    """
    # Domyślny TestClient, gdy w aplikacji poleci wyjątek (np. IndexError), rzuca go
    # od razu w teście. My chcemy zobaczyć to, co zobaczyłby użytkownik - kod HTTP 500.
    # raise_server_exceptions=False właśnie to włącza. Potrzebne w testach błędów (1b-krok2, 2c).
    return TestClient(app, raise_server_exceptions=False)


# --------------------------------------------------------------------------- #
# Funkcje pomocnicze - żeby testy były krótsze i czytelniejsze
# --------------------------------------------------------------------------- #


def nowa_lista(api_client: TestClient, s: StanTestowy, nazwa: str) -> str:
    """Tworzy nową, pustą listę zakupów i zwraca jej id (zapisuje je też do sprzątania)."""
    # POST /api/households/shopping/lists
    r = api_client.post(api_routes.households_shopping_lists, json={"name": nazwa}, headers=s.user.token)
    assert r.status_code == 201, r.text
    lista = r.json()
    # Warunek wstępny scenariuszy 2a-2c: lista na początku jest pusta
    assert lista["listItems"] == []
    # Dopisujemy id do "pudełka", żeby fixture `stan` usunęła tę listę po teście
    s.listy.append(lista["id"])
    return lista["id"]


def dodaj_pozycje(api_client: TestClient, s: StanTestowy, list_id: str, ilosc: float, unit_id: str) -> dict:
    """
    Dodaje do listy pozycję "<ilosc> <jednostka> flour" i zwraca odpowiedź API.

    Odpowiedź ma m.in. pola:
      - createdItems: pozycje, które zostały NOWO utworzone,
      - updatedItems: istniejące pozycje, które serwis zaktualizował (np. połączył z nową).
    """
    # POST /api/households/shopping/items
    r = api_client.post(
        api_routes.households_shopping_items,
        json={
            "shoppingListId": list_id,
            "quantity": ilosc,
            "unitId": unit_id,
            "foodId": s.produkt["id"],
        },
        headers=s.user.token,
    )
    assert r.status_code == 201, r.text
    return r.json()


def pozycje_listy(api_client: TestClient, s: StanTestowy, list_id: str) -> list[dict]:
    """Pobiera listę zakupów z bazy i zwraca jej pozycje (to, co faktycznie zostało zapisane)."""
    # GET /api/households/shopping/lists/{id}
    r = api_client.get(api_routes.households_shopping_lists_item_id(list_id), headers=s.user.token)
    assert r.status_code == 200, r.text
    return r.json()["listItems"]


def parsuj(klient: TestClient, s: StanTestowy, tekst: str):
    """Wysyła tekst składnika do parsera "brute" i zwraca surową odpowiedź HTTP."""
    # POST /api/parser/ingredient  (zwracamy całą odpowiedź, bo testy sprawdzają też kod HTTP)
    return klient.post(
        api_routes.parser_ingredient,
        json={"parser": "brute", "ingredient": tekst},
        headers=s.user.token,
    )


# --------------------------------------------------------------------------- #
# Scenariusz 1 (I-1): rozpoznanie składnika i dopasowanie do bazy
# --------------------------------------------------------------------------- #


# @pytest.mark.parametrize - ten sam test uruchamia się kilka razy z różnymi danymi.
# Tu: 2 uruchomienia (2 kroki z przypadku 1a). `id=` to nazwa widoczna w wyniku pytest,
# np. "test_1a_...[1a-krok1]".
@pytest.mark.parametrize(
    "tekst, oczekiwana_ilosc",
    [
        pytest.param("2 cups flour", 2.0, id="1a-krok1"),
        pytest.param("1/2 cup flour", 0.5, id="1a-krok2"),
    ],
)
def test_1a_parser_dopasowuje_jednostke_i_produkt_z_bazy(
    api_client: TestClient, stan: StanTestowy, tekst: str, oczekiwana_ilosc: float
):
    """Happy path: parser rozbija tekst i dopasowuje jednostkę i produkt do rekordów z bazy."""
    r = parsuj(api_client, stan, tekst)

    assert r.status_code == 200, r.text
    skladnik = r.json()["ingredient"]

    # Ilość odczytana z tekstu. pytest.approx - porównanie liczb zmiennoprzecinkowych z tolerancją.
    assert skladnik["quantity"] == pytest.approx(oczekiwana_ilosc)

    # PUNKT INTEGRACJI: parser nie zwraca tylko napisu "cup"/"flour", ale konkretne rekordy z bazy.
    # Sprawdzamy, że id w odpowiedzi parsera == id, które baza nadała w fixture `stan`.
    # ("cups" w liczbie mnogiej też ma trafić w jednostkę "cup")
    assert skladnik["unit"] is not None
    assert skladnik["unit"]["id"] == stan.jednostki["cup"]["id"]
    assert skladnik["food"] is not None
    assert skladnik["food"]["id"] == stan.produkt["id"]


def test_1b_krok1_produkt_spoza_bazy_nie_dostaje_id(api_client: TestClient, stan: StanTestowy):
    """Tekst bez ilości i z produktem, którego nie ma w bazie."""
    r = parsuj(api_client, stan, "salt")

    assert r.status_code == 200, r.text
    skladnik = r.json()["ingredient"]
    assert not skladnik["quantity"]  # 0 albo None - brak ilości w tekście
    assert skladnik["unit"] is None  # brak jednostki w tekście
    # Parser rozpoznał nazwę produktu...
    assert skladnik["food"] is not None
    assert skladnik["food"]["name"] == "salt"
    # ...ale nie dopasował go do bazy, bo "salt" tam nie ma -> brak id
    assert skladnik["food"].get("id") is None


def test_1b_krok2_pusty_tekst_zwraca_blad_walidacji(klient_http: TestClient, stan: StanTestowy):
    """
    Pusty tekst powinien zostać odrzucony jako błędne dane (422), a nie wywalić serwera (500).
    """
    # klient_http zamiast api_client - żeby wyjątek w aplikacji dał odpowiedź 500, a nie przerwał test
    r = parsuj(klient_http, stan, "")

    if r.status_code != 422:
        pytest.xfail(
            f"BR-01: oczekiwano 422, otrzymano {r.status_code} {r.reason_phrase} "
            f"(odpowiedź: {r.text[:60]!r}) - parser rzuca IndexError dla pustego tekstu"
        )



# --------------------------------------------------------------------------- #
# Scenariusz 2 (I-2): łączenie pozycji na liście zakupów
# --------------------------------------------------------------------------- #


def test_2a_zgodne_jednostki_sa_laczone_z_przeliczeniem(api_client: TestClient, stan: StanTestowy):
    """Happy path: 1 cup + 2 tablespoon tego samego produktu -> jedna pozycja 1.125 cup."""
    list_id = nowa_lista(api_client, stan, "S2a")
    cup = stan.jednostki["cup"]
    tbsp = stan.jednostki["tablespoon"]

    # Krok 2: pierwsza pozycja - lista była pusta, więc musi powstać nowa pozycja
    wynik1 = dodaj_pozycje(api_client, stan, list_id, 1, cup["id"])
    assert len(wynik1["createdItems"]) == 1

    # Krok 3: druga pozycja, ten sam produkt, inna ale zgodna jednostka (obie to objętość)
    wynik2 = dodaj_pozycje(api_client, stan, list_id, 2, tbsp["id"])
    # PUNKT INTEGRACJI: serwis listy zakupów zapytał UnitConverter, czy jednostki da się przeliczyć,
    # i zamiast tworzyć nową pozycję, zaktualizował istniejącą
    assert wynik2["createdItems"] == []
    assert len(wynik2["updatedItems"]) == 1

    # Krok 4: odczyt z bazy - czy wynik przeliczenia został faktycznie zapisany
    pozycje = pozycje_listy(api_client, stan, list_id)
    assert len(pozycje) == 1
    # 1 cup = 16 tablespoon, więc 2 tbsp = 0.125 cup; razem 1 + 0.125 = 1.125 cup
    assert pozycje[0]["quantity"] == pytest.approx(1.125)
    assert pozycje[0]["unitId"] == cup["id"]  # wynik w większej jednostce (cup)
    assert pozycje[0]["foodId"] == stan.produkt["id"]


def test_2b_jednostki_nieprzeliczalne_daja_osobne_pozycje(api_client: TestClient, stan: StanTestowy):
    """500 gram + 1 liter tego samego produktu -> dwie osobne pozycje (masa != objętość)."""
    list_id = nowa_lista(api_client, stan, "S2b")
    gram = stan.jednostki["gram"]
    liter = stan.jednostki["liter"]

    dodaj_pozycje(api_client, stan, list_id, 500, gram["id"])
    wynik2 = dodaj_pozycje(api_client, stan, list_id, 1, liter["id"])
    # UnitConverter odpowiedział "nie da się przeliczyć", więc serwis utworzył NOWĄ pozycję
    assert len(wynik2["createdItems"]) == 1

    pozycje = pozycje_listy(api_client, stan, list_id)
    assert len(pozycje) == 2
    # Zamieniamy listę pozycji na słownik {unitId: ilość}, żeby nie zależeć od kolejności pozycji
    po_jednostce = {p["unitId"]: p["quantity"] for p in pozycje}
    # Ilości zostały bez zmian - nic nie zostało błędnie zsumowane
    assert po_jednostce[gram["id"]] == pytest.approx(500)
    assert po_jednostce[liter["id"]] == pytest.approx(1)


def test_2c_nieistniejaca_jednostka_jest_odrzucana(klient_http: TestClient, stan: StanTestowy):
    """
    Pozycja z id jednostki, której nie ma w bazie, powinna zostać odrzucona (404/422) i niezapisana.
    Znany błąd BR-02 - dopóki występuje, test kończy się wynikiem XFAIL z opisem tego, co przyszło.
    """
    list_id = nowa_lista(klient_http, stan, "S2c")
    # Losowe id - na pewno nie ma takiej jednostki w bazie
    nieistniejace_id = str(uuid4())

    # Nie używamy dodaj_pozycje(), bo ona wymaga kodu 201, a tu oczekujemy błędu
    r = klient_http.post(
        api_routes.households_shopping_items,
        json={
            "shoppingListId": list_id,
            "quantity": 1,
            "unitId": nieistniejace_id,
            "foodId": stan.produkt["id"],
        },
        headers=stan.user.token,
    )
    # Co faktycznie trafiło do bazy po tej próbie
    zapisane = pozycje_listy(klient_http, stan, list_id)

    # Znany błąd: API przyjmuje pozycję i zapisuje ją z id nieistniejącej jednostki
    if r.status_code not in (404, 422) or zapisane:
        opis_zapisanych = [f"unitId=<nieistniejące>, unit={p['unit']}, display={p['display']!r}" for p in zapisane]
        pytest.xfail(
            f"BR-02: oczekiwano 404/422, otrzymano {r.status_code} {r.reason_phrase}; "
            f"w bazie zapisano {len(zapisane)} pozycję: {opis_zapisanych}"
        )

    # Ta część wykona się dopiero po naprawie BR-02 - wtedy test będzie PASSED
    assert r.status_code in (404, 422)
    assert zapisane == []
