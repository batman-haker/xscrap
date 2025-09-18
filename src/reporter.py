import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

class MarkdownReporter:
    """Generate comprehensive Markdown reports from analysis data"""

    def __init__(self):
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def generate_daily_report(self, processed_data: Dict[str, Any],
                            claude_analysis: Dict[str, Any],
                            executive_summary: Dict[str, Any]) -> str:
        """Generate daily financial analysis report"""

        timestamp = datetime.now()
        report_date = timestamp.strftime('%Y-%m-%d')

        # Build report content
        report_content = []

        # Header
        report_content.append(f"# 📊 Raport Finansowy - {report_date}")
        report_content.append("")
        report_content.append(f"*Wygenerowano: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}*")
        report_content.append("")

        # Executive Summary
        report_content.extend(self._generate_executive_summary_section(executive_summary))

        # Market Overview
        report_content.extend(self._generate_market_overview_section(processed_data, claude_analysis))

        # Investment Recommendations
        report_content.extend(self._generate_recommendations_section(processed_data, claude_analysis))

        # Category Analysis
        report_content.extend(self._generate_category_analysis_section(processed_data))

        # Top Tweets
        report_content.extend(self._generate_top_tweets_section(processed_data))

        # Claude AI Insights
        report_content.extend(self._generate_claude_insights_section(claude_analysis))

        # Technical Details
        report_content.extend(self._generate_technical_details_section(processed_data))

        # Footer
        report_content.append("")
        report_content.append("---")
        report_content.append("🤖 *Wygenerowane automatycznie przez X Financial Analyzer*")
        report_content.append("")
        report_content.append(f"📈 *Analiza oparta na {processed_data.get('total_tweets', 0)} tweetach*")

        return "\n".join(report_content)

    def _generate_executive_summary_section(self, executive_summary: Dict[str, Any]) -> List[str]:
        """Generate executive summary section"""
        section = []

        section.append("## 🎯 Podsumowanie Wykonawcze")
        section.append("")

        sentiment = executive_summary.get('market_sentiment', 'Nieznany')
        risk_level = executive_summary.get('risk_level', 'Średni')
        confidence = executive_summary.get('confidence_level', 0.0)

        # Sentiment icon mapping
        sentiment_icons = {
            'Very Positive': '🚀',
            'Positive': '📈',
            'Slightly Positive': '↗️',
            'Slightly Negative': '↘️',
            'Negative': '📉',
            'Very Negative': '💥'
        }

        risk_icons = {
            'Low': '🟢',
            'Medium': '🟡',
            'High': '🔴'
        }

        icon = sentiment_icons.get(sentiment, '📊')
        risk_icon = risk_icons.get(risk_level, '🟡')

        section.append(f"**Sentiment rynkowy**: {icon} {sentiment}")
        section.append(f"**Poziom ryzyka**: {risk_icon} {risk_level}")
        section.append(f"**Pewność analizy**: {confidence:.1%}")
        section.append("")

        # Recommendations summary
        rec_summary = executive_summary.get('recommendation_summary', {})
        if rec_summary:
            section.append("### 📋 Rekomendacje - Podsumowanie")
            section.append("")
            section.append(f"- 🥇 **Silne Kupno**: {rec_summary.get('strong_buy', 0)} sektorów")
            section.append(f"- 📈 **Kupno**: {rec_summary.get('buy', 0)} sektorów")
            section.append(f"- ⏸️ **Trzymaj**: {rec_summary.get('hold', 0)} sektorów")
            section.append(f"- 📉 **Sprzedaj**: {rec_summary.get('sell', 0)} sektorów")
            section.append("")

        # Top opportunities and risks
        opportunities = executive_summary.get('top_opportunities', [])
        risks = executive_summary.get('main_risks', [])

        if opportunities:
            section.append("**🎯 Główne okazje**:")
            for opp in opportunities:
                section.append(f"- {opp.replace('_', ' ').title()}")
            section.append("")

        if risks:
            section.append("**⚠️ Główne ryzyka**:")
            for risk in risks:
                section.append(f"- {risk.replace('_', ' ').title()}")
            section.append("")

        return section

    def _generate_market_overview_section(self, processed_data: Dict[str, Any],
                                        claude_analysis: Dict[str, Any]) -> List[str]:
        """Generate market overview section"""
        section = []

        section.append("## 📈 Przegląd Rynkowy")
        section.append("")

        overall_sentiment = processed_data.get('overall_sentiment', {})
        overall_score = overall_sentiment.get('overall_score', 0.0)
        overall_label = overall_sentiment.get('sentiment_label', 'Nieznany')

        # Overall sentiment gauge
        gauge = self._create_sentiment_gauge(overall_score)
        section.append(f"### Ogólny Sentiment: {overall_label}")
        section.append("")
        section.append(f"```")
        section.append(f"Score: {overall_score:+.2f}")
        section.append(f"{gauge}")
        section.append(f"```")
        section.append("")

        # Category breakdown
        category_breakdown = overall_sentiment.get('category_breakdown', {})
        if category_breakdown:
            section.append("### 📊 Sentiment według kategorii")
            section.append("")
            section.append("| Kategoria | Score | Trend |")
            section.append("|-----------|-------|-------|")

            for category, score in category_breakdown.items():
                trend_icon = "📈" if score > 0.2 else "📉" if score < -0.2 else "➡️"
                category_name = category.replace('_', ' ').title()
                section.append(f"| {category_name} | {score:+.2f} | {trend_icon} |")

            section.append("")

        return section

    def _generate_recommendations_section(self, processed_data: Dict[str, Any],
                                        claude_analysis: Dict[str, Any]) -> List[str]:
        """Generate investment recommendations section"""
        section = []

        section.append("## 🏆 Rekomendacje Inwestycyjne")
        section.append("")

        # Load recommendations from Claude analysis or generate them
        recommendations = self._extract_recommendations_from_data(processed_data)

        if not recommendations:
            section.append("*Brak wystarczających danych do generowania rekomendacji.*")
            section.append("")
            return section

        # Group recommendations by action
        strong_buys = [r for r in recommendations if r.get('recommendation') == 'STRONG BUY']
        buys = [r for r in recommendations if r.get('recommendation') == 'BUY']
        holds = [r for r in recommendations if r.get('recommendation') == 'HOLD']
        sells = [r for r in recommendations if r.get('recommendation') in ['SELL', 'STRONG SELL']]

        # Strong Buy section
        if strong_buys:
            section.append("### 🥇 Silne Kupno")
            section.append("")
            for rec in strong_buys:
                category_name = rec['category'].replace('_', ' ').title()
                confidence = rec.get('confidence', 0.0)
                rationale = rec.get('rationale', 'Brak uzasadnienia')
                section.append(f"**{category_name}** (Pewność: {confidence:.1%})")
                section.append(f"- {rationale}")
                section.append("")

        # Buy section
        if buys:
            section.append("### 📈 Kupno")
            section.append("")
            for rec in buys:
                category_name = rec['category'].replace('_', ' ').title()
                confidence = rec.get('confidence', 0.0)
                rationale = rec.get('rationale', 'Brak uzasadnienia')
                section.append(f"**{category_name}** (Pewność: {confidence:.1%})")
                section.append(f"- {rationale}")
                section.append("")

        # Hold section
        if holds:
            section.append("### ⏸️ Trzymaj / Obserwuj")
            section.append("")
            for rec in holds:
                category_name = rec['category'].replace('_', ' ').title()
                confidence = rec.get('confidence', 0.0)
                rationale = rec.get('rationale', 'Brak uzasadnienia')
                section.append(f"**{category_name}** (Pewność: {confidence:.1%})")
                section.append(f"- {rationale}")
                section.append("")

        # Sell section
        if sells:
            section.append("### ⚠️ Ostrożnie / Sprzedaj")
            section.append("")
            for rec in sells:
                category_name = rec['category'].replace('_', ' ').title()
                confidence = rec.get('confidence', 0.0)
                rationale = rec.get('rationale', 'Brak uzasadnienia')
                section.append(f"**{category_name}** (Pewność: {confidence:.1%})")
                section.append(f"- {rationale}")
                section.append("")

        return section

    def _generate_category_analysis_section(self, processed_data: Dict[str, Any]) -> List[str]:
        """Generate detailed category analysis section"""
        section = []

        section.append("## 🔍 Analiza Szczegółowa")
        section.append("")

        categories = processed_data.get('categories', {})

        for category, data in categories.items():
            if not data or data.get('tweet_count', 0) == 0:
                continue

            category_name = category.replace('_', ' ').title()
            tweet_count = data.get('tweet_count', 0)
            sentiment_label = data.get('sentiment_label', 'Nieznany')
            weighted_sentiment = data.get('weighted_sentiment', 0.0)
            avg_influence = data.get('avg_influence', 0.0)

            section.append(f"### {category_name}")
            section.append("")
            section.append(f"**Tweets przeanalizowane**: {tweet_count}")
            section.append(f"**Sentiment**: {sentiment_label} ({weighted_sentiment:+.2f})")
            section.append(f"**Średni wpływ**: {avg_influence:.2f}")
            section.append("")

            # Sentiment distribution
            sentiment_dist = data.get('sentiment_distribution', {})
            if sentiment_dist:
                positive = sentiment_dist.get('positive', 0.0)
                negative = sentiment_dist.get('negative', 0.0)
                neutral = sentiment_dist.get('neutral', 0.0)

                section.append(f"**Rozkład sentimentu**:")
                section.append(f"- Pozytywny: {positive:.1%}")
                section.append(f"- Negatywny: {negative:.1%}")
                section.append(f"- Neutralny: {neutral:.1%}")
                section.append("")

        return section

    def _generate_top_tweets_section(self, processed_data: Dict[str, Any]) -> List[str]:
        """Generate top tweets section"""
        section = []

        section.append("## 📢 Najważniejsze Tweety")
        section.append("")

        top_tweets = processed_data.get('top_tweets', [])[:5]  # Top 5

        if not top_tweets:
            section.append("*Brak dostępnych tweetów.*")
            section.append("")
            return section

        for i, tweet in enumerate(top_tweets, 1):
            user = tweet.get('user', {})
            username = user.get('screen_name', 'Unknown')
            name = user.get('name', 'Unknown')
            text = tweet.get('text', '')
            impact_score = tweet.get('impact_score', 0.0)
            sentiment = tweet.get('sentiment', {})
            sentiment_score = sentiment.get('polarity', 0.0)

            # Limit text length for display
            display_text = text[:200] + '...' if len(text) > 200 else text

            section.append(f"### {i}. @{username} ({name})")
            section.append("")
            section.append(f"> {display_text}")
            section.append("")
            section.append(f"**Impact Score**: {impact_score:.2f} | **Sentiment**: {sentiment_score:+.2f}")
            section.append("")

        return section

    def _generate_claude_insights_section(self, claude_analysis: Dict[str, Any]) -> List[str]:
        """Generate Claude AI insights section"""
        section = []

        section.append("## 🤖 Analiza AI (Claude)")
        section.append("")

        claude_text = claude_analysis.get('claude_analysis', '')
        if claude_text and claude_text != "Analysis unavailable due to API error":
            # Split Claude's analysis into readable sections
            lines = claude_text.split('\n')
            for line in lines:
                if line.strip():
                    section.append(line)
                else:
                    section.append("")
        else:
            section.append("*Analiza Claude niedostępna.*")
            if 'error' in claude_analysis:
                section.append(f"*Błąd: {claude_analysis['error']}*")

        section.append("")

        # Analysis metadata
        confidence = claude_analysis.get('confidence_score', 0.0)
        data_quality = claude_analysis.get('data_quality', 'unknown')

        section.append(f"**Pewność analizy**: {confidence:.1%}")
        section.append(f"**Jakość danych**: {data_quality.title()}")
        section.append("")

        return section

    def _generate_technical_details_section(self, processed_data: Dict[str, Any]) -> List[str]:
        """Generate technical details section"""
        section = []

        section.append("## ⚙️ Szczegóły Techniczne")
        section.append("")

        total_tweets = processed_data.get('total_tweets', 0)
        processed_at = processed_data.get('processed_at', 'Unknown')

        section.append(f"- **Łączna liczba tweetów**: {total_tweets}")
        section.append(f"- **Czas przetwarzania**: {processed_at}")

        # Category tweet counts
        categories = processed_data.get('categories', {})
        if categories:
            section.append("- **Tweety według kategorii**:")
            for category, data in categories.items():
                tweet_count = data.get('tweet_count', 0)
                if tweet_count > 0:
                    category_name = category.replace('_', ' ').title()
                    section.append(f"  - {category_name}: {tweet_count}")

        section.append("")

        return section

    def _create_sentiment_gauge(self, score: float) -> str:
        """Create ASCII sentiment gauge"""
        # Normalize score to 0-20 range for gauge
        normalized = int((score + 1) * 10)  # -1 to 1 becomes 0 to 20
        normalized = max(0, min(20, normalized))  # Clamp to range

        gauge = ['▁'] * 21
        gauge[10] = '│'  # Center line

        if normalized < 10:
            # Negative sentiment - fill from center left
            for i in range(normalized, 10):
                gauge[i] = '█'
        elif normalized > 10:
            # Positive sentiment - fill from center right
            for i in range(11, normalized + 1):
                gauge[i] = '█'
        else:
            # Neutral
            gauge[10] = '█'

        return ''.join(gauge) + f' ({score:+.2f})'

    def _extract_recommendations_from_data(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract or generate recommendations from processed data"""
        # This would typically come from Claude analysis
        # For now, generate basic recommendations based on sentiment

        recommendations = []
        categories = processed_data.get('categories', {})

        for category, data in categories.items():
            if not data or data.get('tweet_count', 0) == 0:
                continue

            weighted_sentiment = data.get('weighted_sentiment', 0.0)
            avg_influence = data.get('avg_influence', 0.0)
            tweet_count = data.get('tweet_count', 0)

            # Simple recommendation logic
            if weighted_sentiment >= 0.7:
                action = 'STRONG BUY'
                rationale = f'Bardzo pozytywny sentiment ({weighted_sentiment:.2f}) z wysokim wpływem'
            elif weighted_sentiment >= 0.3:
                action = 'BUY'
                rationale = f'Pozytywny sentiment ({weighted_sentiment:.2f})'
            elif weighted_sentiment >= -0.3:
                action = 'HOLD'
                rationale = f'Neutralny sentiment ({weighted_sentiment:.2f}) - czekaj na sygnały'
            elif weighted_sentiment >= -0.7:
                action = 'SELL'
                rationale = f'Negatywny sentiment ({weighted_sentiment:.2f})'
            else:
                action = 'STRONG SELL'
                rationale = f'Bardzo negatywny sentiment ({weighted_sentiment:.2f})'

            confidence = min(abs(weighted_sentiment) * avg_influence * (tweet_count / 10.0), 1.0)

            recommendations.append({
                'category': category,
                'recommendation': action,
                'confidence': confidence,
                'rationale': rationale,
                'sentiment_score': weighted_sentiment
            })

        return recommendations

    def save_report(self, report_content: str, report_type: str = 'daily') -> str:
        """Save report to file"""
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y%m%d')
        time_str = timestamp.strftime('%H%M%S')

        filename = f"reports/{report_type}/raport_{report_type}_{date_str}_{time_str}.md"
        os.makedirs(f"reports/{report_type}", exist_ok=True)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)

            self.logger.info(f"Report saved to {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error saving report: {e}")
            return ""

    def generate_weekly_report(self, daily_reports: List[str]) -> str:
        """Generate weekly summary report from daily reports"""
        # Implementation for weekly report generation
        # This would analyze trends across multiple daily reports
        timestamp = datetime.now()
        week_start = timestamp - timedelta(days=7)

        report_content = []
        report_content.append(f"# 📊 Raport Tygodniowy - {week_start.strftime('%Y-%m-%d')} do {timestamp.strftime('%Y-%m-%d')}")
        report_content.append("")
        report_content.append("## 📈 Podsumowanie Tygodnia")
        report_content.append("")
        report_content.append("*Analiza trendów z ostatnich 7 dni...*")
        report_content.append("")

        # TODO: Implement detailed weekly analysis
        # This would involve:
        # 1. Loading all daily reports from the week
        # 2. Analyzing sentiment trends
        # 3. Tracking recommendation changes
        # 4. Identifying weekly patterns

        return "\n".join(report_content)


if __name__ == "__main__":
    # Test report generation
    reporter = MarkdownReporter()

    # Load latest processed data for testing
    import glob
    processed_files = glob.glob('data/processed/analysis_*.json')
    if processed_files:
        latest_file = max(processed_files)
        with open(latest_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)

        # Mock Claude analysis and executive summary
        mock_claude = {
            'claude_analysis': 'Test analysis from Claude AI',
            'confidence_score': 0.75,
            'data_quality': 'medium'
        }

        mock_executive = {
            'market_sentiment': 'Positive',
            'risk_level': 'Medium',
            'confidence_level': 0.75,
            'recommendation_summary': {
                'strong_buy': 1,
                'buy': 2,
                'hold': 1,
                'sell': 0
            },
            'top_opportunities': ['cryptocurrency'],
            'main_risks': []
        }

        report = reporter.generate_daily_report(test_data, mock_claude, mock_executive)
        filename = reporter.save_report(report, 'daily')
        print(f"Test report generated: {filename}")
    else:
        print("No processed data files found for testing")