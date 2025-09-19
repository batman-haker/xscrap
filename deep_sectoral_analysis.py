#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Sectoral Analysis - Interpretacja wypowiedzi autorów według sektorów
Analiza semantyczna i konfrontacyjna poglądów ekspertów
"""

import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()

def load_comprehensive_tweets():
    """Load tweets from comprehensive cache"""
    try:
        with open('data/raw/comprehensive_tweets_current.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('tweets_by_category', {})
    except Exception as e:
        print(f"[ERROR] Błąd ładowania tweetów: {e}")
        return None

def analyze_sector_with_claude(sector_name, tweets, claude_client):
    """Analiza sektora z wykorzystaniem Claude AI"""

    if not tweets:
        return None

    print(f"[ANALIZA] {sector_name}: {len(tweets)} tweetów od {len(set(t.get('username', '') for t in tweets))} autorów")

    # Prepare tweet content for analysis
    tweets_content = ""
    authors_viewpoints = {}

    for tweet in tweets[:50]:  # Limit to most relevant tweets
        username = tweet.get('username', 'unknown')
        text = tweet.get('text', '')
        engagement = tweet.get('like_count', 0) + tweet.get('retweet_count', 0)

        if username not in authors_viewpoints:
            authors_viewpoints[username] = []

        authors_viewpoints[username].append({
            'text': text,
            'engagement': engagement
        })

        tweets_content += f"\n@{username}: {text}\n"

    # Create comprehensive analysis prompt
    prompt = f"""# GŁĘBOKA ANALIZA SEKTOROWA: {sector_name.upper()}

## ZADANIE ANALITYCZNE
Przeanalizuj wypowiedzi ekspertów z sektora {sector_name} i wykonaj głęboką interpretację semantyczną ich poglądów.

## DANE DO ANALIZY:
{tweets_content}

## AUTORZY I ICH POGLĄDY:
{json.dumps(authors_viewpoints, indent=2, ensure_ascii=False)}

## WYMAGANIA ANALIZY:

### 1. SEMANTYCZNA INTERPRETACJA WYPOWIEDZI
- Wydobądź kluczowe tezy i poglądy każdego autora
- Zidentyfikuj ukryte znaczenia i konteksty
- Oceń pewność/niepewność w wypowiedziach
- Znajdź nietypowe lub nowatorskie spojrzenia

### 2. KONFRONTACJA POGLĄDÓW
- Porównaj stanowiska różnych autorów
- Zidentyfikuj zgodności i sprzeczności
- Przeanalizuj argumenty za i przeciw
- Oceń siłę argumentacji każdego stanowiska

### 3. SYNTEZA I INTERPRETACJA
- Zsyntetyzuj główne nurty myślowe w sektorze
- Wyciągnij wnioski z konfrontacji poglądów
- Zidentyfikuj emerging consensus lub polaryzację
- Oceń implikacje dla inwestorów

### 4. PRZEWAGA KONKURENCYJNA
- Które poglądy mogą dać przewagę inwestycyjną?
- Jakie niestandardowe perspektywy się wyłaniają?
- Gdzie autorzy mogą się mylić?
- Jakie są blind spots w analizie sektora?

## FORMAT ODPOWIEDZI (JSON):
{{
    "sector_overview": {{
        "name": "{sector_name}",
        "total_tweets": {len(tweets)},
        "unique_authors": {len(authors_viewpoints)},
        "dominant_themes": ["temat1", "temat2", "temat3"]
    }},
    "authors_analysis": {{
        "author1": {{
            "key_positions": ["teza1", "teza2"],
            "confidence_level": "high/medium/low",
            "unique_insights": ["insight1", "insight2"],
            "potential_biases": ["bias1", "bias2"]
        }}
    }},
    "viewpoints_confrontation": {{
        "major_agreements": ["zgoda1", "zgoda2"],
        "major_disagreements": ["spór1", "spór2"],
        "unresolved_tensions": ["napięcie1", "napięcie2"],
        "synthesis": "główna synteza poglądów"
    }},
    "investment_implications": {{
        "actionable_insights": ["insight1", "insight2"],
        "contrarian_opportunities": ["okazja1", "okazja2"],
        "risk_warnings": ["ryzyko1", "ryzyko2"],
        "timing_indicators": ["timing1", "timing2"]
    }},
    "competitive_intelligence": {{
        "market_blind_spots": ["blind_spot1", "blind_spot2"],
        "emerging_narratives": ["narracja1", "narracja2"],
        "author_credibility_ranking": ["author1", "author2", "author3"],
        "predictive_value": "ocena wartości predykcyjnej analizy"
    }}
}}

