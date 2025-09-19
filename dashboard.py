#!/usr/bin/env python3
"""
X Financial Analysis - Streamlit Dashboard
Interactive web interface for financial sentiment analysis
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

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import Serena integration
from serena_integration import SerenaIntegration

from src.scraper import DataCollector
from src.analyzer import DataProcessor
from src.claude_client import ClaudeAnalyst
from src.reporter import MarkdownReporter
from src.utils import ensure_directories, validate_api_keys, health_check

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

.sentiment-positive {
    color: #28a745;
    font-weight: bold;
}

.sentiment-negative {
    color: #dc3545;
    font-weight: bold;
}

.sentiment-neutral {
    color: #6c757d;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

class StreamlitDashboard:
    """Main Streamlit Dashboard Class"""

    def __init__(self):
        # Initialize components
        ensure_directories()
        self.data_collector = None
        self.data_processor = None
        self.claude_analyst = None
        self.reporter = None

        # Initialize Serena integration
        self.serena = SerenaIntegration()

        # Initialize session state
        if 'last_update' not in st.session_state:
            st.session_state.last_update = None
        if 'analysis_running' not in st.session_state:
            st.session_state.analysis_running = False

    def initialize_components(self):
        """Initialize components with error handling"""
        try:
            if not self.data_collector:
                self.data_collector = DataCollector()
            if not self.data_processor:
                self.data_processor = DataProcessor()
            if not self.claude_analyst:
                self.claude_analyst = ClaudeAnalyst()
            if not self.reporter:
                self.reporter = MarkdownReporter()
            return True
        except Exception as e:
            st.error(f"Error initializing components: {e}")
            return False

    def render_header(self):
        """Render main header"""
        st.markdown('<h1 class="main-header">📊 X Financial Analyzer</h1>', unsafe_allow_html=True)
        st.markdown("**Automatyczna analiza sentymenty finansowego z X (Twitter)**")

        # Status indicators
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            api_keys = validate_api_keys()
            twitter_status = "✅" if api_keys.get('TWITTER_API_KEY') else "❌"
            st.metric("Twitter API", twitter_status)

        with col2:
            claude_status = "✅" if api_keys.get('CLAUDE_API_KEY') else "❌"
            st.metric("Claude API", claude_status)

        with col3:
            if st.session_state.last_update:
                last_update = st.session_state.last_update.strftime("%H:%M:%S")
            else:
                last_update = "Never"
            st.metric("Ostatnia aktualizacja", last_update)

        with col4:
            # Data freshness
            latest_file = self.get_latest_processed_file()
            if latest_file:
                file_time = datetime.fromtimestamp(os.path.getctime(latest_file))
                age = datetime.now() - file_time
                if age.total_seconds() < 3600:  # Less than 1 hour
                    freshness = "🟢 Fresh"
                elif age.total_seconds() < 14400:  # Less than 4 hours
                    freshness = "🟡 Recent"
                else:
                    freshness = "🔴 Old"
            else:
                freshness = "❌ No Data"
            st.metric("Świeżość danych", freshness)

    def render_sidebar(self):
        """Render sidebar controls"""
        st.sidebar.header("🎛️ Panel Kontrolny")

        # Manual actions
        st.sidebar.subheader("Akcje Manualne")

        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button("🔄 Pobierz dane", use_container_width=True):
                self.run_data_collection()

        with col2:
            if st.button("📊 Analizuj", use_container_width=True):
                self.run_analysis()

        if st.sidebar.button("📋 Pełny cykl", use_container_width=True):
            self.run_full_cycle()

        # Settings
        st.sidebar.subheader("⚙️ Ustawienia")

        hours_back = st.sidebar.slider("Godziny wstecz", 1, 24, 4)

        auto_refresh = st.sidebar.checkbox("Auto-odświeżanie (30s)", value=False)

        if auto_refresh:
            time.sleep(30)
            st.rerun()

        # System info
        st.sidebar.subheader("ℹ️ Informacje")

        if st.sidebar.button("System Health Check"):
            health = health_check()
            st.sidebar.json(health)

        # Serena integration
        st.sidebar.subheader("👀 Live Preview")

        st.sidebar.markdown("**Serena Integration:**")
        st.sidebar.markdown(f"📄 [Project Docs](http://localhost:3000/docs/README.md)")
        st.sidebar.markdown(f"🔥 [Live Analysis](http://localhost:3000/live_preview/current_analysis.md)")

        if st.sidebar.button("📝 Update Documentation"):
            self.serena.create_project_documentation()
            st.sidebar.success("Documentation updated!")

        return hours_back

    def render_main_metrics(self):
        """Render main metrics dashboard"""
        # Load comprehensive tweets data for main metrics
        comprehensive_data = self.load_comprehensive_data()

        if not comprehensive_data:
            st.warning("Brak danych do wyświetlenia. Użyj przycisku 'Użyj danych z cache' w zakładce Tweety.")
            return

        # Extract metrics from comprehensive data
        collection_summary = comprehensive_data.get('collection_summary', {})
        tweets_by_category = comprehensive_data.get('tweets_by_category', {})

        total_tweets = collection_summary.get('total_tweets', 0)
        total_accounts = collection_summary.get('total_accounts', 0)
        active_categories = len([cat for cat, tweets in tweets_by_category.items() if tweets])

        # Calculate basic sentiment
        total_engagement = 0
        positive_tweets = 0
        negative_tweets = 0

        for category, tweets in tweets_by_category.items():
            for tweet in tweets:
                engagement = tweet.get('like_count', 0) + tweet.get('retweet_count', 0)
                total_engagement += engagement

                # Simple sentiment based on text length and engagement
                text = tweet.get('text', '')
                if 'bullish' in text.lower() or 'good' in text.lower() or 'up' in text.lower():
                    positive_tweets += 1
                elif 'bearish' in text.lower() or 'bad' in text.lower() or 'down' in text.lower():
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
                engagement_color = "🔴"
            elif avg_engagement > 1000:
                engagement_level = "High"
                engagement_color = "🟡"
            else:
                engagement_level = "Normal"
                engagement_color = "🟢"

            st.metric("Zaangażowanie", f"{engagement_color} {engagement_level}")

        # Additional metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Konta", f"{total_accounts}")

        with col2:
            avg_tweets_per_account = total_tweets / max(total_accounts, 1)
            st.metric("Śr. tweetów/konto", f"{avg_tweets_per_account:.1f}")

        with col3:
            # Most active category
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
                    if age.total_seconds() < 3600:  # Less than 1 hour
                        freshness = "🟢 Fresh"
                    elif age.total_seconds() < 14400:  # Less than 4 hours
                        freshness = "🟡 Recent"
                    else:
                        freshness = "🔴 Old"
                except:
                    freshness = "❓ Unknown"
            else:
                freshness = "❓ Unknown"
            st.metric("Świeżość danych", freshness)

    def render_sentiment_chart(self):
        """Render sentiment visualization"""
        comprehensive_data = self.load_comprehensive_data()

        if not comprehensive_data:
            st.warning("Brak danych do wykresu. Użyj przycisku 'Użyj danych z cache' w zakładce Tweety.")
            return

        st.subheader("📈 Analiza Sentymenty")

        tweets_by_category = comprehensive_data.get('tweets_by_category', {})

        if not tweets_by_category:
            st.warning("Brak danych kategorii do wyświetlenia")
            return

        # Prepare data for visualization
        category_names = []
        sentiment_scores = []
        tweet_counts = []
        engagement_scores = []

        for category, tweets in tweets_by_category.items():
            if tweets:
                category_names.append(category.replace('_', ' ').title())
                tweet_counts.append(len(tweets))

                # Calculate sentiment for category
                positive = 0
                negative = 0
                total_engagement = 0

                for tweet in tweets:
                    text = tweet.get('text', '').lower()
                    engagement = tweet.get('like_count', 0) + tweet.get('retweet_count', 0)
                    total_engagement += engagement

                    if any(word in text for word in ['bullish', 'good', 'up', 'growth', 'positive']):
                        positive += 1
                    elif any(word in text for word in ['bearish', 'bad', 'down', 'crash', 'negative']):
                        negative += 1

                sentiment_score = (positive - negative) / max(len(tweets), 1)
                sentiment_scores.append(sentiment_score)
                engagement_scores.append(total_engagement / max(len(tweets), 1))

        if not category_names:
            st.warning("Brak aktywnych kategorii")
            return

        # Create subplot with secondary y-axis
        fig = make_subplots(
            specs=[[{"secondary_y": True}]],
            subplot_titles=["Sentiment według kategorii"]
        )

        # Add sentiment bars
        fig.add_trace(
            go.Bar(
                x=category_names,
                y=sentiment_scores,
                name="Sentiment Score",
                marker_color=['green' if s > 0.1 else 'red' if s < -0.1 else 'gray' for s in sentiment_scores],
                text=[f"{s:+.2f}" for s in sentiment_scores],
                textposition="auto"
            ),
            secondary_y=False,
        )

        # Add tweet count line
        fig.add_trace(
            go.Scatter(
                x=category_names,
                y=tweet_counts,
                mode="lines+markers",
                name="Liczba tweetów",
                line=dict(color="blue", width=2),
                marker=dict(size=8)
            ),
            secondary_y=True,
        )

        # Update layout
        fig.update_xaxes(title_text="Kategoria")
        fig.update_yaxes(title_text="Sentiment Score", secondary_y=False)
        fig.update_yaxes(title_text="Liczba tweetów", secondary_y=True)

        fig.update_layout(
            height=500,
            showlegend=True,
            title_text="Sentiment i aktywność według kategorii (654 tweets)"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Show summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Łączne tweety", sum(tweet_counts))
        with col2:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            st.metric("Średni sentiment", f"{avg_sentiment:+.3f}")
        with col3:
            total_engagement = sum(engagement_scores)
            st.metric("Łączne zaangażowanie", f"{total_engagement:,.0f}")

    def render_category_details(self):
        """Render detailed category analysis"""
        latest_data = self.load_latest_processed_data()

        if not latest_data:
            return

        st.subheader("🔍 Szczegóły Kategorii")

        categories = latest_data.get('categories', {})

        # Create tabs for each category
        category_tabs = [cat.replace('_', ' ').title() for cat in categories.keys()
                        if categories[cat].get('tweet_count', 0) > 0]

        if not category_tabs:
            st.warning("Brak aktywnych kategorii")
            return

        tabs = st.tabs(category_tabs)

        for i, (category, data) in enumerate(categories.items()):
            if data.get('tweet_count', 0) == 0:
                continue

            with tabs[i]:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Sentiment",
                        data.get('sentiment_label', 'Unknown'),
                        delta=f"{data.get('weighted_sentiment', 0.0):.2f}"
                    )

                with col2:
                    st.metric("Tweety", data.get('tweet_count', 0))

                with col3:
                    st.metric(
                        "Średni wpływ",
                        f"{data.get('avg_influence', 0.0):.2f}"
                    )

                # Sentiment distribution pie chart
                sentiment_dist = data.get('sentiment_distribution', {})
                if sentiment_dist:
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=['Pozytywny', 'Negatywny', 'Neutralny'],
                        values=[
                            sentiment_dist.get('positive', 0),
                            sentiment_dist.get('negative', 0),
                            sentiment_dist.get('neutral', 0)
                        ],
                        hole=0.3
                    )])

                    fig_pie.update_layout(
                        title=f"Rozkład sentymenty - {category.replace('_', ' ').title()}",
                        height=400
                    )

                    st.plotly_chart(fig_pie, use_container_width=True)

                # Top tweets for this category
                top_tweets = data.get('top_tweets', [])
                if top_tweets:
                    st.write("**Top tweety:**")
                    for j, tweet in enumerate(top_tweets[:3], 1):
                        user = tweet.get('user', {})
                        username = user.get('screen_name', 'Unknown')
                        text = tweet.get('text', '')
                        influence = tweet.get('influence_score', 0.0)

                        st.markdown(f"""
                        **{j}. @{username}** (Wpływ: {influence:.2f})
                        > {text}
                        """)

    def render_recent_activity(self):
        """Render recent activity and top tweets"""
        latest_data = self.load_latest_processed_data()

        if not latest_data:
            return

        st.subheader("🔥 Najważniejsze Tweety")

        top_tweets = latest_data.get('top_tweets', [])

        if not top_tweets:
            st.warning("Brak tweetów do wyświetlenia")
            return

        for i, tweet in enumerate(top_tweets[:5], 1):
            user = tweet.get('user', {})
            username = user.get('screen_name', 'Unknown')
            name = user.get('name', 'Unknown')
            text = tweet.get('text', '')
            impact_score = tweet.get('impact_score', 0.0)
            sentiment = tweet.get('sentiment', {})
            sentiment_score = sentiment.get('polarity', 0.0)

            # Sentiment color
            if sentiment_score > 0.1:
                sentiment_class = "sentiment-positive"
                sentiment_emoji = "📈"
            elif sentiment_score < -0.1:
                sentiment_class = "sentiment-negative"
                sentiment_emoji = "📉"
            else:
                sentiment_class = "sentiment-neutral"
                sentiment_emoji = "➡️"

            st.markdown(f"""
            <div class="metric-card">
                <h4>{i}. @{username} ({name}) {sentiment_emoji}</h4>
                <p>{text}</p>
                <small>
                    <strong>Impact Score:</strong> {impact_score:.2f} |
                    <span class="{sentiment_class}"><strong>Sentiment:</strong> {sentiment_score:+.2f}</span>
                </small>
            </div>
            """, unsafe_allow_html=True)

    def run_data_collection(self):
        """Run data collection"""
        if not self.initialize_components():
            return

        with st.spinner("Pobieranie danych z X..."):
            try:
                raw_file = self.data_collector.collect_and_save(4)
                if raw_file:
                    st.success(f"✅ Dane pobrane pomyślnie: {raw_file}")
                    st.session_state.last_update = datetime.now()
                else:
                    st.error("❌ Błąd podczas pobierania danych")
            except Exception as e:
                st.error(f"❌ Błąd: {e}")

    def run_analysis(self):
        """Run sentiment analysis"""
        if not self.initialize_components():
            return

        # Find latest raw data file
        raw_files = glob.glob('data/raw/tweets_*.json')
        if not raw_files:
            st.warning("Brak danych do analizy. Najpierw pobierz dane.")
            return

        latest_raw_file = max(raw_files, key=os.path.getctime)

        with st.spinner("Analiza sentymenty w toku..."):
            try:
                processed_file = self.data_processor.load_and_process(latest_raw_file)
                if processed_file:
                    st.success(f"✅ Analiza ukończona: {processed_file}")
                    st.session_state.last_update = datetime.now()
                    st.rerun()  # Refresh the dashboard
                else:
                    st.error("❌ Błąd podczas analizy")
            except Exception as e:
                st.error(f"❌ Błąd: {e}")

    def run_full_cycle(self):
        """Run complete analysis cycle"""
        if not self.initialize_components():
            return

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Step 1: Collect data
            status_text.text("Krok 1/5: Pobieranie danych...")
            progress_bar.progress(20)

            raw_file = self.data_collector.collect_and_save(4)
            if not raw_file:
                st.error("❌ Błąd podczas pobierania danych")
                return

            # Step 2: Process data
            status_text.text("Krok 2/5: Analiza sentymenty...")
            progress_bar.progress(40)

            processed_file = self.data_processor.load_and_process(raw_file)
            if not processed_file:
                st.error("❌ Błąd podczas analizy")
                return

            # Step 3: Load processed data
            status_text.text("Krok 3/5: Ładowanie danych...")
            progress_bar.progress(60)

            with open(processed_file, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)

            # Step 4: Claude analysis
            status_text.text("Krok 4/5: Analiza AI...")
            progress_bar.progress(80)

            claude_analysis = self.claude_analyst.analyze_market_sentiment(processed_data)
            executive_summary = self.claude_analyst.generate_executive_summary(
                processed_data, claude_analysis
            )

            # Step 5: Generate report
            status_text.text("Krok 5/5: Generowanie raportu...")
            progress_bar.progress(100)

            report_content = self.reporter.generate_daily_report(
                processed_data, claude_analysis, executive_summary
            )
            report_file = self.reporter.save_report(report_content, 'daily')

            if report_file:
                st.success(f"✅ Pełny cykl ukończony pomyślnie!")
                st.session_state.last_update = datetime.now()
                status_text.text("Gotowe!")

                # Show download button for report
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_content = f.read()

                st.download_button(
                    label="📄 Pobierz raport",
                    data=report_content,
                    file_name=f"raport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )

                st.rerun()  # Refresh dashboard
            else:
                st.error("❌ Błąd podczas generowania raportu")

        except Exception as e:
            st.error(f"❌ Błąd podczas pełnego cyklu: {e}")

        finally:
            progress_bar.empty()
            status_text.empty()

    def load_latest_processed_data(self):
        """Load latest processed data and update live preview"""
        try:
            processed_files = glob.glob('data/processed/analysis_*.json')
            if not processed_files:
                return None

            latest_file = max(processed_files, key=os.path.getctime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update live preview for Serena
            try:
                self.serena.create_live_analysis_file(data)
            except Exception as serena_error:
                # Don't fail if Serena update fails
                pass

            return data
        except Exception as e:
            st.error(f"Błąd ładowania danych: {e}")
            return None

    def load_comprehensive_data(self):
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

    def load_categorized_tweets(self):
        """Load categorized tweets data"""
        try:
            # First try comprehensive tweets (new system)
            comprehensive_file = 'data/raw/comprehensive_tweets_current.json'
            if os.path.exists(comprehensive_file):
                with open(comprehensive_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('tweets_by_category', {})

            # Fallback to sample file
            sample_file = 'data/raw/sample_categorized_tweets.json'
            if os.path.exists(sample_file):
                with open(sample_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            st.error(f"Błąd ładowania kategoryzowanych tweetów: {e}")
            return None

    def render_categorized_tweets(self):
        """Render categorized tweets display"""
        st.subheader("📱 Najnowsze Tweety według Kategorii")

        tweets_data = self.load_categorized_tweets()

        if not tweets_data:
            st.warning("Brak kategoryzowanych tweetów. Uruchom pobieranie danych.")

            # Button to fetch new tweets
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

            with col2:
                if st.button("📊 Pobierz wszystkie konta", key="all_tweets"):
                    st.info("Pobieranie wszystkich kont może potrwać kilka minut...")
                    with st.spinner("Pobieranie kompletnych danych z cache..."):
                        try:
                            import subprocess
                            result = subprocess.run(
                                ['python', 'comprehensive_tweet_collector.py'],
                                cwd=os.getcwd(),
                                capture_output=True,
                                text=True,
                                timeout=600
                            )
                            if result.returncode == 0:
                                st.success("✅ Pobrano kompletne dane!")
                                st.rerun()
                            else:
                                st.error(f"❌ Błąd: {result.stderr}")
                        except Exception as e:
                            st.error(f"❌ Błąd podczas pobierania: {e}")
            return

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
                for j, tweet in enumerate(tweets, 1):
                    username = tweet.get('username', 'unknown')
                    user_name = tweet.get('user_name', username)
                    text = tweet.get('text', 'Brak tekstu')
                    created_at = tweet.get('created_at', '')
                    likes = tweet.get('like_count', 0)
                    retweets = tweet.get('retweet_count', 0)
                    replies = tweet.get('reply_count', 0)

                    # Display full text

                    # Format date
                    try:
                        if created_at:
                            from datetime import datetime
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

                # Refresh button for this category
                if st.button(f"🔄 Odśwież {category}", key=f"refresh_{category}"):
                    st.info(f"Odświeżanie kategorii {category}...")

        # Global refresh button
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Odśwież wszystkie tweety", key="refresh_all_tweets"):
                with st.spinner("Pobieranie najnowszych tweetów..."):
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['python', 'comprehensive_tweet_collector.py', 'quick'],
                            cwd=os.getcwd(),
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        if result.returncode == 0:
                            st.success("✅ Odświeżono wszystkie tweety!")
                            st.rerun()
                        else:
                            st.error(f"❌ Błąd: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ Błąd podczas odświeżania: {e}")

        with col2:
            # Data info
            if tweets_data:
                st.caption(f"Ostatnia aktualizacja: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

    def render_market_analysis(self):
        """Render comprehensive market analysis report"""
        st.subheader("📊 Analiza Rynkowa i Prognozy")

        # Load analysis data
        try:
            analysis_file = 'data/analysis/market_sentiment_analysis.json'
            if os.path.exists(analysis_file):
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
            else:
                analysis_data = None

            report_file = 'data/analysis/market_analysis_report.md'
            if os.path.exists(report_file):
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_content = f.read()
            else:
                report_content = None

        except Exception as e:
            st.error(f"Błąd ładowania analizy: {e}")
            analysis_data = None
            report_content = None

        if not analysis_data or not report_content:
            st.warning("Brak analizy rynkowej. Wygeneruj nową analizę.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧠 Wygeneruj analizę rynkową", key="generate_analysis"):
                    with st.spinner("Generowanie analizy rynkowej..."):
                        try:
                            import subprocess
                            result = subprocess.run(
                                ['python', 'local_market_analysis.py'],
                                cwd=os.getcwd(),
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            if result.returncode == 0:
                                st.success("✅ Analiza wygenerowana!")
                                st.rerun()
                            else:
                                st.error(f"❌ Błąd: {result.stderr}")
                        except Exception as e:
                            st.error(f"❌ Błąd podczas generowania: {e}")

            with col2:
                st.info("Analiza wymaga najpierw pobrania tweetów z zakładki 'Tweety'")
            return

        # Display key metrics
        if analysis_data:
            st.markdown("### 🎯 Kluczowe Wskaźniki")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                sentiment_score = analysis_data.get('overall_sentiment', 0.0)
                sentiment_rating = analysis_data.get('sentiment_rating', 'Neutralny')
                st.metric("Sentiment rynkowy", sentiment_rating, delta=f"{sentiment_score:+.3f}")

            with col2:
                tweets_count = analysis_data.get('tweets_analyzed', 0)
                st.metric("Przeanalizowane tweety", tweets_count)

            with col3:
                total_engagement = analysis_data.get('total_engagement', 0)
                st.metric("Łączne zaangażowanie", f"{total_engagement:,}")

            with col4:
                categories_count = len(analysis_data.get('categories', []))
                st.metric("Kategorie", categories_count)

        # Analysis timestamp
        if analysis_data:
            timestamp = analysis_data.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime('%d.%m.%Y %H:%M:%S')
                    st.caption(f"Analiza z: {formatted_time}")
                except:
                    st.caption(f"Analiza z: {timestamp}")

        # Display full report
        if report_content:
            st.markdown("### 📋 Pełny Raport")

            # Add download button
            col1, col2 = st.columns([3, 1])
            with col2:
                st.download_button(
                    label="📄 Pobierz raport",
                    data=report_content,
                    file_name=f"analiza_rynkowa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="download_analysis"
                )

            # Display report content
            with st.expander("📊 Pokaż pełną analizę", expanded=True):
                st.markdown(report_content)

        # Refresh analysis section
        st.markdown("---")
        st.markdown("### 🔄 Aktualizacja Analizy")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Odśwież analizę", key="refresh_analysis"):
                with st.spinner("Regenerowanie analizy..."):
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['python', 'local_market_analysis.py'],
                            cwd=os.getcwd(),
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if result.returncode == 0:
                            st.success("✅ Analiza zaktualizowana!")
                            st.rerun()
                        else:
                            st.error(f"❌ Błąd: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ Błąd podczas aktualizacji: {e}")

        with col2:
            st.info("💡 Tip: Najpierw odśwież tweety, potem analizę dla najaktualniejszych wyników")

    def render_fund_manager_analysis(self):
        """Render professional fund manager analysis"""
        st.subheader("💼 Fund Manager Analysis - Ray Dalio Style")

        # Load fund manager analysis
        try:
            analysis_file = 'data/analysis/fund_manager_analysis_current.json'
            if os.path.exists(analysis_file):
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
            else:
                analysis_data = None

            report_file = 'data/analysis/fund_manager_analysis_current.md'
            if os.path.exists(report_file):
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_content = f.read()
            else:
                report_content = None

        except Exception as e:
            st.error(f"Błąd ładowania analizy fund managera: {e}")
            analysis_data = None
            report_content = None

        if not analysis_data or not report_content:
            st.warning("Brak analizy fund managera. Wygeneruj nową analizę.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏦 Wygeneruj analizę Fund Manager", key="generate_fund_analysis"):
                    with st.spinner("Generowanie profesjonalnej analizy inwestycyjnej..."):
                        try:
                            import subprocess
                            # First prepare demo data
                            subprocess.run(['python', 'prepare_demo_data.py'],
                                         cwd=os.getcwd(), timeout=30)
                            # Then run fund manager analysis
                            result = subprocess.run(
                                ['python', 'fund_manager_analysis.py'],
                                cwd=os.getcwd(),
                                capture_output=True,
                                text=True,
                                timeout=120
                            )
                            if result.returncode == 0:
                                st.success("✅ Analiza Fund Manager wygenerowana!")
                                st.rerun()
                            else:
                                st.error(f"❌ Błąd: {result.stderr}")
                        except Exception as e:
                            st.error(f"❌ Błąd podczas generowania: {e}")

            with col2:
                if st.button("📊 Pobierz wszystkie dane", key="collect_comprehensive"):
                    st.info("Pobieranie 10 tweetów z każdego konta (może potrwać kilka minut)")
                    with st.spinner("Pobieranie kompletnych danych..."):
                        try:
                            import subprocess
                            result = subprocess.run(
                                ['python', 'comprehensive_tweet_collector.py'],
                                cwd=os.getcwd(),
                                capture_output=True,
                                text=True,
                                timeout=600
                            )
                            if result.returncode == 0:
                                st.success("✅ Kompletne dane pobrane!")
                                # Auto-run fund manager analysis
                                subprocess.run(['python', 'fund_manager_analysis.py'],
                                             cwd=os.getcwd(), timeout=120)
                                st.success("✅ Analiza zaktualizowana!")
                                st.rerun()
                            else:
                                st.error(f"❌ Błąd pobierania: {result.stderr}")
                        except Exception as e:
                            st.error(f"❌ Błąd: {e}")
            return

        # Display professional metrics
        if analysis_data:
            st.markdown("### 🎯 Professional Investment Metrics")

            risk_metrics = analysis_data.get('risk_metrics', {})
            market_themes = analysis_data.get('market_themes', {})

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                avg_sentiment = risk_metrics.get('avg_sentiment', 0.0)
                if avg_sentiment > 0.1:
                    stance = "BULLISH"
                    color = "green"
                elif avg_sentiment < -0.1:
                    stance = "BEARISH"
                    color = "red"
                else:
                    stance = "NEUTRAL"
                    color = "gray"

                st.metric("Market Stance", stance, delta=f"{avg_sentiment:+.3f}")

            with col2:
                volatility = risk_metrics.get('sentiment_volatility', 0.0)
                vol_level = "HIGH" if volatility > 0.4 else "MODERATE" if volatility > 0.2 else "LOW"
                st.metric("Volatility Regime", vol_level, delta=f"{volatility:.3f}")

            with col3:
                if market_themes:
                    top_theme = max(market_themes, key=market_themes.get)
                    theme_count = market_themes[top_theme]
                    st.metric("Dominant Theme", top_theme, delta=f"{theme_count} signals")
                else:
                    st.metric("Dominant Theme", "N/A", delta="0 signals")

            with col4:
                tweets_analyzed = analysis_data.get('data_summary', {}).get('total_tweets', 0)
                accounts_analyzed = analysis_data.get('data_summary', {}).get('total_accounts', 0)
                st.metric("Data Coverage", f"{accounts_analyzed} accounts", delta=f"{tweets_analyzed} tweets")

            # Risk assessment section
            st.markdown("### ⚠️ Risk Assessment")

            extreme_ratio = risk_metrics.get('extreme_sentiment_ratio', 0.0)
            uncertainty_index = risk_metrics.get('uncertainty_index', 0.0)

            col1, col2, col3 = st.columns(3)

            with col1:
                if extreme_ratio > 0.3:
                    risk_color = "🔴"
                    risk_text = "HIGH RISK"
                elif extreme_ratio > 0.15:
                    risk_color = "🟡"
                    risk_text = "MODERATE"
                else:
                    risk_color = "🟢"
                    risk_text = "LOW RISK"

                st.markdown(f"**Extreme Sentiment Risk**")
                st.markdown(f"{risk_color} {risk_text} ({extreme_ratio:.1%})")

            with col2:
                if uncertainty_index > 0.3:
                    uncertainty_color = "🔴"
                    uncertainty_text = "HIGH"
                elif uncertainty_index > 0.15:
                    uncertainty_color = "🟡"
                    uncertainty_text = "MODERATE"
                else:
                    uncertainty_color = "🟢"
                    uncertainty_text = "LOW"

                st.markdown(f"**Uncertainty Index**")
                st.markdown(f"{uncertainty_color} {uncertainty_text} ({uncertainty_index:.3f})")

            with col3:
                avg_engagement = risk_metrics.get('avg_engagement', 0)
                if avg_engagement > 10000:
                    engagement_text = "VERY HIGH"
                    engagement_color = "🔴"
                elif avg_engagement > 1000:
                    engagement_text = "HIGH"
                    engagement_color = "🟡"
                else:
                    engagement_text = "NORMAL"
                    engagement_color = "🟢"

                st.markdown(f"**Market Attention**")
                st.markdown(f"{engagement_color} {engagement_text} ({avg_engagement:,.0f})")

        # Analysis timestamp
        if analysis_data:
            timestamp = analysis_data.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    formatted_time = dt.strftime('%d.%m.%Y %H:%M:%S')
                    st.caption(f"Professional Analysis Generated: {formatted_time}")
                except:
                    st.caption(f"Analysis from: {timestamp}")

        # Full professional report
        if report_content:
            st.markdown("### 📋 Complete Fund Manager Report")

            # Download buttons
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                st.download_button(
                    label="📄 Download Report",
                    data=report_content,
                    file_name=f"fund_manager_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="download_fund_analysis"
                )

            with col3:
                if analysis_data:
                    st.download_button(
                        label="📊 Download Data",
                        data=json.dumps(analysis_data, indent=2, ensure_ascii=False),
                        file_name=f"fund_analysis_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_fund_data"
                    )

            # Show report with professional formatting
            with st.expander("📈 Professional Investment Analysis", expanded=True):
                st.markdown(report_content)

        # Update controls
        st.markdown("---")
        st.markdown("### 🔄 Analysis Management")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Fund Analysis", key="refresh_fund_analysis"):
                with st.spinner("Refreshing professional analysis..."):
                    try:
                        import subprocess
                        # Run fund manager analysis
                        result = subprocess.run(
                            ['python', 'fund_manager_analysis.py'],
                            cwd=os.getcwd(),
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        if result.returncode == 0:
                            st.success("✅ Fund Manager Analysis refreshed!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ Error during refresh: {e}")

        with col2:
            st.info("💡 Pro Tip: This analysis follows Ray Dalio's systematic investment principles")

    def render_deep_sectoral_analysis(self):
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

        # Actions section
        st.markdown("---")
        st.markdown("### 🔄 Zarządzanie Analizami")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Odśwież Analizy", key="refresh_deep_analysis"):
                with st.spinner("Odświeżanie analiz sektorowych..."):
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
                            st.success("✅ Analizy odświeżone!")
                            st.rerun()
                        else:
                            st.error(f"❌ Błąd: {result.stderr}")
                    except Exception as e:
                        st.error(f"❌ Błąd podczas odświeżania: {e}")

        with col2:
            # Download all analyses
            if available_analyses:
                comprehensive_data = {
                    'metadata': {
                        'generated_at': datetime.now().isoformat(),
                        'total_sectors': len(available_analyses),
                        'analysis_type': 'deep_sectoral_semantic'
                    },
                    'sectoral_analyses': available_analyses
                }

                st.download_button(
                    label="📦 Pobierz Wszystkie",
                    data=json.dumps(comprehensive_data, indent=2, ensure_ascii=False),
                    file_name=f"comprehensive_deep_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_all_deep_analyses"
                )

        with col3:
            st.info("💡 Tip: Analizy fokusują się na interpretacji ZNACZENIA wypowiedzi autorów")

    def get_latest_processed_file(self):
        """Get path to latest processed file"""
        processed_files = glob.glob('data/processed/analysis_*.json')
        if not processed_files:
            return None
        return max(processed_files, key=os.path.getctime)

    def run(self):
        """Main dashboard run method"""
        self.render_header()

        hours_back = self.render_sidebar()

        # Main content area
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📊 Dashboard", "📱 Tweety", "🧠 Analiza", "📈 Wykresy", "🔍 Szczegóły", "🔥 Aktywność", "💼 Fund Manager", "🎯 Analiza Sektorowa"])

        with tab1:
            self.render_main_metrics()

        with tab2:
            self.render_categorized_tweets()

        with tab3:
            self.render_market_analysis()

        with tab4:
            self.render_sentiment_chart()

        with tab5:
            self.render_category_details()

        with tab6:
            self.render_recent_activity()

        with tab7:
            self.render_fund_manager_analysis()

        with tab8:
            self.render_deep_sectoral_analysis()

        # Footer
        st.markdown("---")
        st.markdown("🤖 **X Financial Analyzer** - Automatyczna analiza sentymenty finansowego")


def main():
    """Main Streamlit app"""
    dashboard = StreamlitDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()