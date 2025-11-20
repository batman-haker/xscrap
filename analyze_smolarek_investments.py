#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
from datetime import datetime
from collections import Counter

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_tweets_for_investments(json_file):
    """Analizuje tweety T_Smolarek pod kątem inwestycji"""

    print("="*80)
    print("ANALIZA INWESTYCYJNA TWEETÓW T_SMOLAREK")
    print("="*80)

    # Load tweets
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tweets = data.get('tweets', [])
    print(f"\nAnalizuję {len(tweets)} tweetów...\n")

    # 1. Extract stock tickers mentioned
    ticker_pattern = r'\$([A-Z]{1,5})'
    companies_mentioned = Counter()
    ticker_contexts = {}

    # 2. Topic analysis
    topics = {
        'AI': [],
        'Semiconductors': [],
        'Geopolitics': [],
        'China': [],
        'USA': [],
        'Europe': [],
        'Supply Chain': [],
        'Manufacturing': []
    }

    # 3. Companies and keywords
    company_keywords = {
        'NVIDIA': ['nvidia', '$nvda'],
        'ASML': ['asml'],
        'TSMC': ['tsmc', '$tsm'],
        'AMD': ['amd', '$amd'],
        'Intel': ['intel', '$intc'],
        'Qualcomm': ['qualcomm', '$qcom'],
        'Broadcom': ['broadcom', '$avgo'],
        'Applied Materials': ['applied materials', '$amat'],
        'Lam Research': ['lam research', '$lrcx'],
        'KLA': ['kla', '$klac'],
        'Synopsys': ['synopsys', '$snps'],
        'Cadence': ['cadence', '$cdns']
    }

    # 4. Sentiment indicators
    positive_indicators = ['wzrost', 'szansa', 'potencjał', 'pozytywn', 'dobrze', 'sukces', 'zysk']
    negative_indicators = ['ryzyko', 'zagrożenie', 'problem', 'spadek', 'kryzys', 'słabo']

    sentiment_scores = {}

    # Analyze each tweet
    for i, tweet in enumerate(tweets, 1):
        text = tweet.get('text', '')
        text_lower = text.lower()
        created_at = tweet.get('createdAt', 'N/A')

        # Extract tickers
        tickers = re.findall(ticker_pattern, text)
        for ticker in tickers:
            companies_mentioned[ticker] += 1
            if ticker not in ticker_contexts:
                ticker_contexts[ticker] = []
            ticker_contexts[ticker].append({
                'date': created_at,
                'text': text[:200],
                'likes': tweet.get('likeCount', 0),
                'views': tweet.get('viewCount', 0)
            })

        # Company mentions
        for company, keywords in company_keywords.items():
            if any(kw in text_lower for kw in keywords):
                companies_mentioned[company] += 1
                if company not in ticker_contexts:
                    ticker_contexts[company] = []
                ticker_contexts[company].append({
                    'date': created_at,
                    'text': text[:300],
                    'likes': tweet.get('likeCount', 0),
                    'views': tweet.get('viewCount', 0)
                })

        # Topic classification
        if any(word in text_lower for word in [' ai ', 'ai,', 'ai.', 'sztuczn', 'artificial']):
            topics['AI'].append(text[:200])

        if any(word in text_lower for word in ['chip', 'półprzewodnik', 'semiconductor', 'wafer', 'litograf']):
            topics['Semiconductors'].append(text[:200])

        if any(word in text_lower for word in ['chin', '🇨🇳', 'pekin']):
            topics['China'].append(text[:200])

        if any(word in text_lower for word in ['usa', '🇺🇸', 'ameryk', 'waszyngton']):
            topics['USA'].append(text[:200])

        if any(word in text_lower for word in ['europ', '🇪🇺', 'ue ', 'unii', 'bruksela']):
            topics['Europe'].append(text[:200])

        if any(word in text_lower for word in ['geopolit', 'handel', 'restrykcj', 'sankcj', 'wojna handlowa']):
            topics['Geopolitics'].append(text[:200])

        if any(word in text_lower for word in ['łańcuch dostaw', 'supply chain', 'produkcj', 'fabryka', 'manufacturing']):
            topics['Supply Chain'].append(text[:200])

    # Print analysis
    print("\n" + "="*80)
    print("1. NAJCZĘŚCIEJ WSPOMNIANE SPÓŁKI")
    print("="*80)

    for company, count in companies_mentioned.most_common(15):
        print(f"\n{company}: {count} wzmianek")

        if company in ticker_contexts and ticker_contexts[company]:
            latest = ticker_contexts[company][0]
            total_views = sum(ctx.get('views', 0) for ctx in ticker_contexts[company])
            total_likes = sum(ctx.get('likes', 0) for ctx in ticker_contexts[company])

            print(f"  Łączne wyświetlenia: {total_views:,}")
            print(f"  Łączne polubienia: {total_likes:,}")
            print(f"  Ostatnia wzmianka: {latest['date']}")
            print(f"  Kontekst: {latest['text'][:150]}...")

    print("\n" + "="*80)
    print("2. ANALIZA TEMATYCZNA")
    print("="*80)

    for topic, mentions in topics.items():
        if mentions:
            print(f"\n{topic}: {len(mentions)} tweetów")

    print("\n" + "="*80)
    print("3. KLUCZOWE WNIOSKI Z ANALIZY")
    print("="*80)

    # Analyze full text for key themes
    full_text = ' '.join([t.get('text', '') for t in tweets]).lower()

    print("\nGłówne tezy autora:")

    if 'asml' in full_text and 'euv' in full_text:
        print("\n✓ ASML i technologia EUV:")
        print("  - Podkreśla technologiczną dominację ASML w litografii EUV")
        print("  - Zachodnia inżynieria na najwyższym poziomie")
        print("  - Współpraca krajów zachodnich (NL, USA, DE, UK)")

    if 'chin' in full_text and any(word in full_text for word in ['dominuj', 'zagrożen', 'bezpieczeń']):
        print("\n⚠️ Zagrożenia z Chin:")
        print("  - Uzależnienie od chińskich dostaw (metale ziem rzadkich, proste chipy)")
        print("  - Ryzyko geopolityczne i weaponizacja łańcuchów dostaw")
        print("  - Potrzeba dywersyfikacji i onshoring'u")

    if 'nvidia' in full_text:
        print("\n✓ NVIDIA:")
        print("  - Lider w AI chips")
        print("  - Atrakcyjna wycena na PEG")
        print("  - Silny popyt przekraczający podaż")

    if 'bezpieczeńst' in full_text and 'gospodar' in full_text:
        print("\n✓ Bezpieczeństwo gospodarcze:")
        print("  - Bezpieczeństwo gospodarcze = bezpieczeństwo narodowe")
        print("  - Krytyka nadmiernej zależności od Chin")
        print("  - Potrzeba budowy własnych zdolności produkcyjnych")

    # Generate investment recommendations
    print("\n" + "="*80)
    print("4. REKOMENDACJE INWESTYCYJNE (na podstawie analizy)")
    print("="*80)

    recommendations = []

    # Based on mentions and context
    if companies_mentioned.get('NVIDIA', 0) > 0 or companies_mentioned.get('NVDA', 0) > 0:
        recommendations.append({
            'ticker': '$NVDA',
            'company': 'NVIDIA',
            'rating': 'KUP',
            'rationale': 'Atrakcyjna wycena na PEG, silny popyt na AI chips, pozycja lidera',
            'mentions': companies_mentioned.get('NVIDIA', 0) + companies_mentioned.get('NVDA', 0)
        })

    if companies_mentioned.get('ASML', 0) > 0:
        recommendations.append({
            'ticker': 'ASML',
            'company': 'ASML',
            'rating': 'KUP',
            'rationale': 'Monopol w EUV, niezbędne dla produkcji zaawansowanych chipów, wysoka bariera wejścia',
            'mentions': companies_mentioned.get('ASML', 0)
        })

    if companies_mentioned.get('TSMC', 0) > 0 or companies_mentioned.get('TSM', 0) > 0:
        recommendations.append({
            'ticker': '$TSM',
            'company': 'TSMC',
            'rating': 'KUP',
            'rationale': 'Największy foundry świata, kluczowy gracz w łańcuchu dostaw chipów',
            'mentions': companies_mentioned.get('TSMC', 0) + companies_mentioned.get('TSM', 0)
        })

    # Sector recommendations based on themes
    if len(topics['Semiconductors']) > 3:
        recommendations.append({
            'ticker': 'SEKTOR',
            'company': 'Semiconductor Equipment (ASML, AMAT, LRCX, KLAC)',
            'rating': 'KUP',
            'rationale': 'Autor koncentruje się na łańcuchu dostaw półprzewodników i equipment',
            'mentions': len(topics['Semiconductors'])
        })

    print("\nREKOMENDOWANE SPÓŁKI:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['company']} ({rec['ticker']})")
        print(f"   Rating: {rec['rating']}")
        print(f"   Wzmianki: {rec['mentions']}")
        print(f"   Uzasadnienie: {rec['rationale']}")

    # Additional sector plays based on themes
    print("\n\nDODATKOWE MOŻLIWOŚCI INWESTYCYJNE (wynikające z analiz autora):")

    print("\n📊 Sektor półprzewodników (Semiconductor Equipment):")
    print("   • Applied Materials ($AMAT) - equipment dla produkcji chipów")
    print("   • Lam Research ($LRCX) - etching i deposition equipment")
    print("   • KLA Corporation ($KLAC) - metrologia i inspekcja")

    print("\n📊 Western Reshoring / Onshoring:")
    print("   • Spółki budujące faby w USA/Europie")
    print("   • Intel ($INTC) - inwestycje w USA i Europę (ryzykowne)")
    print("   • GlobalFoundries ($GFS) - foundry w USA i Europie")

    print("\n⚠️ SPÓŁKI DO UNIKANIA (potencjalne ryzyka z analiz):")
    if len(topics['China']) > 2:
        print("   • Chińskie spółki chipowe - ryzyko geopolityczne, ograniczenia eksportowe")
        print("   • Spółki silnie uzależnione od chińskiego rynku")

    # Save detailed analysis
    output_file = f"data/analysis/smolarek_investment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs('data/analysis', exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'analyzed_at': datetime.now().isoformat(),
            'tweets_analyzed': len(tweets),
            'companies_mentioned': dict(companies_mentioned.most_common()),
            'topics': {k: len(v) for k, v in topics.items()},
            'recommendations': recommendations,
            'ticker_contexts': ticker_contexts
        }, f, indent=2, ensure_ascii=False)

    print(f"\n\n✓ Szczegółowa analiza zapisana do: {output_file}")

    return recommendations

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # Use the most recent file
        import glob
        files = glob.glob('data/raw/smolarek_all_tweets_*.json')
        if files:
            json_file = max(files)
        else:
            print("Nie znaleziono pliku z tweetami!")
            sys.exit(1)

    print(f"Analizuję plik: {json_file}\n")
    analyze_tweets_for_investments(json_file)