Skoncentruj się na ZNACZENIU i INTERPRETACJI, nie na liczeniu słów kluczowych. Chcę zrozumieć co autorzy NAPRAWDĘ myślą i jak ich poglądy się ze sobą konfrontują."""

    try:
        # Try latest Claude models first
        models_to_try = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-5-haiku-20241022",
            "claude-3-haiku-20240307"
        ]

        for model in models_to_try:
            try:
                print(f"[CLAUDE] Próbuję model: {model}")
                response = claude_client.messages.create(
                    model=model,
                    max_tokens=8000,
                    temperature=0.2,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                print(f"[SUCCESS] Analiza sektora {sector_name} ukończona z modelem {model}")
                return {
                    "model_used": model,
                    "analysis": response.content[0].text,
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                print(f"[FAIL] Model {model} failed: {e}")
                continue

        print(f"[ERROR] Wszystkie modele Claude zawiodły dla sektora {sector_name}")
        return None

    except Exception as e:
        print(f"[ERROR] Błąd analizy Claude dla {sector_name}: {e}")
        return None

def run_deep_sectoral_analysis():
    """Main function to run deep sectoral analysis"""

    print("=== GŁĘBOKA ANALIZA SEKTOROWA ===")
    print("Analiza semantyczna i konfrontacyjna poglądów ekspertów\n")

    # Load comprehensive tweets
    tweets_by_category = load_comprehensive_tweets()
    if not tweets_by_category:
        print("[ERROR] Nie można załadować tweetów")
        return None

    # Initialize Claude client
    try:
        claude_client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
    except Exception as e:
        print(f"[ERROR] Nie można zainicjalizować klienta Claude: {e}")
        return None

    # Analyze each sector
    sectoral_analyses = {}

    for sector, tweets in tweets_by_category.items():
        if not tweets:
            print(f"[SKIP] {sector}: Brak tweetów")
            continue

        print(f"\n--- ROZPOCZYNAM ANALIZĘ: {sector.upper()} ---")

        analysis = analyze_sector_with_claude(sector, tweets, claude_client)

        if analysis:
            sectoral_analyses[sector] = analysis

            # Save individual sector analysis
            sector_file = f'data/analysis/deep_analysis_{sector.lower()}.json'
            os.makedirs('data/analysis', exist_ok=True)

            with open(sector_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)

            print(f"[SAVED] {sector_file}")

            # Rate limiting between requests
            time.sleep(10)  # 10 seconds between sectors to respect rate limits
        else:
            print(f"[FAILED] Analiza sektora {sector} nie powiodła się")

    # Create comprehensive report
    comprehensive_report = {
        "analysis_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_sectors_analyzed": len(sectoral_analyses),
            "analysis_type": "deep_sectoral_semantic"
        },
        "sectoral_analyses": sectoral_analyses
    }

    # Save comprehensive analysis
    comprehensive_file = 'data/analysis/deep_sectoral_analysis_comprehensive.json'
    with open(comprehensive_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_report, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Kompletna analiza zapisana: {comprehensive_file}")
    print(f"[STATS] Przeanalizowano {len(sectoral_analyses)} sektorów")

    return comprehensive_report

if __name__ == "__main__":
    result = run_deep_sectoral_analysis()

    if result:
        print("\n=== PODSUMOWANIE ===")
        for sector in result['sectoral_analyses'].keys():
            print(f"✓ {sector}: Analiza semantyczna ukończona")
        print(f"\n[READY] Głębokie analizy sektorowe gotowe!")
        print("Sprawdź pliki w folderze data/analysis/")
    else:
        print("\n[ERROR] Analiza nie powiodła się")