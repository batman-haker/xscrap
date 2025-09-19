#!/usr/bin/env python3
"""
Smart Dashboard - Uses cached tweets, updates only on demand
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import glob
import sys
from datetime import datetime, timedelta
import time

# Configure Streamlit page
st.set_page_config(
    page_title="X Financial Analyzer - Smart",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}

.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #1f77b4;
    margin: 0.5rem 0;
}

.update-card {
    background-color: #e8f5e8;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #28a745;
    margin: 0.5rem 0;
}

.cache-info {
    background-color: #fff3cd;
    padding: 0.5rem;
    border-radius: 0.3rem;
    border-left: 3px solid #ffc107;
    font-size: 0.9em;
}
</style>
""", unsafe_allow_html=True)

def load_comprehensive_data():
    """Load comprehensive data with statistics"""
    try:
        comprehensive_file = 'data/raw/comprehensive_tweets_current.json'
        if os.path.exists(comprehensive_file):
            with open(comprehensive_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        return None
    except Exception as e:
        st.error(f"Błąd ładowania danych: {e}")
        return None

def load_custom_analysis(filename):
    """Load custom analysis files from project directory"""
    try:
        # Try local project directory first (for Streamlit Cloud)
        file_path = filename
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        # Fallback to C:/Xscrap/ for local development
        fallback_path = f'C:/Xscrap/{filename}'
        if os.path.exists(fallback_path):
            with open(fallback_path, 'r', encoding='utf-8') as f:
                return f.read()

        return None
    except Exception as e:
        st.error(f"Błąd ładowania {filename}: {e}")
        return None

def get_last_update_time():
    """Get last update time from comprehensive data"""
    data = load_comprehensive_data()
    if data:
        timestamp = data.get('timestamp', '')
        if timestamp:
            try:
                return datetime.fromisoformat(timestamp)
            except:
                pass
    return None

def format_analysis_text(analysis_text):
    """Format analysis text, especially if it contains JSON"""
    try:
        # Check if text contains JSON structure
        if '{' in analysis_text and '"sector_overview"' in analysis_text:
            # Find the start and end of JSON
            json_start = analysis_text.find('{\n    "sector_overview"')
            if json_start == -1:
                json_start = analysis_text.find('{"sector_overview"')

            if json_start != -1:
                intro_text = analysis_text[:json_start].strip()

                # Find the JSON end by looking for the closing brace before "Kluczowe obserwacje"
                remaining_text = analysis_text[json_start:]
                json_end_marker = '\n\nKluczowe obserwacje:'
                json_end = remaining_text.find(json_end_marker)

                if json_end != -1:
                    json_text = remaining_text[:json_end].strip()
                    conclusion_text = remaining_text[json_end:].strip()
                else:
                    # Fallback: try to find the last complete JSON structure
                    brace_count = 0
                    json_end = -1
                    for i, char in enumerate(remaining_text):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break

                    if json_end != -1:
                        json_text = remaining_text[:json_end]
                        conclusion_text = remaining_text[json_end:].strip()
                    else:
                        return analysis_text  # Fallback to original text

                try:
                    # Parse JSON
                    parsed_json = json.loads(json_text)

                    # Format as readable text
                    formatted = intro_text + "\n\n"

                    # Sector Overview
                    if 'sector_overview' in parsed_json:
                        overview = parsed_json['sector_overview']
                        formatted += f"## 📊 PRZEGLĄD SEKTORA: {overview.get('name', 'N/A')}\n\n"
                        formatted += f"- **Przeanalizowane tweety:** {overview.get('total_tweets', 0)}\n"
                        formatted += f"- **Unikalni autorzy:** {overview.get('unique_authors', 0)}\n"

                        if 'dominant_themes' in overview:
                            formatted += "- **Dominujące tematy:**\n"
                            for theme in overview['dominant_themes']:
                                formatted += f"  - {theme}\n"
                        formatted += "\n"

                    # Authors Analysis
                    if 'authors_analysis' in parsed_json:
                        formatted += "## 👥 ANALIZA AUTORÓW\n\n"
                        for author, analysis in parsed_json['authors_analysis'].items():
                            formatted += f"### @{author}\n"
                            formatted += f"**Poziom pewności:** {analysis.get('confidence_level', 'N/A')}\n\n"

                            if 'key_positions' in analysis:
                                formatted += "**Kluczowe stanowiska:**\n"
                                for pos in analysis['key_positions']:
                                    formatted += f"- {pos}\n"
                                formatted += "\n"

                            if 'unique_insights' in analysis:
                                formatted += "**Unikalne spostrzeżenia:**\n"
                                for insight in analysis['unique_insights']:
                                    formatted += f"- {insight}\n"
                                formatted += "\n"

                            if 'potential_biases' in analysis:
                                formatted += "**Potencjalne uprzedzenia:**\n"
                                for bias in analysis['potential_biases']:
                                    formatted += f"- {bias}\n"
                                formatted += "\n"

                    # Viewpoints Confrontation
                    if 'viewpoints_confrontation' in parsed_json:
                        conf = parsed_json['viewpoints_confrontation']
                        formatted += "## ⚔️ KONFRONTACJA POGLĄDÓW\n\n"

                        if 'major_agreements' in conf:
                            formatted += "**Główne zgodności:**\n"
                            for agreement in conf['major_agreements']:
                                formatted += f"- {agreement}\n"
                            formatted += "\n"

                        if 'major_disagreements' in conf:
                            formatted += "**Główne rozbieżności:**\n"
                            for disagreement in conf['major_disagreements']:
                                formatted += f"- {disagreement}\n"
                            formatted += "\n"

                        if 'synthesis' in conf:
                            formatted += f"**Synteza:** {conf['synthesis']}\n\n"

                    # Investment Implications
                    if 'investment_implications' in parsed_json:
                        impl = parsed_json['investment_implications']
                        formatted += "## 💼 IMPLIKACJE INWESTYCYJNE\n\n"

                        if 'actionable_insights' in impl:
                            formatted += "**Actionable Insights:**\n"
                            for insight in impl['actionable_insights']:
                                formatted += f"- {insight}\n"
                            formatted += "\n"

                        if 'contrarian_opportunities' in impl:
                            formatted += "**Okazje Contrarian:**\n"
                            for opp in impl['contrarian_opportunities']:
                                formatted += f"- {opp}\n"
                            formatted += "\n"

                        if 'risk_warnings' in impl:
                            formatted += "**Ostrzeżenia o ryzyku:**\n"
                            for warning in impl['risk_warnings']:
                                formatted += f"- {warning}\n"
                            formatted += "\n"

                    # Competitive Intelligence
                    if 'competitive_intelligence' in parsed_json:
                        ci = parsed_json['competitive_intelligence']
                        formatted += "## 🔍 COMPETITIVE INTELLIGENCE\n\n"

                        if 'market_blind_spots' in ci:
                            formatted += "**Blind Spots Rynku:**\n"
                            for spot in ci['market_blind_spots']:
                                formatted += f"- {spot}\n"
                            formatted += "\n"

                        if 'emerging_narratives' in ci:
                            formatted += "**Emerging Narratives:**\n"
                            for narrative in ci['emerging_narratives']:
                                formatted += f"- {narrative}\n"
                            formatted += "\n"

                        if 'author_credibility_ranking' in ci:
                            formatted += "**Ranking Wiarygodności Autorów:**\n"
                            for rank in ci['author_credibility_ranking']:
                                formatted += f"- {rank}\n"
                            formatted += "\n"

                        if 'predictive_value' in ci:
                            formatted += f"**Wartość Predykcyjna:** {ci['predictive_value']}\n\n"

                    # Add conclusion
                    if conclusion_text:
                        formatted += "## 📋 PODSUMOWANIE\n\n"
                        formatted += conclusion_text

                    return formatted

                except json.JSONDecodeError:
                    # If JSON parsing fails, return original text
                    return analysis_text
            else:
                return analysis_text
        else:
            # No JSON detected, return as is
            return analysis_text

    except Exception:
        # On any error, return original text
        return analysis_text

def render_header():
    """Render main header with smart update info"""
    st.markdown('<h1 class="main-header">📊 X Financial Analyzer - Smart Mode</h1>', unsafe_allow_html=True)

    # Show cache info
    last_update = get_last_update_time()
    data = load_comprehensive_data()

    if data and last_update:
        age = datetime.now() - last_update
        hours_ago = int(age.total_seconds() / 3600)
        minutes_ago = int((age.total_seconds() % 3600) / 60)

        if hours_ago > 0:
            age_text = f"{hours_ago}h {minutes_ago}m temu"
        else:
            age_text = f"{minutes_ago}m temu"

        total_tweets = data.get('collection_summary', {}).get('total_tweets', 0)

        st.markdown(f"""
        <div class="cache-info">
        <strong>Cache Mode:</strong> Używam {total_tweets} tweetów z cache (ostatnia aktualizacja: {age_text})
        <br><strong>Zero kosztów TwitterAPI</strong> - tylko inteligentne aktualizacje na żądanie
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="cache-info">
        ⚠️ <strong>Brak danych cache</strong> - użyj przycisku "Załaduj dane z cache" w zakładce Tweety
        </div>
        """, unsafe_allow_html=True)

def render_smart_sidebar():
    """Render sidebar with smart update controls"""
    st.sidebar.header("🎛️ Smart Control Panel")

    # Show current data status
    st.sidebar.subheader("📊 Status Danych")

    data = load_comprehensive_data()
    if data:
        collection_summary = data.get('collection_summary', {})
        last_update = get_last_update_time()

        st.sidebar.metric("Tweety w cache", f"{collection_summary.get('total_tweets', 0):,}")
        st.sidebar.metric("Konta", collection_summary.get('total_accounts', 0))

        if last_update:
            age = datetime.now() - last_update
            if age.total_seconds() < 3600:
                freshness = "🟢 Fresh"
            elif age.total_seconds() < 14400:
                freshness = "🟡 Recent"
            else:
                freshness = "🔴 Old"
        else:
            freshness = "❓ Unknown"

        st.sidebar.metric("Świeżość", freshness)
    else:
        st.sidebar.warning("Brak danych cache")

    # Smart update controls
    st.sidebar.subheader("🔄 Inteligentne Aktualizacje")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("🔄 Szybka", use_container_width=True, help="Sprawdź nowe tweety (3h)"):
            run_smart_update("quick")

    with col2:
        if st.button("📅 Dzienna", use_container_width=True, help="Aktualizacja dzienna (6h)"):
            run_smart_update("daily")

    if st.sidebar.button("🧠 Odśwież Analizy", use_container_width=True):
        run_analysis_update()

    # Cache management
    st.sidebar.subheader("💾 Zarządzanie Cache")

    if st.sidebar.button("📦 Użyj Cache", help="Załaduj wszystkie dane z cache"):
        with st.spinner("Ładowanie danych z cache..."):
            try:
                import subprocess
                result = subprocess.run(
                    ['python', 'convert_cache_to_comprehensive.py'],
                    cwd=os.getcwd(),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    st.sidebar.success("✅ Cache załadowany!")
                    st.rerun()
                else:
                    st.sidebar.error(f"❌ Błąd: {result.stderr}")
            except Exception as e:
                st.sidebar.error(f"❌ Błąd: {e}")

    # Info section
    st.sidebar.subheader("ℹ️ Informacje")
    st.sidebar.markdown("""
    **🎯 Smart Mode:**
    - Używa 654 tweetów z cache
    - Zero kosztów TwitterAPI w trybie offline
    - Aktualizacje tylko na żądanie
    - Inteligentne zarządzanie danymi
    """)

    return True

def run_smart_update(mode):
    """Run smart update - only fetch new tweets"""
    if mode == "quick":
        st.info("🔄 Szybka aktualizacja - sprawdzam nowe tweety z ostatnich 3h...")
        command = ['python', 'comprehensive_tweet_collector.py', 'quick']
    else:
        st.info("📅 Dzienna aktualizacja - sprawdzam nowe tweety z ostatnich 6h...")
        command = ['python', 'comprehensive_tweet_collector.py', 'daily']

    with st.spinner(f"Uruchamiam {mode} aktualizację..."):
        try:
            import subprocess
            result = subprocess.run(
                command,
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                st.success(f"✅ {mode.title()} aktualizacja ukończona!")
                # Show update summary
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'API calls:' in line or 'Tweets:' in line:
                        st.info(f"📊 {line}")
                st.rerun()
            else:
                st.error(f"❌ Błąd aktualizacji: {result.stderr}")
        except Exception as e:
            st.error(f"❌ Błąd: {e}")

def run_analysis_update():
    """Update analyses using current data"""
    st.info("🧠 Odświeżanie analiz z aktualnych danych...")

    with st.spinner("Generowanie nowych analiz..."):
        try:
            import subprocess

            # Run fund manager analysis
            result1 = subprocess.run(
                ['python', 'fund_manager_analysis.py'],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=120
            )

            # Run deep sectoral analysis
            result2 = subprocess.run(
                ['python', 'deep_sectoral_analysis.py'],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=600
            )

            success_count = 0
            if result1.returncode == 0:
                success_count += 1
                st.success("✅ Fund Manager analiza zaktualizowana!")
            else:
                st.warning(f"⚠️ Fund Manager błąd: {result1.stderr}")

            if result2.returncode == 0:
                success_count += 1
                st.success("✅ Analizy sektorowe zaktualizowane!")
            else:
                st.warning(f"⚠️ Analizy sektorowe błąd: {result2.stderr}")

            if success_count > 0:
                st.info(f"📊 Zaktualizowano {success_count}/2 analiz")
                st.rerun()
            else:
                st.error("❌ Nie udało się zaktualizować analiz")

        except Exception as e:
            st.error(f"❌ Błąd: {e}")

def render_main_metrics():
    """Render main metrics dashboard"""
    comprehensive_data = load_comprehensive_data()

    if not comprehensive_data:
        st.warning("Brak danych do wyświetlenia. Użyj przycisku 'Użyj Cache' w bocznym panelu.")
        return

    # Extract metrics from comprehensive data
    collection_summary = comprehensive_data.get('collection_summary', {})
    tweets_by_category = comprehensive_data.get('tweets_by_category', {})

    total_tweets = collection_summary.get('total_tweets', 0)
    total_accounts = collection_summary.get('total_accounts', 0)
    active_categories = len([cat for cat, tweets in tweets_by_category.items() if tweets])

    # Calculate basic sentiment and engagement
    total_engagement = 0
    positive_tweets = 0
    negative_tweets = 0

    for category, tweets in tweets_by_category.items():
        for tweet in tweets:
            engagement = tweet.get('like_count', 0) + tweet.get('retweet_count', 0)
            total_engagement += engagement

            text = tweet.get('text', '').lower()
            if any(word in text for word in ['bullish', 'good', 'up', 'growth', 'positive', 'wzrost']):
                positive_tweets += 1
            elif any(word in text for word in ['bearish', 'bad', 'down', 'crash', 'negative', 'spadek']):
                negative_tweets += 1

    sentiment_score = (positive_tweets - negative_tweets) / max(total_tweets, 1) * 100

    # Main metrics display
    st.subheader("📊 Główne Metryki")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if sentiment_score > 10:
            sentiment_label = "Bullish"
            delta_color = "normal"
        elif sentiment_score < -10:
            sentiment_label = "Bearish"
            delta_color = "inverse"
        else:
            sentiment_label = "Neutral"
            delta_color = "off"

        st.metric(
            "Market Sentiment",
            sentiment_label,
            delta=f"{sentiment_score:+.1f}%",
            delta_color=delta_color
        )

    with col2:
        st.metric("Łączne tweety", f"{total_tweets:,}")

    with col3:
        st.metric("Konta monitorowane", f"{total_accounts}")

    with col4:
        avg_engagement = total_engagement / max(total_tweets, 1)
        if avg_engagement > 10000:
            engagement_level = "Very High"
            engagement_emoji = "🔴"
        elif avg_engagement > 1000:
            engagement_level = "High"
            engagement_emoji = "🟡"
        else:
            engagement_level = "Normal"
            engagement_emoji = "🟢"

        st.metric("Zaangażowanie", f"{engagement_emoji} {engagement_level}")

    # Category breakdown
    st.subheader("📈 Breakdown według Kategorii")

    # Create a nice chart
    if tweets_by_category:
        categories = []
        tweet_counts = []
        engagement_scores = []

        for category, tweets in tweets_by_category.items():
            if tweets:
                categories.append(category)
                tweet_counts.append(len(tweets))

                total_cat_engagement = sum(
                    tweet.get('like_count', 0) + tweet.get('retweet_count', 0)
                    for tweet in tweets
                )
                engagement_scores.append(total_cat_engagement)

        # Create bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=categories,
            y=tweet_counts,
            name="Liczba tweetów",
            marker_color='lightblue',
            text=tweet_counts,
            textposition='auto'
        ))

        fig.update_layout(
            title="Tweety według kategorii",
            xaxis_title="Kategoria",
            yaxis_title="Liczba tweetów",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

def render_categorized_tweets():
    """Render categorized tweets display"""
    st.subheader("📱 Tweety według Kategorii")

    comprehensive_data = load_comprehensive_data()

    if not comprehensive_data:
        st.warning("Brak danych. Użyj przycisku 'Użyj Cache' w bocznym panelu.")
        return

    tweets_data = comprehensive_data.get('tweets_by_category', {})

    # Display summary
    total_tweets = sum(len(tweets) for tweets in tweets_data.values())
    st.info(f"📊 Łącznie {total_tweets:,} tweetów w {len(tweets_data)} kategoriach")

    # Create tabs for each category
    active_categories = [(cat, tweets) for cat, tweets in tweets_data.items() if tweets]

    if not active_categories:
        st.warning("Brak aktywnych kategorii")
        return

    # Create category tabs
    tab_names = [f"{cat} ({len(tweets)})" for cat, tweets in active_categories]
    tabs = st.tabs(tab_names)

    for i, (category, tweets) in enumerate(active_categories):
        with tabs[i]:
            st.write(f"**{category}** - {len(tweets)} tweetów")

            # Category metrics
            if tweets:
                total_likes = sum(tweet.get('like_count', 0) for tweet in tweets)
                total_retweets = sum(tweet.get('retweet_count', 0) for tweet in tweets)
                unique_authors = len(set(tweet.get('username', '') for tweet in tweets))

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Polubienia", f"{total_likes:,}")
                with col2:
                    st.metric("Retweety", f"{total_retweets:,}")
                with col3:
                    st.metric("Autorzy", unique_authors)
                with col4:
                    avg_engagement = (total_likes + total_retweets) / len(tweets)
                    st.metric("Śr. zaangażowanie", f"{avg_engagement:.1f}")

            # Show top tweets by engagement
            sorted_tweets = sorted(tweets,
                                 key=lambda x: x.get('like_count', 0) + x.get('retweet_count', 0),
                                 reverse=True)

            st.write("**🔥 Top tweety według zaangażowania:**")

            for j, tweet in enumerate(sorted_tweets[:5], 1):
                username = tweet.get('username', 'unknown')
                user_name = tweet.get('user_name', username)
                text = tweet.get('text', 'Brak tekstu')
                likes = tweet.get('like_count', 0)
                retweets = tweet.get('retweet_count', 0)
                replies = tweet.get('reply_count', 0)
                total_engagement = likes + retweets

                st.markdown(f"""
                <div class="metric-card">
                    <h4>{j}. @{username} ({user_name}) - {total_engagement:,} zaangażowania</h4>
                    <p>{text}</p>
                    <div style="display: flex; gap: 20px; font-size: 0.8em; color: #666;">
                        <span>❤️ {likes:,}</span>
                        <span>🔄 {retweets:,}</span>
                        <span>💬 {replies:,}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def render_deep_sectoral_analysis():
    """Render deep sectoral analysis results"""
    st.subheader("🎯 Głęboka Analiza Sektorowa")

    # Check if analysis files exist
    analysis_files = {
        'Giełda': 'data/analysis/deep_analysis_giełda.json',
        'Kryptowaluty': 'data/analysis/deep_analysis_kryptowaluty.json',
        'Gospodarka': 'data/analysis/deep_analysis_gospodarka.json',
        'Polityka': 'data/analysis/deep_analysis_polityka.json',
        'Nowinki AI': 'data/analysis/deep_analysis_nowinki ai.json',
        'Filozofia': 'data/analysis/deep_analysis_filozofia.json'
    }

    available_analyses = {}
    for sector, file_path in analysis_files.items():
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    available_analyses[sector] = json.load(f)
            except Exception as e:
                st.error(f"Błąd ładowania analizy {sector}: {e}")

    if not available_analyses:
        st.warning("Brak analiz sektorowych.")
        if st.button("🧠 Wygeneruj Analizy", key="generate_analyses"):
            run_analysis_update()
        return

    # Display analyses
    st.info(f"📊 Dostępne analizy: {len(available_analyses)} sektorów")

    # Create tabs for each sector
    sector_tabs = st.tabs(list(available_analyses.keys()))

    for i, (sector, analysis_data) in enumerate(available_analyses.items()):
        with sector_tabs[i]:
            st.markdown(f"#### 📈 {sector}")

            # Show metadata
            col1, col2 = st.columns(2)
            with col1:
                model = analysis_data.get('model_used', 'Unknown')
                st.caption(f"Model: {model}")
            with col2:
                timestamp = analysis_data.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        formatted_time = dt.strftime('%d.%m.%Y %H:%M')
                        st.caption(f"Wygenerowano: {formatted_time}")
                    except:
                        st.caption("Timestamp: Unknown")

            # Display analysis
            analysis_text = analysis_data.get('analysis', 'Brak analizy')

            # Try to parse JSON if present and format nicely
            formatted_analysis = format_analysis_text(analysis_text)

            with st.expander("📖 Pełna Analiza", expanded=True):
                st.markdown(formatted_analysis)

def render_ray_dalio_analysis():
    """Render Ray Dalio style analysis"""
    st.subheader("💼 Ray Dalio Style - List do Udziałowców")

    ray_dalio_content = load_custom_analysis('listRayDalio.txt')

    if not ray_dalio_content:
        st.warning("Brak analizy Ray Dalio. Sprawdź czy plik C:\\Xscrap\\listRayDalio.txt istnieje.")
        return

    # Display analysis with proper formatting
    st.markdown("### 📋 Strategiczny Przegląd Rynków")
    st.markdown("**Format:** Professional Fund Manager Letter")
    st.markdown("**Styl:** Ray Dalio systematic approach")

    # Create downloadable version
    col1, col2 = st.columns([4, 1])
    with col2:
        st.download_button(
            label="📄 Pobierz Report",
            data=ray_dalio_content,
            file_name=f"ray_dalio_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

    with st.expander("📖 Pełna Analiza Ray Dalio", expanded=True):
        st.markdown(ray_dalio_content)

def render_trading_playbook():
    """Render Trading Playbook analysis"""
    st.subheader("📈 Trading Playbook Q4 2025")

    trading_content = load_custom_analysis('tradingprediction.txt')

    if not trading_content:
        st.warning("Brak Trading Playbook. Sprawdź czy plik C:\\Xscrap\\tradingprediction.txt istnieje.")
        return

    # Display analysis with proper formatting
    st.markdown("### 🎯 Konkretne Strategie Tradingowe")
    st.markdown("**Format:** Tactical Trading Guide")
    st.markdown("**Zawiera:** Tickery, katalizatory, poziomy ryzyka")

    # Create downloadable version
    col1, col2 = st.columns([4, 1])
    with col2:
        st.download_button(
            label="📊 Pobierz Playbook",
            data=trading_content,
            file_name=f"trading_playbook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

    with st.expander("📈 Pełny Trading Playbook", expanded=True):
        st.markdown(trading_content)

def render_openai_analysis():
    """Render OpenAI comprehensive analysis"""
    st.subheader("🧠 OpenAI Comprehensive Market Analysis")

    openai_content = load_custom_analysis('analizaOpenAI.txt')

    if not openai_content:
        st.warning("Brak analizy OpenAI. Sprawdź czy plik C:\\Xscrap\\analizaOpenAI.txt istnieje.")
        return

    # Display analysis with proper formatting
    st.markdown("### 🔍 Głęboka Analiza 6 Sektorów")
    st.markdown("**Format:** Multi-sector comprehensive analysis")
    st.markdown("**Sektory:** Giełda, Krypto, Makro, Polityka, AI, Filozofia")

    # Create downloadable version
    col1, col2 = st.columns([4, 1])
    with col2:
        st.download_button(
            label="🧠 Pobierz Analizę",
            data=openai_content,
            file_name=f"openai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

    with st.expander("🧠 Pełna Analiza OpenAI", expanded=True):
        st.markdown(openai_content)

def main():
    """Main Streamlit app"""
    render_header()

    # Sidebar
    render_smart_sidebar()

    # Main content area
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📱 Tweety", "🎯 Analiza Sektorowa"])

    with tab1:
        render_main_metrics()

    with tab2:
        render_categorized_tweets()

    with tab3:
        # Create sub-tabs for different analysis types
        analysis_tabs = st.tabs([
            "🎯 Analiza Sektorowa",
            "💼 Ray Dalio Report",
            "📈 Trading Playbook",
            "🧠 OpenAI Analysis"
        ])

        with analysis_tabs[0]:
            render_deep_sectoral_analysis()

        with analysis_tabs[1]:
            render_ray_dalio_analysis()

        with analysis_tabs[2]:
            render_trading_playbook()

        with analysis_tabs[3]:
            render_openai_analysis()

    # Footer
    st.markdown("---")
    st.markdown("🤖 **X Financial Analyzer - Smart Mode** | 💾 Zero kosztów TwitterAPI | 🧠 Inteligentne aktualizacje")

if __name__ == "__main__":
    main()