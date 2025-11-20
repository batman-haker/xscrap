#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper import DataCollector
from src.analyzer import DataProcessor
import json

def test_app():
    print("=== Testing Updated Application ===")
    print("Testing with @MarekLangalis data...")

    # Initialize collector
    try:
        collector = DataCollector()
        print("OK: DataCollector initialized")
    except Exception as e:
        print(f"ERROR: DataCollector failed: {e}")
        return False

    # Test data collection
    print("\n1. Testing data collection...")
    print("This will take time due to rate limiting (5 sec between requests)")

    try:
        tweets_data = collector.collect_all_tweets(hours_back=24)

        total_tweets = sum(len(tweets) for tweets in tweets_data.values())
        print(f"SUCCESS: Collected {total_tweets} tweets total")

        # Show details
        for category, tweets in tweets_data.items():
            if tweets:
                print(f"  Category {category}: {len(tweets)} tweets")

                # Show first tweet
                if tweets:
                    tweet = tweets[0]
                    print(f"    Text: {tweet['text'][:100]}...")
                    print(f"    User: @{tweet['user']['screen_name']}")
                    print(f"    Date: {tweet['created_at']}")
                    print(f"    Likes: {tweet['favorite_count']}")
                    print(f"    Retweets: {tweet['retweet_count']}")

    except Exception as e:
        print(f"ERROR: Data collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Save raw data
    print("\n2. Saving raw data...")
    try:
        filename = collector.save_raw_data(tweets_data)
        if filename:
            print(f"SUCCESS: Raw data saved to {filename}")
        else:
            print("ERROR: Failed to save raw data")
            return False
    except Exception as e:
        print(f"ERROR: Save failed: {e}")
        return False

    # Test processing
    print("\n3. Testing data processing...")
    try:
        processor = DataProcessor()
        processed_data = processor.process_tweets(tweets_data)

        total = processed_data.get('total_tweets', 0)
        sentiment_info = processed_data.get('overall_sentiment', {})
        sentiment_label = sentiment_info.get('sentiment_label', 'Unknown')
        sentiment_score = sentiment_info.get('overall_score', 0.0)

        print(f"SUCCESS: Processed {total} tweets")
        print(f"Overall sentiment: {sentiment_label} (score: {sentiment_score:.2f})")

        # Show category details
        categories = processed_data.get('categories', {})
        for category, data in categories.items():
            if data.get('tweet_count', 0) > 0:
                cat_sentiment = data.get('sentiment_label', 'Unknown')
                cat_score = data.get('weighted_sentiment', 0.0)
                cat_count = data.get('tweet_count', 0)
                print(f"  {category}: {cat_sentiment} ({cat_score:.2f}) - {cat_count} tweets")

        # Show insights
        insights = processed_data.get('insights', [])
        if insights:
            print("\nKey insights:")
            for insight in insights[:3]:
                print(f"  - {insight}")

    except Exception as e:
        print(f"ERROR: Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n=== TEST COMPLETED SUCCESSFULLY ===")
    print("The X Financial Analyzer is working with real Twitter data!")
    print("\nYou can now run:")
    print("  py main.py                 # Full analysis")
    print("  streamlit run dashboard.py # Web dashboard")

    return True

if __name__ == "__main__":
    test_app()