# X Financial Analysis Project

## Opis Projektu
Aplikacja do analizy finansowej wykorzystująca X API do pobierania i analizowania tweetów z kont ekspertów finansowych. System automatycznie pobiera treści, analizuje sentymenty i generuje rekomendacje inwestycyjne.

## Funkcjonalności
- Automatyczne pobieranie tweetów z wybranych kont ekspertów finansowych
- Kategoryzacja tematyczna (crypto, gospodarka USA, Polska, geopolityka)
- Analiza sentymenty z wykorzystaniem AI
- Generowanie rekomendacji inwestycyjnych
- Raportowanie w formacie Markdown
- Automatyzacja zadań według harmonogramu

## Instalacja

1. Sklonuj repozytorium
2. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

3. Skonfiguruj zmienne środowiskowe w pliku `.env`:
```env
# X API (twitterapi.io)
TWITTER_API_KEY=your_api_key
TWITTER_BEARER_TOKEN=your_bearer_token

# Claude API
CLAUDE_API_KEY=your_claude_api_key

# GitHub (opcjonalnie)
GITHUB_TOKEN=your_github_token
```

## Użycie

```bash
python main.py
```

## Struktura Projektu
- `config/` - pliki konfiguracyjne
- `src/` - kod źródłowy aplikacji
- `data/` - dane raw, przetworzone i archiwum
- `reports/` - generowane raporty

## Harmonogram
- Co 1 godzina: Pobieranie nowych tweetów
- Co 4 godziny: Analiza sentymenty
- Codziennie o 8:00: Generowanie raportu dziennego
- W niedziele: Raport tygodniowy z rekomendacjami