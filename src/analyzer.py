import json
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from textblob import TextBlob
import logging

class SentimentAnalyzer:
    """Advanced sentiment analysis for financial content"""

    def __init__(self):
        self.keywords_config = self._load_keywords_config()
        self.categories_config = self._load_categories_config()

        # Financial sentiment lexicon weights
        self.financial_weights = {
            # Positive
            'bullish': 2.0, 'buy': 1.5, 'pump': 1.8, 'moon': 2.2, 'rocket': 2.0,
            'gains': 1.5, 'profit': 1.4, 'green': 1.2, 'surge': 1.6, 'rally': 1.5,
            'boom': 1.8, 'opportunity': 1.3, 'optimistic': 1.4, 'strong': 1.3,
            'growth': 1.4, 'breakout': 1.7, 'uptrend': 1.5, 'support': 1.2,

            # Negative
            'bearish': -2.0, 'sell': -1.5, 'dump': -1.8, 'crash': -2.5, 'drop': -1.4,
            'loss': -1.5, 'red': -1.2, 'decline': -1.4, 'correction': -1.6,
            'recession': -2.2, 'fear': -1.8, 'panic': -2.0, 'pessimistic': -1.4,
            'weak': -1.3, 'risk': -1.1, 'breakdown': -1.7, 'downtrend': -1.5,
            'resistance': -1.2, 'bubble': -1.8
        }

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _load_keywords_config(self) -> Dict[str, Any]:
        """Load keywords configuration"""
        try:
            with open('config/keywords.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error("keywords.json not found")
            return {}

    def _load_categories_config(self) -> Dict[str, Any]:
        """Load categories configuration"""
        try:
            with open('config/categories.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error("categories.json not found")
            return {}

    def clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # Remove mentions and hashtags for sentiment analysis
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text.lower()

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text with financial context"""
        clean_text = self.clean_text(text)

        # Basic TextBlob sentiment
        blob = TextBlob(text)
        base_polarity = blob.sentiment.polarity
        base_subjectivity = blob.sentiment.subjectivity

        # Financial-specific sentiment adjustment
        financial_score = 0.0
        word_count = 0

        words = clean_text.split()
        for word in words:
            if word in self.financial_weights:
                financial_score += self.financial_weights[word]
                word_count += 1

        # Combine scores
        if word_count > 0:
            financial_score = financial_score / word_count
            # Weight financial terms more heavily for financial content
            combined_polarity = (base_polarity * 0.4) + (financial_score * 0.6)
        else:
            combined_polarity = base_polarity

        # Normalize to [-1, 1] range
        combined_polarity = max(-1.0, min(1.0, combined_polarity))

        return {
            'polarity': combined_polarity,
            'subjectivity': base_subjectivity,
            'financial_score': financial_score,
            'confidence': abs(combined_polarity) * (1 - base_subjectivity)
        }

    def categorize_tweet(self, tweet: Dict[str, Any]) -> List[str]:
        """Categorize tweet based on content"""
        text = tweet.get('text', '').lower()
        categories = []

        for category, keywords in self.keywords_config.items():
            if category in ['sentiment_positive', 'sentiment_negative']:
                continue

            for keyword in keywords:
                if keyword.lower() in text:
                    categories.append(category)
                    break

        return list(set(categories))

    def calculate_influence_score(self, tweet: Dict[str, Any]) -> float:
        """Calculate influence score based on user metrics and engagement"""
        user = tweet.get('user', {})
        followers = user.get('followers_count', 0)
        retweets = tweet.get('retweet_count', 0)
        likes = tweet.get('favorite_count', 0)

        # Logarithmic scaling for followers
        follower_score = np.log10(max(followers, 1)) / 8.0  # Normalize to ~0-1

        # Engagement score
        engagement_score = (retweets * 2 + likes) / 1000.0  # Weight retweets more

        # Account priority bonus
        priority_bonus = {
            'high': 1.5,
            'medium': 1.0,
            'low': 0.7
        }.get(tweet.get('account_priority', 'medium'), 1.0)

        influence_score = (follower_score + engagement_score) * priority_bonus
        return min(influence_score, 5.0)  # Cap at 5.0


class DataProcessor:
    """Main data processing and analysis orchestrator"""

    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.categories_config = self._load_categories_config()

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _load_categories_config(self) -> Dict[str, Any]:
        """Load categories configuration"""
        try:
            with open('config/categories.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error("categories.json not found")
            return {}

    def process_tweets(self, tweets_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Process all tweets and generate analysis"""
        processed_data = {
            'processed_at': datetime.now().isoformat(),
            'total_tweets': 0,
            'categories': {},
            'overall_sentiment': {},
            'top_tweets': [],
            'insights': []
        }

        all_tweets = []

        # Process each category
        for category, tweets in tweets_data.items():
            if not tweets:
                continue

            category_analysis = self._process_category(category, tweets)
            processed_data['categories'][category] = category_analysis
            all_tweets.extend(tweets)

        processed_data['total_tweets'] = len(all_tweets)

        # Calculate overall sentiment
        if all_tweets:
            processed_data['overall_sentiment'] = self._calculate_overall_sentiment(all_tweets)
            processed_data['top_tweets'] = self._get_top_tweets(all_tweets)
            processed_data['insights'] = self._generate_insights(processed_data)

        return processed_data

    def _process_category(self, category: str, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process tweets for a specific category"""
        if not tweets:
            return {}

        sentiments = []
        influences = []
        processed_tweets = []

        for tweet in tweets:
            # Analyze sentiment
            sentiment = self.sentiment_analyzer.analyze_sentiment(tweet['text'])

            # Calculate influence
            influence = self.sentiment_analyzer.calculate_influence_score(tweet)

            # Categorize content
            content_categories = self.sentiment_analyzer.categorize_tweet(tweet)

            # Store processed tweet
            processed_tweet = {
                **tweet,
                'sentiment': sentiment,
                'influence_score': influence,
                'content_categories': content_categories,
                'weighted_sentiment': sentiment['polarity'] * influence
            }

            processed_tweets.append(processed_tweet)
            sentiments.append(sentiment['polarity'])
            influences.append(influence)

        # Calculate category statistics
        avg_sentiment = np.mean(sentiments) if sentiments else 0.0
        weighted_sentiment = sum(t['weighted_sentiment'] for t in processed_tweets) / sum(influences) if influences else 0.0

        sentiment_label = self._get_sentiment_label(weighted_sentiment)

        return {
            'tweet_count': len(tweets),
            'avg_sentiment': avg_sentiment,
            'weighted_sentiment': weighted_sentiment,
            'sentiment_label': sentiment_label,
            'avg_influence': np.mean(influences) if influences else 0.0,
            'sentiment_distribution': self._get_sentiment_distribution(sentiments),
            'top_tweets': sorted(processed_tweets, key=lambda x: x['influence_score'], reverse=True)[:5],
            'processed_tweets': processed_tweets
        }

    def _calculate_overall_sentiment(self, all_tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall market sentiment"""
        category_weights = self.categories_config.get('categories', {})

        weighted_sentiments = []
        category_sentiments = {}

        # Group by category
        for tweet in all_tweets:
            category = tweet.get('account_category', 'unknown')
            sentiment = self.sentiment_analyzer.analyze_sentiment(tweet['text'])
            influence = self.sentiment_analyzer.calculate_influence_score(tweet)

            weight = category_weights.get(category, {}).get('weight', 1.0)
            weighted_sentiment = sentiment['polarity'] * influence * weight

            weighted_sentiments.append(weighted_sentiment)

            if category not in category_sentiments:
                category_sentiments[category] = []
            category_sentiments[category].append(sentiment['polarity'])

        overall_sentiment = np.mean(weighted_sentiments) if weighted_sentiments else 0.0

        return {
            'overall_score': overall_sentiment,
            'sentiment_label': self._get_sentiment_label(overall_sentiment),
            'category_breakdown': {
                cat: np.mean(scores) for cat, scores in category_sentiments.items()
            },
            'confidence': min(abs(overall_sentiment) + 0.1, 1.0)
        }

    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        thresholds = self.categories_config.get('sentiment_thresholds', {})

        if score >= thresholds.get('very_positive', 0.8):
            return 'Very Positive'
        elif score >= thresholds.get('positive', 0.4):
            return 'Positive'
        elif score >= thresholds.get('neutral', 0.0):
            return 'Slightly Positive'
        elif score >= thresholds.get('negative', -0.4):
            return 'Slightly Negative'
        elif score >= thresholds.get('very_negative', -0.8):
            return 'Negative'
        else:
            return 'Very Negative'

    def _get_sentiment_distribution(self, sentiments: List[float]) -> Dict[str, float]:
        """Calculate sentiment distribution"""
        if not sentiments:
            return {}

        positive = sum(1 for s in sentiments if s > 0.1)
        negative = sum(1 for s in sentiments if s < -0.1)
        neutral = len(sentiments) - positive - negative

        total = len(sentiments)
        return {
            'positive': positive / total,
            'negative': negative / total,
            'neutral': neutral / total
        }

    def _get_top_tweets(self, all_tweets: List[Dict[str, Any]], count: int = 10) -> List[Dict[str, Any]]:
        """Get most influential tweets"""
        processed_tweets = []

        for tweet in all_tweets:
            sentiment = self.sentiment_analyzer.analyze_sentiment(tweet['text'])
            influence = self.sentiment_analyzer.calculate_influence_score(tweet)

            processed_tweets.append({
                **tweet,
                'sentiment': sentiment,
                'influence_score': influence,
                'impact_score': abs(sentiment['polarity']) * influence
            })

        return sorted(processed_tweets, key=lambda x: x['impact_score'], reverse=True)[:count]

    def _generate_insights(self, processed_data: Dict[str, Any]) -> List[str]:
        """Generate key insights from processed data"""
        insights = []

        overall_sentiment = processed_data.get('overall_sentiment', {})
        categories = processed_data.get('categories', {})

        # Overall market insight
        sentiment_score = overall_sentiment.get('overall_score', 0.0)
        sentiment_label = overall_sentiment.get('sentiment_label', 'Neutral')

        insights.append(f"Overall market sentiment: {sentiment_label} (score: {sentiment_score:.2f})")

        # Category insights
        for category, data in categories.items():
            if data.get('tweet_count', 0) > 0:
                weighted_sentiment = data.get('weighted_sentiment', 0.0)
                tweet_count = data.get('tweet_count', 0)
                insights.append(
                    f"{category.replace('_', ' ').title()}: {data.get('sentiment_label', 'Neutral')} "
                    f"({tweet_count} tweets, score: {weighted_sentiment:.2f})"
                )

        # Risk indicators
        if sentiment_score < -0.5:
            insights.append("⚠️ High negative sentiment detected - increased market risk")
        elif sentiment_score > 0.7:
            insights.append("🚀 Strong positive sentiment - potential overheating risk")

        return insights

    def save_processed_data(self, processed_data: Dict[str, Any]) -> str:
        """Save processed data to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/processed/analysis_{timestamp}.json"

        os.makedirs('data/processed', exist_ok=True)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Processed data saved to {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error saving processed data: {e}")
            return ""

    def load_and_process(self, raw_data_file: str) -> str:
        """Load raw data and process it"""
        try:
            with open(raw_data_file, 'r', encoding='utf-8') as f:
                tweets_data = json.load(f)

            self.logger.info(f"Processing data from {raw_data_file}")
            processed_data = self.process_tweets(tweets_data)
            filename = self.save_processed_data(processed_data)

            return filename

        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
            return ""


if __name__ == "__main__":
    processor = DataProcessor()

    # Find latest raw data file
    raw_files = [f for f in os.listdir('data/raw') if f.startswith('tweets_') and f.endswith('.json')]
    if raw_files:
        latest_file = max(raw_files)
        processor.load_and_process(f"data/raw/{latest_file}")
    else:
        print("No raw data files found")