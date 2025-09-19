#!/usr/bin/env python3
"""
Simple Dashboard - Only for analysis display, no TwitterAPI calls
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
    page_title="X Financial Analyzer",
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
</style>
""", unsafe_allow_html=True)

def load_comprehensive_data():
    """Load comprehensive data with statistics"""
    try:
        comprehensive_file = 'data/raw/comprehensive_tweets_current.json'
        if os.path.exists(comprehensive_file):
            with open(comprehensive_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        st.error(f"Błąd ładowania danych: {e}")
        return None

def render_header():
    """Render main header"""
    st.markdown('<h1 class="main-header">📊 X Financial Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("**Głęboka analiza sentymenty finansowego z 654 tweetów z cache**")

def render_main_metrics():
    """Render main metrics dashboard"""
    comprehensive_data = load_comprehensive_data()

    if not comprehensive_data:
        st.warning("Brak danych do wyświetlenia. Użyj convert_cache_to_comprehensive.py")
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
            if any(word in text for word in ['bullish', 'good', 'up', 'growth', 'positive']):
                positive_tweets += 1
            elif any(word in text for word in ['bearish', 'bad', 'down', 'crash', 'negative']):
                negative_tweets += 1

    sentiment_score = (positive_tweets - negative_tweets) / max(total_tweets, 1) * 100

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if sentiment_score > 20:
            sentiment_label = "Bullish"
            delta_color = "normal"
        elif sentiment_score < -20:
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
        st.metric("Aktywne kategorie", active_categories)

    with col4:
        avg_engagement = total_engagement / max(total_tweets, 1)
        if avg_engagement > 10000:
            engagement_level = "Very High"
        elif avg_engagement > 1000:
            engagement_level = "High"
        else:
            engagement_level = "Normal"

        st.metric("Zaangażowanie", engagement_level)

    # Additional metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Konta", f"{total_accounts}")

    with col2:
        avg_tweets_per_account = total_tweets / max(total_accounts, 1)
        st.metric("Śr. tweetów/konto", f"{avg_tweets_per_account:.1f}")

    with col3:
        most_active_cat = max(tweets_by_category.keys(),
                            key=lambda k: len(tweets_by_category[k]),
                            default="N/A")
        if most_active_cat != "N/A":
            most_active_count = len(tweets_by_category[most_active_cat])
            st.metric("Najaktywniejsza", f"{most_active_cat} ({most_active_count})")
        else:
            st.metric("Najaktywniejsza", "N/A")

    with col4:
        timestamp = comprehensive_data.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                age = datetime.now() - dt
                if age.total_seconds() < 3600:
                    freshness = "Fresh"
                elif age.total_seconds() < 14400:
                    freshness = "Recent"
                else:
                    freshness = "Old"
            except:
                freshness = "Unknown"
        else:
            freshness = "Unknown"
        st.metric("Świeżość danych", freshness)

def render_categorized_tweets():
    """Render categorized tweets display"""
    st.subheader("📱 Najnowsze Tweety według Kategorii")

    comprehensive_data = load_comprehensive_data()

    if not comprehensive_data:
        st.warning("Brak kategoryzowanych tweetów.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Użyj danych z cache", key="sample_tweets"):
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
                            st.success("✅ Załadowano dane z cache!")
                            st.rerun()
                        else:
                            st.error(f"❌ Błąd: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ Błąd podczas ładowania: {e}")
        return

    tweets_data = comprehensive_data.get('tweets_by_category', {})

    # Display summary stats
    total_tweets = sum(len(tweets) for tweets in tweets_data.values())
    categories_count = len([cat for cat, tweets in tweets_data.items() if tweets])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Kategorie aktywne", categories_count)
    with col2:
        st.metric("Łącznie tweetów", total_tweets)
    with col3:
        if total_tweets > 0:
            avg_per_category = total_tweets / categories_count if categories_count > 0 else 0
            st.metric("Średnio na kategorię", f"{avg_per_category:.1f}")

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
            st.write(f"**{category}** - {len(tweets)} najnowszych tweetów")

            # Category metrics
            if tweets:
                total_likes = sum(tweet.get('like_count', 0) for tweet in tweets)
                total_retweets = sum(tweet.get('retweet_count', 0) for tweet in tweets)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Łącznie polubień", f"{total_likes:,}")
                with col2:
                    st.metric("Łącznie retweetów", f"{total_retweets:,}")
                with col3:
                    avg_engagement = (total_likes + total_retweets) / len(tweets) if tweets else 0
                    st.metric("Śr. zaangażowanie", f"{avg_engagement:.1f}")

            # Display tweets
            for j, tweet in enumerate(tweets[:10], 1):  # Show only first 10
                username = tweet.get('username', 'unknown')
                user_name = tweet.get('user_name', username)
                text = tweet.get('text', 'Brak tekstu')
                created_at = tweet.get('created_at', '')
                likes = tweet.get('like_count', 0)
                retweets = tweet.get('retweet_count', 0)
                replies = tweet.get('reply_count', 0)

                # Format date
                try:
                    if created_at:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        formatted_date = dt.strftime('%d.%m.%Y %H:%M')
                    else:
                        formatted_date = "Nieznana data"
                except:
                    formatted_date = created_at

                # Create tweet card
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{j}. @{username} ({user_name})</h4>
                    <p>{text}</p>
                    <div style="display: flex; gap: 20px; font-size: 0.8em; color: #666;">
                        <span>📅 {formatted_date}</span>
                        <span>❤️ {likes:,}</span>
                        <span>🔄 {retweets:,}</span>
                        <span>💬 {replies:,}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def render_deep_sectoral_analysis():
    """Render deep sectoral analysis results"""
    st.subheader("🎯 Głęboka Analiza Sektorowa - Interpretacja Poglądów Ekspertów")

    st.markdown("""
    **Typ analizy:** Semantyczna interpretacja wypowiedzi autorów z konfrontacją różnych poglądów
    **Model AI:** Claude 3.5 Haiku (najnowszy dostępny)
    **Fokus:** Wydobycie SENSU wypowiedzi zamiast liczenia słów kluczowych
    """)

    # Check if analysis files exist
    analysis_files = {
        'Giełda': 'data/analysis/deep_analysis_giełda.json',
        'Kryptowaluty': 'data/analysis/deep_analysis_kryptowaluty.json',
        'Gospodarka': 'data/analysis/deep_analysis_gospodarka.json',
        'Polityka': 'data/analysis/deep_analysis_polityka.json',
        'Nowinki AI': 'data/analysis/deep_analysis_nowinki ai.json',
        'Filozofia': 'data/analysis/deep_analysis_filozofia.json'
    }

    # Check which analyses are available
    available_analyses = {}
    for sector, file_path in analysis_files.items():
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    available_analyses[sector] = json.load(f)
            except Exception as e:
                st.error(f"Błąd ładowania analizy {sector}: {e}")

    if not available_analyses:
        st.warning("Brak analiz sektorowych. Wygeneruj analizy używając przycisku poniżej.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧠 Wygeneruj Głębokie Analizy Sektorowe", key="generate_deep_analysis"):
                with st.spinner("Generowanie głębokich analiz sektorowych..."):
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['python', 'deep_sectoral_analysis.py'],
                            cwd=os.getcwd(),
                            capture_output=True,
                            text=True,
                            timeout=600
                        )
                        if result.returncode == 0:
                            st.success("✅ Głębokie analizy sektorowe wygenerowane!")
                            st.rerun()
                        else:
                            st.error(f"❌ Błąd: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ Błąd podczas generowania: {e}")

        with col2:
            st.info("💡 Analizy używają 654 tweetów z cache (zero kosztów TwitterAPI)")
        return

    # Display summary metrics
    st.markdown("### 📊 Podsumowanie Analiz")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Sektory przeanalizowane", len(available_analyses))

    with col2:
        latest_analysis = max(available_analyses.values(),
                            key=lambda x: x.get('timestamp', ''))
        model_used = latest_analysis.get('model_used', 'Unknown')
        st.metric("Model Claude", model_used.split('-')[-1] if model_used else 'Unknown')

    with col3:
        latest_time = latest_analysis.get('timestamp', '')
        if latest_time:
            try:
                dt = datetime.fromisoformat(latest_time)
                time_ago = datetime.now() - dt
                if time_ago.total_seconds() < 3600:
                    freshness = f"{int(time_ago.total_seconds()/60)}m ago"
                else:
                    freshness = f"{int(time_ago.total_seconds()/3600)}h ago"
            except:
                freshness = "Unknown"
        else:
            freshness = "Unknown"
        st.metric("Ostatnia analiza", freshness)

    with col4:
        total_insights = sum(len(analysis.get('analysis', '').split('###')) for analysis in available_analyses.values())
        st.metric("Insights wygenerowane", total_insights)

    # Display sectoral analyses
    st.markdown("### 🔍 Analizy Sektorowe")

    # Create tabs for each sector
    if available_analyses:
        sector_tabs = st.tabs(list(available_analyses.keys()))

        for i, (sector, analysis_data) in enumerate(available_analyses.items()):
            with sector_tabs[i]:
                st.markdown(f"#### 📈 Sektor: {sector}")

                # Show model and timestamp
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"Model: {analysis_data.get('model_used', 'Unknown')}")
                with col2:
                    timestamp = analysis_data.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp)
                            formatted_time = dt.strftime('%d.%m.%Y %H:%M')
                            st.caption(f"Wygenerowano: {formatted_time}")
                        except:
                            st.caption(f"Wygenerowano: {timestamp}")

                # Display analysis content
                analysis_text = analysis_data.get('analysis', 'Brak analizy')

                # Create expandable sections for better readability
                with st.expander("📖 Pełna Analiza Sektorowa", expanded=True):
                    st.markdown(analysis_text)

                # Download button for this sector
                col1, col2 = st.columns([3, 1])
                with col2:
                    st.download_button(
                        label=f"📄 Pobierz {sector}",
                        data=json.dumps(analysis_data, indent=2, ensure_ascii=False),
                        file_name=f"deep_analysis_{sector.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key=f"download_{sector}"
                    )

def main():
    """Main Streamlit app"""
    render_header()

    # Main content area
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📱 Tweety", "🎯 Analiza Sektorowa"])

    with tab1:
        render_main_metrics()

    with tab2:
        render_categorized_tweets()

    with tab3:
        render_deep_sectoral_analysis()

    # Footer
    st.markdown("---")
    st.markdown("🤖 **X Financial Analyzer** - Analiza 654 tweetów bez kosztów TwitterAPI")

if __name__ == "__main__":
    main()