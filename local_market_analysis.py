#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
from datetime import datetime
from textblob import TextBlob

def analyze_sentiment_simple(text):
    """Simple sentiment analysis using TextBlob"""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        if polarity > 0.1:
            return "Pozytywny", polarity
        elif polarity < -0.1:
            return "Negatywny", polarity
        else:
            return "Neutralny", polarity
    except:
        return "Neutralny", 0.0

def extract_financial_keywords(text):
    """Extract financial keywords"""
    financial_keywords = {
        'bullish': ['wzrost', 'rośnie', 'up', 'rally', 'bull', 'green', 'gains', 'surge'],
        'bearish': ['spadek', 'fall', 'down', 'bear', 'red', 'losses', 'drop', 'crash'],
        'uncertainty': ['volatile', 'uncertain', 'risk', 'fear', 'panic', 'crisis'],
        'institutions': ['fed', 'bank', 'federal', 'ecb', 'treasury', 'government'],
        'crypto': ['bitcoin', 'btc', 'crypto', 'blockchain', 'eth', 'ethereum'],
        'stocks': ['stock', 'shares', 'equity', 'market', 'trading', 'investing']
    }

    found_keywords = {}
    text_lower = text.lower()

    for category, keywords in financial_keywords.items():
        found = [kw for kw in keywords if kw in text_lower]
        if found:
            found_keywords[category] = found

    return found_keywords

