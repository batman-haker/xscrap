#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper import DataCollector
from src.analyzer import DataProcessor
import json

def test_updated_app():
    print("=== Testing Updated Application ===")
    print("Testing with @MarekLangalis data...")

    # Initialize collector
    try:
        collector = DataCollector()
        print("✓ DataCollector initialized")
    except Exception as e:
        print(f"✗ DataCollector error: {e}")
        return False

    # Test data collection for MarekLangalis only
    print("\n1. Testing data collection...")
    try:
        # Collect just from MarekLangalis (should be fast with rate limiting)
        tweets_data = collector.collect_all_tweets(hours_back=24)

        total_tweets = sum(len(tweets) for tweets in tweets_data.values())
        print(f"✓ Collected {total_tweets} tweets total")

        # Show details
        for category, tweets in tweets_data.items():
            if tweets:
                print(f"  - {category}: {len(tweets)} tweets")

                # Show first tweet details
                if tweets:
                    first_tweet = tweets[0]
                    print(f"    Latest: {first_tweet['text'][:100]}...")
                    print(f"    User: @{first_tweet['user']['screen_name']}")
                    print(f"    Date: {first_tweet['created_at']}")

    except Exception as e:
        print(f"✗ Data collection error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Save raw data
    print("\n2. Saving raw data...")
    try:
        filename = collector.save_raw_data(tweets_data)
        if filename:
            print(f"✓ Raw data saved: {filename}")
        else:
            print("✗ Failed to save raw data")
            return False
    except Exception as e:
        print(f"✗ Save error: {e}")
        return False

    # Test data processing
    print("\n3. Testing data processing...")
    try:
        processor = DataProcessor()
        processed_data = processor.process_tweets(tweets_data)

        print(f"✓ Processed {processed_data.get('total_tweets', 0)} tweets")
        print(f"✓ Overall sentiment: {processed_data.get('overall_sentiment', {}).get('sentiment_label', 'Unknown')}")

        # Show category analysis
        categories = processed_data.get('categories', {})
        for category, data in categories.items():
            if data.get('tweet_count', 0) > 0:
                print(f"  - {category}: {data.get('sentiment_label', 'Unknown')} ({data.get('weighted_sentiment', 0):.2f})")

    except Exception as e:
        print(f"✗ Processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Save processed data
    print("\n4. Saving processed data...")
    try:
        processed_filename = processor.save_processed_data(processed_data)
        if processed_filename:
            print(f"✓ Processed data saved: {processed_filename}")
        else:
            print("✗ Failed to save processed data")
            return False
    except Exception as e:
        print(f"✗ Save processed error: {e}")
        return False

    print("\n=== TEST SUCCESSFUL ===")
    print("Application is working with real Twitter data!")
    print(f"Raw data: {filename}")
    print(f"Processed data: {processed_filename}")

    return True

if __name__ == "__main__":
    success = test_updated_app()

    if success:
        print("\n🎉 SUCCESS! Your X Financial Analyzer is ready!")
        print("\nNext steps:")
        print("1. Run: py main.py                 # For full analysis")
        print("2. Run: streamlit run dashboard.py # For web interface")
    else:
        print("\n❌ Test failed. Check errors above.")