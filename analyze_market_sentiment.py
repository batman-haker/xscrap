#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()

def analyze_tweets_with_claude():
    """Analyze categorized tweets using Claude"""

    # Load tweets data
    try:
        # First try comprehensive tweets (new system)
        comprehensive_file = 'data/raw/comprehensive_tweets_current.json'
        if os.path.exists(comprehensive_file):
            with open(comprehensive_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tweets_data = data.get('tweets_by_category', {})
        else:
            # Fallback to sample file
            with open('data/raw/sample_categorized_tweets.json', 'r', encoding='utf-8') as f:
                tweets_data = json.load(f)
    except Exception as e:
        print(f"Błąd ładowania tweetów: {e}")
        return None

    # Prepare data for Claude
    total_tweets = sum(len(tweets) for tweets in tweets_data.values())
    print(f"Przygotowuję analizę {total_tweets} tweetów z {len(tweets_data)} kategorii...")

    # Create comprehensive prompt for Claude
    prompt = f"""# ANALIZA SENTYMENTY FINANSOWEGO - {datetime.now().strftime('%d.%m.%Y')}

Przeanalizuj poniższe najnowsze tweety z różnych kategorii finansowych i ekonomicznych. Na podstawie tych danych przygotuj kompleksową analizę i prognozy.

## DANE DO ANALIZY:
"""

    for category, tweets in tweets_data.items():
        if tweets:
            prompt += f"\n### {category.upper()} ({len(tweets)} tweetów):\n"
            for i, tweet in enumerate(tweets, 1):
                username = tweet.get('username', 'unknown')
                text = tweet.get('text', '')
                likes = tweet.get('like_count', 0)
                retweets = tweet.get('retweet_count', 0)

                prompt += f"{i}. @{username} ({likes} ❤️, {retweets} 🔄):\n"
                prompt += f"   \"{text}\"\n\n"

    prompt += """
## ZADANIE ANALIZY:

Przygotuj kompleksową analizę rynkową zawierającą:

### 1. 📊 EXECUTIVE SUMMARY
- Ogólny sentiment rynkowy (skala 1-10)
- Kluczowe trendy i sygnały
- Najważniejsze wnioski (3-5 punktów)

### 2. 🔍 ANALIZA KATEGORIALNA
Dla każdej kategorii:
- Dominujący sentiment (pozytywny/negatywny/neutralny)
- Kluczowe tematy i obawy
- Poziom zaangażowania (high/medium/low)
- Wpływ na rynki

### 3. 🚨 SYGNAŁY OSTRZEGAWCZE
- Potencjalne zagrożenia
- Sygnały bańki spekulacyjnej
- Sygnały paniki/wyprzedaży
- Anomalie w sentymencje

### 4. 📈 PROGNOZY KRÓTKOTERMINOWE (1-4 tygodnie)
- Przewidywane kierunki rynków
- Najbardziej prawdopodobne scenariusze
- Kluczowe wydarzenia do obserwacji

### 5. 💡 REKOMENDACJE INWESTYCYJNE
- Sektory do rozważenia
- Sektory do unikania
- Strategia zarządzania ryzykiem
- Optymalne alokacje

### 6. 🔮 CZYNNIKI KLUCZOWE
- Eventi i daty do obserwacji
- Potencjalne katalizatory zmian
- Indykatory do monitorowania

Analiza powinna być konkretna, praktyczna i oparta na danych. Uwzględnij kontekst makroekonomiczny i obecne warunki rynkowe.
"""

    # Call Claude API
    try:
        client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))

        print("Wysyłam dane do Claude do analizy...")

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        analysis = response.content[0].text

        # Save analysis
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'tweets_analyzed': total_tweets,
            'categories': list(tweets_data.keys()),
            'source_data': tweets_data,
            'claude_analysis': analysis
        }

        output_file = 'data/analysis/market_sentiment_analysis.json'
        os.makedirs('data/analysis', exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)

        # Also save as markdown for easy reading
        markdown_file = 'data/analysis/market_analysis_report.md'
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(f"# ANALIZA RYNKU FINANSOWEGO\n")
            f.write(f"*Wygenerowano: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*\n\n")
            f.write(f"**Przeanalizowano {total_tweets} tweetów z {len(tweets_data)} kategorii**\n\n")
            f.write("---\n\n")
            f.write(analysis)

        print(f"✅ Analiza zapisana do:")
        print(f"   - {output_file}")
        print(f"   - {markdown_file}")

        return analysis_data

    except Exception as e:
        print(f"[ERROR] Blad podczas analizy Claude: {e}")
        return None

if __name__ == "__main__":
    print("=== ANALIZA SENTYMENTY RYNKOWEGO ===\n")

    result = analyze_tweets_with_claude()

    if result:
        print("\n[SUCCESS] Analiza ukonczona pomyslnie!")
        print(f"Przeanalizowano {result['tweets_analyzed']} tweetów")
        print("Sprawdź pliki w folderze data/analysis/")
    else:
        print("\n[ERROR] Nie udalo sie ukonczyc analizy")