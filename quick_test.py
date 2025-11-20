#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper import TwitterAPIClient
import json

def quick_test():
    print("Quick test - getting @MarekLangalis tweet for dashboard")

    client = TwitterAPIClient()

    # Get just MarekLangalis
    tweets = client.get_user_tweets('MarekLangalis', count=1, since_hours=24)

    if tweets:
        tweet = tweets[0]
        print(f"SUCCESS: Got tweet")
        print(f"Text: {tweet['text'][:100]}...")
        print(f"Likes: {tweet['favorite_count']}")

        # Save to quick data for dashboard
        quick_data = {
            'polish_finance': tweets,
            'cryptocurrency': [],
            'us_economy': [],
            'geopolitics': [],
            'gold_commodities': []
        }

        with open('data/raw/quick_tweets.json', 'w', encoding='utf-8') as f:
            json.dump(quick_data, f, indent=2, ensure_ascii=False)

        print("Saved to data/raw/quick_tweets.json")
        return True
    else:
        print("No tweets retrieved")
        return False

if __name__ == "__main__":
    quick_test()