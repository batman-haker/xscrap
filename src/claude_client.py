import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeAnalyst:
    """Claude AI integration for advanced financial analysis and insights"""

    def __init__(self):
        self.api_key = os.getenv('CLAUDE_API_KEY')
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-sonnet-20240229"

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def analyze_market_sentiment(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive market analysis using Claude"""

        # Prepare data summary for Claude
        data_summary = self._prepare_data_summary(processed_data)

        prompt = f"""
        You are a professional financial analyst specializing in social media sentiment analysis and market intelligence.
        Analyze the following Twitter data from financial experts and provide comprehensive insights.

        DATA SUMMARY:
        {data_summary}

        Please provide a detailed analysis in the following format:

        1. MARKET OVERVIEW
        - Overall sentiment assessment
        - Key market trends identified
        - Risk level evaluation (Low/Medium/High)

        2. SECTOR ANALYSIS
        - Cryptocurrency sentiment and outlook
        - Traditional markets (US/Polish economy)
        - Commodities and safe-haven assets
        - Geopolitical impact assessment

        3. INVESTMENT RECOMMENDATIONS
        - Strong Buy opportunities with rationale
        - Buy recommendations with reasoning
        - Hold/Caution areas with explanations
        - Sell/Avoid recommendations if any

        4. KEY INSIGHTS
        - Most significant findings from the data
        - Potential market catalysts identified
        - Early warning signals if present

        5. RISK ASSESSMENT
        - Primary risks identified
        - Market volatility indicators
        - Recommended portfolio adjustments

        Please be specific, actionable, and base all recommendations on the sentiment data provided.
        Include confidence levels where appropriate.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            analysis = response.content[0].text

            return {
                'analysis_timestamp': datetime.now().isoformat(),
                'claude_analysis': analysis,
                'confidence_score': self._calculate_analysis_confidence(processed_data),
                'data_quality': self._assess_data_quality(processed_data)
            }

        except Exception as e:
            self.logger.error(f"Error generating Claude analysis: {e}")
            return {
                'analysis_timestamp': datetime.now().isoformat(),
                'claude_analysis': "Analysis unavailable due to API error",
                'error': str(e),
                'confidence_score': 0.0,
                'data_quality': 'unknown'
            }

    def generate_recommendations(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific investment recommendations"""

        categories = processed_data.get('categories', {})
        overall_sentiment = processed_data.get('overall_sentiment', {})

        recommendations = []

        # Get recommendation rules from config
        try:
            with open('config/categories.json', 'r') as f:
                config = json.load(f)
                rec_rules = config.get('recommendation_rules', {})
        except:
            rec_rules = {}

        for category, data in categories.items():
            if not data or data.get('tweet_count', 0) == 0:
                continue

            weighted_sentiment = data.get('weighted_sentiment', 0.0)
            avg_influence = data.get('avg_influence', 0.0)
            tweet_count = data.get('tweet_count', 0)

            # Determine recommendation based on sentiment and rules
            recommendation = self._determine_recommendation(
                weighted_sentiment, avg_influence, tweet_count, rec_rules
            )

            if recommendation:
                recommendations.append({
                    'category': category,
                    'recommendation': recommendation['action'],
                    'confidence': recommendation['confidence'],
                    'sentiment_score': weighted_sentiment,
                    'rationale': recommendation['rationale'],
                    'risk_level': self._assess_category_risk(category, weighted_sentiment),
                    'time_horizon': recommendation.get('time_horizon', 'medium_term')
                })

        return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)

    def _prepare_data_summary(self, processed_data: Dict[str, Any]) -> str:
        """Prepare a concise summary of the processed data for Claude"""

        summary_parts = []

        # Overall stats
        total_tweets = processed_data.get('total_tweets', 0)
        overall_sentiment = processed_data.get('overall_sentiment', {})

        summary_parts.append(f"Total Tweets Analyzed: {total_tweets}")
        summary_parts.append(f"Overall Sentiment: {overall_sentiment.get('sentiment_label', 'Unknown')} "
                           f"(Score: {overall_sentiment.get('overall_score', 0.0):.2f})")

        # Category breakdown
        categories = processed_data.get('categories', {})
        summary_parts.append("\nCategory Breakdown:")

        for category, data in categories.items():
            if data.get('tweet_count', 0) > 0:
                sentiment_label = data.get('sentiment_label', 'Unknown')
                tweet_count = data.get('tweet_count', 0)
                weighted_sentiment = data.get('weighted_sentiment', 0.0)

                summary_parts.append(
                    f"- {category.replace('_', ' ').title()}: {sentiment_label} "
                    f"({tweet_count} tweets, weighted score: {weighted_sentiment:.2f})"
                )

        # Top insights
        insights = processed_data.get('insights', [])
        if insights:
            summary_parts.append("\nKey Insights:")
            for insight in insights[:5]:  # Top 5 insights
                summary_parts.append(f"- {insight}")

        # Top influential tweets (just the text, not full objects)
        top_tweets = processed_data.get('top_tweets', [])
        if top_tweets:
            summary_parts.append("\nMost Influential Tweets:")
            for i, tweet in enumerate(top_tweets[:3], 1):
                text = tweet.get('text', '')[:100] + '...' if len(tweet.get('text', '')) > 100 else tweet.get('text', '')
                user = tweet.get('user', {}).get('screen_name', 'Unknown')
                impact = tweet.get('impact_score', 0.0)
                summary_parts.append(f"{i}. @{user}: \"{text}\" (Impact: {impact:.2f})")

        return '\n'.join(summary_parts)

    def _determine_recommendation(self, sentiment: float, influence: float,
                                tweet_count: int, rules: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine investment recommendation based on sentiment and rules"""

        confidence = min(abs(sentiment) * influence * (tweet_count / 10.0), 1.0)

        if sentiment >= rules.get('strong_buy', {}).get('min_sentiment', 0.7):
            return {
                'action': 'STRONG BUY',
                'confidence': confidence,
                'rationale': f'Very positive sentiment ({sentiment:.2f}) with high influence',
                'time_horizon': 'short_term'
            }
        elif sentiment >= rules.get('buy', {}).get('min_sentiment', 0.4):
            return {
                'action': 'BUY',
                'confidence': confidence,
                'rationale': f'Positive sentiment ({sentiment:.2f}) detected',
                'time_horizon': 'medium_term'
            }
        elif sentiment <= rules.get('strong_sell', {}).get('max_sentiment', -0.7):
            return {
                'action': 'STRONG SELL',
                'confidence': confidence,
                'rationale': f'Very negative sentiment ({sentiment:.2f}) with high influence',
                'time_horizon': 'short_term'
            }
        elif sentiment <= rules.get('sell', {}).get('max_sentiment', -0.4):
            return {
                'action': 'SELL',
                'confidence': confidence,
                'rationale': f'Negative sentiment ({sentiment:.2f}) detected',
                'time_horizon': 'medium_term'
            }
        else:
            return {
                'action': 'HOLD',
                'confidence': confidence,
                'rationale': f'Neutral sentiment ({sentiment:.2f}) - wait for clearer signals',
                'time_horizon': 'medium_term'
            }

    def _assess_category_risk(self, category: str, sentiment: float) -> str:
        """Assess risk level for a category"""

        risk_mapping = {
            'cryptocurrency': 'high',
            'geopolitics': 'high',
            'us_economy': 'medium',
            'polish_economy': 'medium',
            'gold_commodities': 'low'
        }

        base_risk = risk_mapping.get(category, 'medium')

        # Adjust based on sentiment volatility
        if abs(sentiment) > 0.8:
            if base_risk == 'low':
                return 'medium'
            elif base_risk == 'medium':
                return 'high'
            else:
                return 'very_high'

        return base_risk

    def _calculate_analysis_confidence(self, processed_data: Dict[str, Any]) -> float:
        """Calculate overall confidence in the analysis"""

        total_tweets = processed_data.get('total_tweets', 0)
        overall_sentiment = processed_data.get('overall_sentiment', {})

        # Base confidence on tweet volume
        volume_confidence = min(total_tweets / 100.0, 1.0)

        # Sentiment confidence
        sentiment_confidence = overall_sentiment.get('confidence', 0.0)

        # Category coverage
        categories = processed_data.get('categories', {})
        active_categories = sum(1 for cat_data in categories.values()
                              if cat_data.get('tweet_count', 0) > 0)
        coverage_confidence = min(active_categories / 5.0, 1.0)

        # Combined confidence
        return (volume_confidence * 0.4 + sentiment_confidence * 0.4 + coverage_confidence * 0.2)

    def _assess_data_quality(self, processed_data: Dict[str, Any]) -> str:
        """Assess the quality of the input data"""

        total_tweets = processed_data.get('total_tweets', 0)
        categories = processed_data.get('categories', {})

        active_categories = sum(1 for cat_data in categories.values()
                              if cat_data.get('tweet_count', 0) > 0)

        if total_tweets >= 50 and active_categories >= 3:
            return 'high'
        elif total_tweets >= 20 and active_categories >= 2:
            return 'medium'
        elif total_tweets >= 5:
            return 'low'
        else:
            return 'insufficient'

    def generate_executive_summary(self, processed_data: Dict[str, Any],
                                 claude_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary for reports"""

        overall_sentiment = processed_data.get('overall_sentiment', {})
        recommendations = self.generate_recommendations(processed_data)

        # Extract key recommendations by action type
        strong_buys = [r for r in recommendations if r['recommendation'] == 'STRONG BUY']
        buys = [r for r in recommendations if r['recommendation'] == 'BUY']
        holds = [r for r in recommendations if r['recommendation'] == 'HOLD']
        sells = [r for r in recommendations if r['recommendation'] in ['SELL', 'STRONG SELL']]

        return {
            'timestamp': datetime.now().isoformat(),
            'market_sentiment': overall_sentiment.get('sentiment_label', 'Unknown'),
            'confidence_level': claude_analysis.get('confidence_score', 0.0),
            'risk_level': self._determine_overall_risk(overall_sentiment),
            'total_signals': len(recommendations),
            'recommendation_summary': {
                'strong_buy': len(strong_buys),
                'buy': len(buys),
                'hold': len(holds),
                'sell': len(sells)
            },
            'top_opportunities': [r['category'] for r in strong_buys[:3]],
            'main_risks': [r['category'] for r in sells[:3]],
            'data_quality': claude_analysis.get('data_quality', 'unknown')
        }

    def _determine_overall_risk(self, overall_sentiment: Dict[str, Any]) -> str:
        """Determine overall market risk level"""

        sentiment_score = overall_sentiment.get('overall_score', 0.0)
        confidence = overall_sentiment.get('confidence', 0.0)

        if abs(sentiment_score) > 0.7 and confidence > 0.7:
            return 'High'
        elif abs(sentiment_score) > 0.4 or confidence < 0.4:
            return 'Medium'
        else:
            return 'Low'


if __name__ == "__main__":
    # Test the Claude client with sample data
    analyst = ClaudeAnalyst()

    # Load latest processed data for testing
    import glob
    processed_files = glob.glob('data/processed/analysis_*.json')
    if processed_files:
        latest_file = max(processed_files)
        with open(latest_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)

        analysis = analyst.analyze_market_sentiment(test_data)
        print("Claude Analysis Generated Successfully")
        print(f"Confidence: {analysis.get('confidence_score', 0.0):.2f}")
    else:
        print("No processed data files found for testing")