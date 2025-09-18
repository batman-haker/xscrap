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

        return hours_back

    def render_main_metrics(self):
        """Render main metrics dashboard"""
        latest_data = self.load_latest_processed_data()

        if not latest_data:
            st.warning("Brak danych do wyświetlenia. Uruchom analizę aby wygenerować dane.")
            return

        # Overall sentiment
        overall_sentiment = latest_data.get('overall_sentiment', {})
        sentiment_score = overall_sentiment.get('overall_score', 0.0)
        sentiment_label = overall_sentiment.get('sentiment_label', 'Unknown')

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Sentiment score with color
            if sentiment_score > 0.2:
                delta_color = "normal"
            elif sentiment_score < -0.2:
                delta_color = "inverse"
            else:
                delta_color = "off"

            st.metric(
                "Overall Sentiment",
                f"{sentiment_score:.2f}",
                delta=sentiment_label,
                delta_color=delta_color
            )

        with col2:
            total_tweets = latest_data.get('total_tweets', 0)
            st.metric("Łączne tweety", total_tweets)

        with col3:
            categories = latest_data.get('categories', {})
            active_categories = sum(1 for cat_data in categories.values()
                                  if cat_data.get('tweet_count', 0) > 0)
            st.metric("Aktywne kategorie", active_categories)

        with col4:
            # Risk level (derived from sentiment)
            if abs(sentiment_score) > 0.7:
                risk_level = "High"
                risk_color = "🔴"
            elif abs(sentiment_score) > 0.4:
                risk_level = "Medium"
                risk_color = "🟡"
            else:
                risk_level = "Low"
                risk_color = "🟢"

            st.metric("Poziom ryzyka", f"{risk_color} {risk_level}")

    def render_sentiment_chart(self):
        """Render sentiment visualization"""
        latest_data = self.load_latest_processed_data()

        if not latest_data:
            return

        st.subheader("📈 Analiza Sentymenty")

        categories = latest_data.get('categories', {})

        if not categories:
            st.warning("Brak danych kategorii do wyświetlenia")
            return

        # Prepare data for visualization
        category_names = []
        sentiment_scores = []
        tweet_counts = []
        sentiment_labels = []

        for category, data in categories.items():
            if data.get('tweet_count', 0) > 0:
                category_names.append(category.replace('_', ' ').title())
                sentiment_scores.append(data.get('weighted_sentiment', 0.0))
                tweet_counts.append(data.get('tweet_count', 0))
                sentiment_labels.append(data.get('sentiment_label', 'Unknown'))

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
                marker_color=['green' if s > 0 else 'red' if s < 0 else 'gray' for s in sentiment_scores],
                text=[f"{s:.2f}" for s in sentiment_scores],
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
            title_text="Sentiment i aktywność według kategorii"
        )

        st.plotly_chart(fig, use_container_width=True)

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
                        text = tweet.get('text', '')[:150] + '...' if len(tweet.get('text', '')) > 150 else tweet.get('text', '')
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
        """Load latest processed data"""
        try:
            processed_files = glob.glob('data/processed/analysis_*.json')
            if not processed_files:
                return None

            latest_file = max(processed_files, key=os.path.getctime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Błąd ładowania danych: {e}")
            return None

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
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Wykresy", "🔍 Szczegóły", "🔥 Aktywność"])

        with tab1:
            self.render_main_metrics()

        with tab2:
            self.render_sentiment_chart()

        with tab3:
            self.render_category_details()

        with tab4:
            self.render_recent_activity()

        # Footer
        st.markdown("---")
        st.markdown("🤖 **X Financial Analyzer** - Automatyczna analiza sentymenty finansowego")


def main():
    """Main Streamlit app"""
    dashboard = StreamlitDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()