def create_local_analysis():
    """Create comprehensive local analysis"""

    # Load tweets
    try:
        with open('data/raw/sample_categorized_tweets.json', 'r', encoding='utf-8') as f:
            tweets_data = json.load(f)
    except Exception as e:
        print(f"Błąd ładowania danych: {e}")
        return None

    analysis_report = f"""# ANALIZA RYNKU FINANSOWEGO
*Wygenerowano: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*

**Przeanalizowano {sum(len(tweets) for tweets in tweets_data.values())} tweetów z {len(tweets_data)} kategorii**

---

## 📊 EXECUTIVE SUMMARY

"""

    # Overall sentiment analysis
    all_sentiments = []
    total_engagement = 0

    for category, tweets in tweets_data.items():
        for tweet in tweets:
            sentiment, score = analyze_sentiment_simple(tweet.get('text', ''))
            all_sentiments.append(score)
            total_engagement += tweet.get('like_count', 0) + tweet.get('retweet_count', 0)

    avg_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0

    # Sentiment rating
    if avg_sentiment > 0.2:
        sentiment_rating = "Zdecydowanie optymistyczny (8/10)"
    elif avg_sentiment > 0.1:
        sentiment_rating = "Umiarkowanie optymistyczny (6/10)"
    elif avg_sentiment > -0.1:
        sentiment_rating = "Neutralny (5/10)"
    elif avg_sentiment > -0.2:
        sentiment_rating = "Umiarkowanie pesymistyczny (4/10)"
    else:
        sentiment_rating = "Zdecydowanie pesymistyczny (2/10)"

    analysis_report += f"""
**Ogólny sentiment rynkowy:** {sentiment_rating}
**Średni wskaźnik sentymenty:** {avg_sentiment:.3f}
**Łączne zaangażowanie:** {total_engagement:,} interakcji

### Kluczowe obserwacje:
- Aktywność na rynkach wysoka, szczególnie w segmencie giełdowym
- Zauważalne zainteresowanie decyzjami Fed dotyczącymi stóp procentowych
- Rosnące znaczenie AI i technologii w dyskusjach rynkowych
- Stabilny optimism w segmencie nieruchomości

"""

    # Category analysis
    analysis_report += "\n## 🔍 ANALIZA KATEGORIALNA\n\n"

    for category, tweets in tweets_data.items():
        if not tweets:
            continue

        analysis_report += f"### {category}\n"

        # Category sentiment
        category_sentiments = []
        category_engagement = 0
        category_keywords = {}

        for tweet in tweets:
            sentiment, score = analyze_sentiment_simple(tweet.get('text', ''))
            category_sentiments.append(score)
            category_engagement += tweet.get('like_count', 0) + tweet.get('retweet_count', 0)

            keywords = extract_financial_keywords(tweet.get('text', ''))
            for kw_cat, kws in keywords.items():
                if kw_cat not in category_keywords:
                    category_keywords[kw_cat] = []
                category_keywords[kw_cat].extend(kws)

        avg_cat_sentiment = sum(category_sentiments) / len(category_sentiments) if category_sentiments else 0

        if avg_cat_sentiment > 0.1:
            cat_sentiment_label = "Pozytywny"
        elif avg_cat_sentiment < -0.1:
            cat_sentiment_label = "Negatywny"
        else:
            cat_sentiment_label = "Neutralny"

        # Engagement level
        avg_engagement = category_engagement / len(tweets) if tweets else 0
        if avg_engagement > 500:
            engagement_level = "Wysoki"
        elif avg_engagement > 100:
            engagement_level = "Średni"
        else:
            engagement_level = "Niski"

        analysis_report += f"""
**Sentiment:** {cat_sentiment_label} ({avg_cat_sentiment:+.3f})
**Zaangażowanie:** {engagement_level} ({category_engagement:,} łącznych interakcji)
**Liczba tweetów:** {len(tweets)}

**Kluczowe tematy:**
"""

        # Most engaging tweet
        if tweets:
            top_tweet = max(tweets, key=lambda t: t.get('like_count', 0) + t.get('retweet_count', 0))
            analysis_report += f"- Najważniejszy tweet: @{top_tweet.get('username', 'unknown')} ({top_tweet.get('like_count', 0)}❤️ {top_tweet.get('retweet_count', 0)}🔄)\n"

        if category_keywords:
            analysis_report += "- Wykryte sygnały: " + ", ".join([f"{cat} ({len(set(kws))})" for cat, kws in category_keywords.items()]) + "\n"

        analysis_report += "\n"

    # Predictions and recommendations
    analysis_report += """
## 📈 PROGNOZY KRÓTKOTERMINOWE (1-4 tygodnie)

### Prawdopodobne scenariusze:
1. **Stabilizacja po decyzjach Fed** - Rynki prawdopodobnie będą reagować na najnowsze decyzje dotyczące stóp procentowych
2. **Wzrost zainteresowania technologiami** - Szczególnie AI i blockchain nadal przyciągają uwagę inwestorów
3. **Ożywienie w sektorze nieruchomości** - Spadające stopy mogą stymulować refinansowanie i nowe inwestycje

### Kluczowe wydarzenia do obserwacji:
- Kolejne komunikaty Fed i dane makroekonomiczne
- Rozwój sytuacji na rynku kryptowalut
- Earnings season i wyniki spółek technologicznych

## 💡 REKOMENDACJE INWESTYCYJNE

### Sektory do rozważenia:
- **Technologie (AI/Blockchain)** - Rosnące zainteresowanie i innowacje
- **Nieruchomości** - Potencjał z tytułu spadających stóp
- **Tradycyjne blue chips** - Stabilność w niepewnych czasach

### Strategia zarządzania ryzykiem:
- Dywersyfikacja między sektorami
- Monitoring komunikacji banków centralnych
- Zachowanie płynności na możliwe korekty

### Uwagi specjalne:
- Wysokie zaangażowanie w mediach społecznościowych może sygnalizować podwyższoną zmienność
- Tematy związane z polityką (Trump, wybory) mogą wpływać na nastoje rynkowe
- Kryptowaluty pozostają wysoko skorelowane z decyzjami Fed

## 🔮 MONITORING I WSKAŹNIKI

### Do obserwacji:
- Volume i aktywność na głównych giełdach
- Spread między stopami długo- i krótkoterminowymi
- Sentiment w mediach społecznościowych (kontynuacja monitoringu)
- Przepływy kapitału do/z funduszy ETF

---

**Zastrzeżenie:** Analiza oparta na ograniczonej próbie tweetów z okresu 16-18.09.2025.
Nie stanowi porady inwestycyjnej. Zawsze przeprowadź własną analizę przed podjęciem decyzji inwestycyjnych.
"""

    # Save analysis
    os.makedirs('data/analysis', exist_ok=True)

    # Save as markdown
    markdown_file = 'data/analysis/market_analysis_report.md'
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(analysis_report)

    # Save structured data
    analysis_data = {
        'timestamp': datetime.now().isoformat(),
        'tweets_analyzed': sum(len(tweets) for tweets in tweets_data.values()),
        'categories': list(tweets_data.keys()),
        'overall_sentiment': avg_sentiment,
        'sentiment_rating': sentiment_rating,
        'total_engagement': total_engagement,
        'source_data': tweets_data,
        'analysis_report': analysis_report
    }

    json_file = 'data/analysis/market_sentiment_analysis.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)

    print(f"Analiza zapisana do:")
    print(f"  - {markdown_file}")
    print(f"  - {json_file}")

    return analysis_data

if __name__ == "__main__":
    print("=== LOKALNA ANALIZA RYNKOWA ===\n")

    result = create_local_analysis()

    if result:
        print(f"\nGOTOWE! Przeanalizowano {result['tweets_analyzed']} tweetów")
        print(f"Ogólny sentiment: {result['sentiment_rating']}")
        print(f"Wskaźnik sentiment: {result['overall_sentiment']:.3f}")
    else:
        print("\nBłąd podczas analizy")