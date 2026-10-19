# Unit testy czarnoskrzynkowe — Mealie

## Wybrane najważniejsze funkcjonalności systemu

Mealie to aplikacja do zarządzania przepisami kulinarnymi. Za najważniejsze funkcjonalności uznaliśmy te, bez których aplikacja traci swój główny sens:

| Funkcjonalność | Dlaczego jest kluczowa | Osoba |
|---|---|---|
| **Import przepisu z adresu URL** | Główny sposób dodawania przepisów: użytkownik wkleja link, a system zamienia dane ze strony na przepis (składniki, kroki, porcje, czas, zdjęcie) | KacperM |
| **Rozpoznawanie składników i przeliczanie jednostek** | System musi zrozumieć tekst typu „2 1/2 cup flour”, żeby skalować przepisy i łączyć pozycje na liście zakupów | Basia |
| **Logowanie, adresy przepisów, wyszukiwanie i planer posiłków** | Dostęp do konta, unikalny adres każdego przepisu, filtrowanie przepisów oraz przypisywanie posiłków do dni tygodnia | KacperS |

Każda osoba testuje **5 funkcji** realizujących jej funkcjonalność. Razem: 15 funkcji.

## Zasady (testy czarnoskrzynkowe)

- Przypadki testowe projektujemy **wyłącznie na podstawie wejścia i wyjścia funkcji** (sygnatura, nazwa, docstring). Nie analizujemy kodu wewnątrz funkcji.
- Nie kopiujemy istniejących testów z `tests/unit_tests/`.
- Dla każdej funkcji: min. 3–5 przypadków (poprawne, brzegowe, niepoprawne dane).
- Jeśli test nie przechodzi, **nie poprawiamy go pod kod**. Zapisujemy `FAIL` i opisujemy rozbieżność.

## Pliki

| Osoba | Opis zadania | Implementacja testów |
|---|---|---|
| KacperM | [kacperM.md](kacperM.md) | `test_kacperM.py` |
| Basia | [basia.md](basia.md) | `test_basia.py` |
| KacperS | [KacperS.md](KacperS.md) | `test_KacperS.py` |

Uruchomienie wszystkich testów: `uv run pytest tests/black_box -v`
