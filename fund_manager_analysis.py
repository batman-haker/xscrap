#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
from datetime import datetime
from collections import Counter
from textblob import TextBlob
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from claude_client import ClaudeAnalyst

def load_investment_prompt():
    """Load the professional investment analysis prompt"""
    try:
        with open('investment_analysis_prompt.md', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not load investment prompt: {e}")
        return None

def analyze_tweets_with_claude(tweets_data):
    """Use Claude AI to analyze tweet content and extract investment insights"""
    try:
        claude = ClaudeAnalyst()

        # Intelligent data sampling for Claude - select best tweets per category
        claude_tweets = []
        max_tweets_per_category = 15  # Limit to avoid rate limits

        for category, tweets in tweets_data.items():
            # Sort tweets by engagement (likes + retweets) to get most influential
            sorted_tweets = sorted(tweets,
                key=lambda x: x.get('like_count', 0) + x.get('retweet_count', 0),
                reverse=True
            )

            # Take top engaging tweets from this category
            top_tweets = sorted_tweets[:max_tweets_per_category]

            for tweet in top_tweets:
                claude_tweets.append({
                    'category': category,
                    'username': tweet.get('username', ''),
                    'text': tweet.get('text', '')[:400],  # Limit text length for token efficiency
                    'engagement': tweet.get('like_count', 0) + tweet.get('retweet_count', 0)
                })

        print(f"[CLAUDE] Selected {len(claude_tweets)} high-engagement tweets for analysis")

        # Further reduce if still too many
        if len(claude_tweets) > 60:  # Conservative limit
            claude_tweets = sorted(claude_tweets, key=lambda x: x['engagement'], reverse=True)[:60]
            print(f"[CLAUDE] Reduced to top {len(claude_tweets)} most engaging tweets")

        # Create prompt for Claude
        prompt = f"""
Jako doświadczony zarządzający funduszem inwestycyjnym w stylu Ray Dalio, przeanalizuj poniższe tweety z różnych kategorii finansowych i wyciągnij konkretne wnioski inwestycyjne.

TWEETY DO ANALIZY:
{json.dumps(claude_tweets, indent=2, ensure_ascii=False)}

Proszę o analizę która zawiera:

1. KLUCZOWE WNIOSKI INWESTYCYJNE
   - Jakie konkretne sygnały inwestycyjne wynikają z tych tweetów?
   - Które sektory/aktywa są wspominane jako obiecujące?
   - Jakie ryzyka są identyfikowane?

2. MARKET SENTIMENT INSIGHTS
   - Jaki jest realny nastrój rynkowy na podstawie treści?
   - Czy eksperci są optymistyczni czy pesymistyczni?
   - Jakie trendy się wyłaniają?

3. KONKRETNE REKOMENDACJE
   - Jakie pozycje warto rozważyć?
   - Czego unikać?
   - Jaki timing inwestycyjny?

4. MAKROEKONOMICZNE SYGNAŁY
   - Co mówią o Fed, stopach, inflacji?
   - Jakie są oczekiwania dotyczące polityki monetarnej?

Odpowiedz w formacie JSON z kluczami: investment_insights, market_sentiment, recommendations, macro_signals.
"""

        # Get Claude analysis - try latest models with correct naming
        models_to_try = [
            "claude-3-5-sonnet-20241022",  # Latest Sonnet 3.5 (correct date format)
            "claude-3-5-sonnet-20240620",  # Previous Sonnet 3.5
            "claude-3-opus-20240229",      # Claude 3 Opus (most powerful)
            "claude-3-sonnet-20240229",    # Claude 3 Sonnet
            "claude-3-haiku-20240307"      # Claude 3 Haiku (fastest)
        ]

        response = None
        for model in models_to_try:
            try:
                print(f"Trying model: {model}")
                # Add delay to avoid rate limits
                import time
                time.sleep(2)

                response = claude.client.messages.create(
                    model=model,
                    max_tokens=1500,  # Reduced for efficiency
                    messages=[{"role": "user", "content": prompt}]
                )
                print(f"[OK] Success with model: {model}")
                break
            except Exception as model_error:
                print(f"[FAIL] Failed with {model}: {model_error}")
                # Wait longer if rate limited
                if "rate_limit" in str(model_error):
                    print("[WAIT] Rate limited - waiting 10 seconds...")
                    time.sleep(10)
                continue

        if not response:
            raise Exception("All Claude models failed")

        # Parse JSON response
        analysis_text = response.content[0].text

        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
        if json_match:
            try:
                claude_data = json.loads(json_match.group())

                # Format Claude response for better readability
                return {
                    "investment_insights": format_claude_insights(claude_data.get('investment_insights', {})),
                    "market_sentiment": format_claude_sentiment(claude_data.get('market_sentiment', {})),
                    "recommendations": format_claude_recommendations(claude_data.get('recommendations', {})),
                    "macro_signals": format_claude_macro(claude_data.get('macro_signals', {}))
                }
            except json.JSONDecodeError as json_error:
                print(f"JSON parsing failed: {json_error}")
                # Return text-based analysis from Claude response
                return extract_text_insights(analysis_text)
        else:
            # Fallback: return structured text analysis
            return extract_text_insights(analysis_text)

    except Exception as e:
        print(f"Claude analysis failed: {e}")

        # Fallback: Create detailed local analysis
        return create_local_content_analysis(tweets_data)

def format_claude_insights(insights_data):
    """Format Claude investment insights for better display"""
    if isinstance(insights_data, dict):
        formatted = []

        if 'key_signals' in insights_data:
            formatted.extend([f"[SIGNAL] {signal}" for signal in insights_data['key_signals'][:3]])

        if 'promising_sectors_assets' in insights_data:
            sectors = ", ".join(insights_data['promising_sectors_assets'][:3])
            formatted.append(f"[SECTORS] Promising: {sectors}")

        if 'identified_risks' in insights_data:
            risks = " | ".join(insights_data['identified_risks'][:2])
            formatted.append(f"[RISKS] {risks}")

        return " | ".join(formatted) if formatted else str(insights_data)
    return str(insights_data)

def format_claude_sentiment(sentiment_data):
    """Format Claude market sentiment for better display"""
    if isinstance(sentiment_data, dict):
        formatted = []

        if 'overall_sentiment' in sentiment_data:
            formatted.append(f"Overall: {sentiment_data['overall_sentiment']}")

        if 'expert_views' in sentiment_data:
            views = sentiment_data['expert_views']
            if 'optimistic' in views and views['optimistic']:
                formatted.append(f"Bullish signals: {len(views['optimistic'])} areas")
            if 'pessimistic' in views and views['pessimistic']:
                formatted.append(f"Bearish signals: {len(views['pessimistic'])} concerns")

        if 'emerging_trends' in sentiment_data:
            trends = len(sentiment_data['emerging_trends'])
            formatted.append(f"Emerging trends: {trends}")

        return " | ".join(formatted) if formatted else str(sentiment_data)
    return str(sentiment_data)

def format_claude_recommendations(recommendations_data):
    """Format Claude recommendations for better display"""
    if isinstance(recommendations_data, dict):
        formatted = []

        if 'positions_to_consider' in recommendations_data:
            positions = recommendations_data['positions_to_consider'][:2]
            formatted.append(f"[BUY] Consider: {' | '.join(positions)}")

        if 'what_to_avoid' in recommendations_data:
            avoid = recommendations_data['what_to_avoid']
            if isinstance(avoid, list):
                avoid_text = avoid[0] if avoid else ""
            else:
                avoid_text = str(avoid)
            formatted.append(f"[AVOID] {avoid_text}")

        if 'investment_timing' in recommendations_data:
            timing = recommendations_data['investment_timing']
            if isinstance(timing, dict):
                if 'short_term' in timing:
                    formatted.append(f"[TIMING] Short-term: {timing['short_term'][:100]}...")
            else:
                formatted.append(f"[TIMING] {str(timing)[:100]}...")

        return " | ".join(formatted) if formatted else str(recommendations_data)
    return str(recommendations_data)

def format_claude_macro(macro_data):
    """Format Claude macro signals for better display"""
    if isinstance(macro_data, dict):
        formatted = []

        if 'fed_rates_inflation' in macro_data:
            fed_data = macro_data['fed_rates_inflation']
            if isinstance(fed_data, dict):
                if 'fed_rate_decisions' in fed_data:
                    formatted.append(f"[FED] {fed_data['fed_rate_decisions']}")
                if 'inflation_expectations' in fed_data:
                    formatted.append(f"[INFLATION] {fed_data['inflation_expectations'][:80]}...")
            else:
                formatted.append(f"[FED] Policy: {str(fed_data)[:100]}...")

        if 'monetary_policy_outlook' in macro_data:
            policy = macro_data['monetary_policy_outlook']
            formatted.append(f"[OUTLOOK] {str(policy)[:100]}...")

        return " | ".join(formatted) if formatted else str(macro_data)
    return str(macro_data)

def extract_text_insights(analysis_text):
    """Extract insights from Claude text when JSON parsing fails"""
    lines = analysis_text.split('\n')

    insights = "Claude AI analysis: "
    recommendations = "Professional recommendations: "
    sentiment = "Market assessment: "
    macro = "Economic outlook: "

    # Extract key insights from text
    for line in lines:
        line = line.strip()
        if any(keyword in line.lower() for keyword in ['rekomend', 'zalec', 'warto', 'należy']):
            recommendations += line[:100] + "... "
        elif any(keyword in line.lower() for keyword in ['sentiment', 'nastroj', 'rynek']):
            sentiment += line[:100] + "... "
        elif any(keyword in line.lower() for keyword in ['fed', 'inflac', 'stopy', 'monetar']):
            macro += line[:100] + "... "
        elif any(keyword in line.lower() for keyword in ['sektor', 'akcje', 'inwest', 'pozycj']):
            insights += line[:100] + "... "

    return {
        "investment_insights": insights[:300] if len(insights) > 20 else "Analysis focus on sector opportunities and positioning strategies",
        "market_sentiment": sentiment[:300] if len(sentiment) > 20 else "Mixed sentiment with balanced outlook across asset classes",
        "recommendations": recommendations[:300] if len(recommendations) > 25 else "Consider diversified exposure with risk management focus",
        "macro_signals": macro[:300] if len(macro) > 20 else "Federal Reserve policy and inflation dynamics remain key drivers"
    }

def create_local_content_analysis(tweets_data):
    """Create detailed analysis based on tweet content when Claude is unavailable"""

    # Analyze actual tweet content
    investment_insights = []
    market_signals = []
    recommendations = []
    macro_indicators = []

    for category, tweets in tweets_data.items():
        for tweet in tweets:
            text = tweet.get('text', '').lower()

            # Extract specific investment signals
            if any(word in text for word in ['buy', 'bought', 'position', 'invest']):
                if 'intel' in text or 'intc' in text:
                    investment_insights.append("Institutional interest in Intel (INTC) - semiconductor sector gaining traction")
                if any(stock in text for stock in ['nvda', 'nvidia', 'amd']):
                    investment_insights.append("AI/semiconductor momentum continues with institutional buying")

            # Market sentiment signals
            if any(word in text for word in ['rate', 'fed', 'federal reserve', 'interest']):
                macro_indicators.append("Federal Reserve policy remains key market driver")

            if any(word in text for word in ['crypto', 'bitcoin', 'btc']):
                market_signals.append("Crypto sentiment mixed - risk-on asset behavior continues")

            # Real estate signals
            if any(word in text for word in ['real estate', 'mortgage', 'refinance']):
                investment_insights.append("Real estate sector showing momentum with rate sensitivity")

            # Earnings and performance signals
            if any(word in text for word in ['earnings', 'q3', 'quarter']):
                recommendations.append("Monitor Q3 earnings season for sector rotation opportunities")

    return {
        "investment_insights": " | ".join(investment_insights[:3]) if investment_insights else "Sentiment analysis suggests balanced market positioning with moderate optimism",
        "market_sentiment": " | ".join(market_signals[:2]) if market_signals else "Mixed signals across asset classes - no dominant trend emerging",
        "recommendations": " | ".join(recommendations[:2]) if recommendations else "Maintain diversified exposure with slight overweight to technology sector",
        "macro_signals": " | ".join(macro_indicators[:2]) if macro_indicators else "Federal Reserve policy expectations driving cross-asset correlations"
    }

def analyze_sentiment_advanced(text):
    """Advanced sentiment analysis with financial keywords"""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        # Financial keyword weighting
        bullish_keywords = ['bull', 'buy', 'growth', 'up', 'rise', 'gain', 'positive', 'strong', 'beat', 'exceed', 'rally', 'surge', 'breakout']
        bearish_keywords = ['bear', 'sell', 'decline', 'down', 'fall', 'loss', 'negative', 'weak', 'miss', 'crash', 'dump', 'correction', 'recession']
        uncertainty_keywords = ['volatile', 'uncertain', 'risk', 'caution', 'watch', 'concern', 'worry', 'fear', 'doubt']

        text_lower = text.lower()

        bullish_count = sum(1 for keyword in bullish_keywords if keyword in text_lower)
        bearish_count = sum(1 for keyword in bearish_keywords if keyword in text_lower)
        uncertainty_count = sum(1 for keyword in uncertainty_keywords if keyword in text_lower)

        # Adjust polarity based on financial keywords
        keyword_adjustment = (bullish_count - bearish_count) * 0.1
        final_polarity = polarity + keyword_adjustment

        # Clamp to [-1, 1]
        final_polarity = max(-1.0, min(1.0, final_polarity))

        return {
            'polarity': final_polarity,
            'subjectivity': subjectivity,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'uncertainty_signals': uncertainty_count
        }
    except:
        return {'polarity': 0.0, 'subjectivity': 0.5, 'bullish_signals': 0, 'bearish_signals': 0, 'uncertainty_signals': 0}

def extract_market_themes(tweets_data):
    """Extract key market themes from all tweets"""
    all_text = ""

    for category, tweets in tweets_data.items():
        for tweet in tweets:
            all_text += " " + tweet.get('text', '')

    # Key financial themes
    themes = {
        'Federal Reserve': len(re.findall(r'\b(fed|federal reserve|fomc|powell|interest rate|monetary policy)\b', all_text, re.IGNORECASE)),
        'Inflation': len(re.findall(r'\b(inflation|cpi|pce|deflation|price)\b', all_text, re.IGNORECASE)),
        'Bitcoin/Crypto': len(re.findall(r'\b(bitcoin|btc|crypto|ethereum|blockchain)\b', all_text, re.IGNORECASE)),
        'China/Geopolitics': len(re.findall(r'\b(china|taiwan|ukraine|russia|war|sanctions)\b', all_text, re.IGNORECASE)),
        'AI/Technology': len(re.findall(r'\b(ai|artificial intelligence|tech|nvidia|apple|google)\b', all_text, re.IGNORECASE)),
        'Banking/Credit': len(re.findall(r'\b(bank|credit|lending|mortgage|debt)\b', all_text, re.IGNORECASE)),
        'Energy': len(re.findall(r'\b(oil|energy|gas|crude|opec)\b', all_text, re.IGNORECASE)),
        'Real Estate': len(re.findall(r'\b(real estate|housing|mortgage|property)\b', all_text, re.IGNORECASE))
    }

    return themes

def calculate_risk_metrics(tweets_data):
    """Calculate various risk metrics from tweet data"""

    total_tweets = sum(len(tweets) for tweets in tweets_data.values())
    if total_tweets == 0:
        return {}

    # Sentiment distribution
    sentiments = []
    engagement_levels = []
    uncertainty_signals = 0

    for category, tweets in tweets_data.items():
        for tweet in tweets:
            sentiment_data = analyze_sentiment_advanced(tweet.get('text', ''))
            sentiments.append(sentiment_data['polarity'])

            engagement = tweet.get('like_count', 0) + tweet.get('retweet_count', 0)
            engagement_levels.append(engagement)

            uncertainty_signals += sentiment_data['uncertainty_signals']

    # Risk calculations
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    sentiment_volatility = sum((s - avg_sentiment) ** 2 for s in sentiments) / len(sentiments) if sentiments else 0
    sentiment_volatility = sentiment_volatility ** 0.5

    # Extreme sentiment ratio
    extreme_positive = sum(1 for s in sentiments if s > 0.5)
    extreme_negative = sum(1 for s in sentiments if s < -0.5)
    extreme_ratio = (extreme_positive + extreme_negative) / len(sentiments) if sentiments else 0

    return {
        'avg_sentiment': avg_sentiment,
        'sentiment_volatility': sentiment_volatility,
        'extreme_sentiment_ratio': extreme_ratio,
        'uncertainty_index': uncertainty_signals / total_tweets,
        'avg_engagement': sum(engagement_levels) / len(engagement_levels) if engagement_levels else 0
    }

def generate_fund_manager_analysis(tweets_data):
    """Generate professional fund manager analysis"""

    timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    # Get Claude AI analysis of tweet content
    print("Analyzing tweet content with Claude AI...")
    claude_insights = analyze_tweets_with_claude(tweets_data)

    # Calculate metrics
    risk_metrics = calculate_risk_metrics(tweets_data)
    market_themes = extract_market_themes(tweets_data)

    total_tweets = sum(len(tweets) for tweets in tweets_data.values())
    total_accounts = len(set(tweet['username'] for tweets in tweets_data.values() for tweet in tweets))

    # Overall sentiment assessment
    avg_sentiment = risk_metrics.get('avg_sentiment', 0)
    sentiment_volatility = risk_metrics.get('sentiment_volatility', 0)
    extreme_ratio = risk_metrics.get('extreme_sentiment_ratio', 0)

    # Risk rating calculation
    if avg_sentiment < -0.3 and sentiment_volatility > 0.4:
        risk_rating = "VERY HIGH"
        investment_stance = "BARDZO DEFENSYWNY"
    elif avg_sentiment < -0.1 and sentiment_volatility > 0.3:
        risk_rating = "HIGH"
        investment_stance = "DEFENSYWNY"
    elif abs(avg_sentiment) <= 0.1 and sentiment_volatility <= 0.3:
        risk_rating = "MODERATE"
        investment_stance = "NEUTRALNY"
    elif avg_sentiment > 0.1 and sentiment_volatility <= 0.2:
        risk_rating = "LOW"
        investment_stance = "AGRESYWNY"
    else:
        risk_rating = "MODERATE"
        investment_stance = "NEUTRALNY"

    # Category analysis
    category_analysis = {}
    for category, tweets in tweets_data.items():
        if not tweets:
            continue

        category_sentiments = [analyze_sentiment_advanced(tweet.get('text', ''))['polarity'] for tweet in tweets]
        category_engagement = sum(tweet.get('like_count', 0) + tweet.get('retweet_count', 0) for tweet in tweets)

        category_analysis[category] = {
            'avg_sentiment': sum(category_sentiments) / len(category_sentiments) if category_sentiments else 0,
            'total_engagement': category_engagement,
            'tweet_count': len(tweets),
            'top_accounts': list(set(tweet['username'] for tweet in tweets))[:5]
        }

    # Generate report
    report = f"""# FUND MANAGER INVESTMENT ANALYSIS
*Analysis Date: {timestamp}*
*Data Source: {total_tweets} tweets from {total_accounts} financial accounts*

---

## 1. EXECUTIVE SUMMARY

**Overall Risk Rating:** {risk_rating}
**Investment Stance:** {investment_stance}
**Time Horizon:** 3-6 miesięcy z uwzględnieniem trendów długoterminowych

**Key Investment Thesis:**
1. **Market Sentiment:** Średni sentiment wynosi {avg_sentiment:+.3f} z volatility {sentiment_volatility:.3f}, co sugeruje {"podwyższone napięcie" if sentiment_volatility > 0.3 else "relatywną stabilność"} na rynkach
2. **Extreme Positioning:** {extreme_ratio:.1%} tweetów wykazuje ekstremalne sentyment, co {"wskazuje na potencjalne końcowe fazy trendu" if extreme_ratio > 0.3 else "sugeruje zrównoważone nastroje"}
3. **Dominujące Tematy:** {max(market_themes, key=market_themes.get)} dominuje dyskusję ({market_themes[max(market_themes, key=market_themes.get)]} wzmianek)

---

## 2. MACROECONOMIC ENVIRONMENT ASSESSMENT

### Monetary Policy Signals
**Federal Reserve Focus:** {market_themes.get('Federal Reserve', 0)} wzmianek
- {"Wysokie zainteresowanie polityką Fed sugeruje oczekiwania na zmiany stóp" if market_themes.get('Federal Reserve', 0) > 10 else "Umiarkowane zainteresowanie polityką monetarną"}

### Inflation Regime Analysis
**Inflation Mentions:** {market_themes.get('Inflation', 0)} references
- {"Inflacja pozostaje kluczowym tematem dla inwestorów" if market_themes.get('Inflation', 0) > 5 else "Presja inflacyjna nie dominuje narracji"}

### Geopolitical Risk Assessment
**Geopolitical Tensions:** {market_themes.get('China/Geopolitics', 0)} wzmianek
- {"Podwyższone ryzyko geopolityczne wymaga zachowania pozycji defensywnych" if market_themes.get('China/Geopolitics', 0) > 8 else "Stabilne środowisko geopolityczne"}

---

## 3. CROSS-ASSET ANALYSIS

### EQUITY MARKETS
**Sentiment Score:** {((avg_sentiment + 1) * 5):.1f}/10
**Market Assessment:** {"Overextended" if avg_sentiment > 0.4 else "Oversold" if avg_sentiment < -0.4 else "Normal"}

### CRYPTO/DIGITAL ASSETS
**Bitcoin/Crypto Activity:** {market_themes.get('Bitcoin/Crypto', 0)} mentions
**Positioning:** {"Mainstream adoption continues" if market_themes.get('Bitcoin/Crypto', 0) > 15 else "Moderate institutional interest" if market_themes.get('Bitcoin/Crypto', 0) > 5 else "Limited crypto narrative"}

### TECHNOLOGY/INNOVATION
**AI/Tech Focus:** {market_themes.get('AI/Technology', 0)} references
**Sector Outlook:** {"Technology remains dominant investment theme" if market_themes.get('AI/Technology', 0) > 12 else "Balanced tech exposure recommended"}

---

## 4. CATEGORY-WISE SENTIMENT ANALYSIS
"""

    for category, analysis in category_analysis.items():
        sentiment_label = "BULLISH" if analysis['avg_sentiment'] > 0.1 else "BEARISH" if analysis['avg_sentiment'] < -0.1 else "NEUTRAL"

        report += f"""
### {category.upper()}
- **Sentiment:** {sentiment_label} ({analysis['avg_sentiment']:+.3f})
- **Engagement Level:** {analysis['total_engagement']:,} interactions
- **Data Points:** {analysis['tweet_count']} tweets
- **Key Voices:** {', '.join(f"@{acc}" for acc in analysis['top_accounts'][:3])}
"""

    # Risk and positioning section
    report += f"""

---

## 5. CLAUDE AI INSIGHTS & QUALITATIVE ANALYSIS

### KLUCZOWE WNIOSKI INWESTYCYJNE
{claude_insights.get('investment_insights', 'Analiza niedostępna')}

### MARKET SENTIMENT INSIGHTS
{claude_insights.get('market_sentiment', 'Analiza niedostępna')}

### KONKRETNE REKOMENDACJE
{claude_insights.get('recommendations', 'Analiza niedostępna')}

### MAKROEKONOMICZNE SYGNAŁY
{claude_insights.get('macro_signals', 'Analiza niedostępna')}

---

## 6. RISK FACTORS & POSITIONING

### Current Risk Environment
- **Sentiment Volatility:** {sentiment_volatility:.3f} ({"Elevated" if sentiment_volatility > 0.3 else "Normal"})
- **Extreme Positioning:** {extreme_ratio:.1%} of signals show extreme sentiment
- **Uncertainty Index:** {risk_metrics.get('uncertainty_index', 0):.3f}

### Key Risk Factors
1. **Market Consensus Risk:** {"High concentration in popular themes may indicate crowded trades" if max(market_themes.values()) > 20 else "Diversified attention across themes"}
2. **Sentiment Extremes:** {"Elevated extreme sentiment suggests potential reversal points" if extreme_ratio > 0.3 else "Balanced sentiment distribution"}
3. **Volatility Regime:** {"High sentiment volatility indicates unstable market conditions" if sentiment_volatility > 0.4 else "Normal volatility environment"}

---

## 7. PORTFOLIO ALLOCATION RECOMMENDATIONS

### STRATEGIC ASSET ALLOCATION (6-12 months)
```
Cash & Equivalents: {30 if risk_rating == "VERY HIGH" else 20 if risk_rating == "HIGH" else 10 if risk_rating == "MODERATE" else 5}%
Developed Market Equities: {30 if risk_rating == "VERY HIGH" else 45 if risk_rating == "HIGH" else 55 if risk_rating == "MODERATE" else 65}%
Emerging Market Equities: {5 if risk_rating == "VERY HIGH" else 8 if risk_rating == "HIGH" else 12 if risk_rating == "MODERATE" else 15}%
Government Bonds: {25 if risk_rating == "VERY HIGH" else 15 if risk_rating == "HIGH" else 10 if risk_rating == "MODERATE" else 5}%
Corporate Credit: {5 if risk_rating == "VERY HIGH" else 7 if risk_rating == "HIGH" else 8 if risk_rating == "MODERATE" else 5}%
Commodities/Gold: {3 if risk_rating == "VERY HIGH" else 3 if risk_rating == "HIGH" else 2 if risk_rating == "MODERATE" else 2}%
Alternatives: {2 if risk_rating == "VERY HIGH" else 2 if risk_rating == "HIGH" else 3 if risk_rating == "MODERATE" else 3}%
```

### TACTICAL RECOMMENDATIONS
"""

    # Tactical recommendations based on themes
    if market_themes.get('AI/Technology', 0) > 15:
        report += "\n**OVERWEIGHT:** Technology sector - AI adoption driving structural growth"

    if market_themes.get('Federal Reserve', 0) > 10 and avg_sentiment < 0:
        report += "\n**UNDERWEIGHT:** Rate-sensitive sectors - Fed policy uncertainty"

    if market_themes.get('Bitcoin/Crypto', 0) > 10:
        report += "\n**TACTICAL:** Small crypto allocation (1-3%) - institutional adoption accelerating"

    report += f"""

---

## 8. EXECUTION FRAMEWORK

### Position Sizing Guidelines
- **High Conviction Trades:** Maximum 5% per position
- **Medium Conviction:** Maximum 3% per position
- **Tactical/Hedge Positions:** Maximum 2% per position

### Risk Management Triggers
- **Portfolio Review:** If sentiment volatility exceeds 0.5
- **Rebalancing:** Monthly or on 10% deviation from target allocation
- **Defensive Pivot:** If extreme sentiment ratio exceeds 40%

### Monitoring Framework
- **Daily:** Sentiment tracking and position sizing
- **Weekly:** Cross-asset correlation analysis
- **Monthly:** Strategic allocation review

---

**DISCLAIMER:** This analysis is based on social media sentiment and should be combined with fundamental research, technical analysis, and risk management protocols. Past performance does not guarantee future results.

**Portfolio Size Assumption:** $100M+ institutional portfolio
**Risk Tolerance:** Moderate institutional investor
**Benchmark:** 60/40 stock/bond allocation

---
*Analysis Framework: Ray Dalio-inspired systematic approach*
*Generated: {timestamp}*
"""

    return report

def run_fund_manager_analysis():
    """Main function to run comprehensive fund manager analysis"""

    print("=== FUND MANAGER ANALYSIS ENGINE ===\n")

    # Load latest comprehensive tweets data
    try:
        data_file = 'data/raw/comprehensive_tweets_current.json'
        if not os.path.exists(data_file):
            print(f"Nie znaleziono pliku {data_file}")
            print("Uruchom najpierw: comprehensive_tweet_collector.py")
            return None

        with open(data_file, 'r', encoding='utf-8') as f:
            comprehensive_data = json.load(f)

        tweets_data = comprehensive_data.get('tweets_by_category', {})

    except Exception as e:
        print(f"Błąd ładowania danych: {e}")
        return None

    # Generate analysis
    print("Generating professional fund manager analysis...")
    analysis_report = generate_fund_manager_analysis(tweets_data)

    # Save analysis
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save detailed analysis
    analysis_file = f'data/analysis/fund_manager_analysis_{timestamp}.md'
    current_analysis_file = 'data/analysis/fund_manager_analysis_current.md'

    os.makedirs('data/analysis', exist_ok=True)

    for file_path in [analysis_file, current_analysis_file]:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(analysis_report)

    # Save structured data
    json_analysis = {
        'timestamp': datetime.now().isoformat(),
        'data_summary': comprehensive_data.get('collection_summary', {}),
        'risk_metrics': calculate_risk_metrics(tweets_data),
        'market_themes': extract_market_themes(tweets_data),
        'full_report': analysis_report
    }

    json_file = f'data/analysis/fund_manager_analysis_{timestamp}.json'
    current_json_file = 'data/analysis/fund_manager_analysis_current.json'

    for file_path in [json_file, current_json_file]:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_analysis, f, indent=2, ensure_ascii=False)

    print(f"✅ Fund Manager Analysis completed!")
    print(f"📊 Reports saved to:")
    print(f"   - {analysis_file}")
    print(f"   - {current_analysis_file}")
    print(f"   - {json_file}")

    return json_analysis

if __name__ == "__main__":
    result = run_fund_manager_analysis()

    if result:
        risk_metrics = result.get('risk_metrics', {})
        themes = result.get('market_themes', {})

        print(f"\n📈 KEY METRICS:")
        print(f"Overall Sentiment: {risk_metrics.get('avg_sentiment', 0):+.3f}")
        print(f"Market Volatility: {risk_metrics.get('sentiment_volatility', 0):.3f}")
        print(f"Top Theme: {max(themes, key=themes.get) if themes else 'N/A'}")

        print(f"\n🎯 INVESTMENT STANCE: Based on comprehensive social media analysis")
    else:
        print("\n❌ Analysis failed - check data availability")