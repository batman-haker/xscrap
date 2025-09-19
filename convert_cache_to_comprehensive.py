#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
from tweet_cache_manager import TweetCacheManager

def parse_accounts_from_file():
    """Parse all accounts from lista kont.txt"""
    accounts = {
        'Giełda': [],
        'Kryptowaluty': [],
        'Gospodarka': [],
        'Polityka': [],
        'Nowinki AI': [],
        'Filozofia': []
    }

    try:
        with open('C:\\Xscrap\\lista kont.txt', 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.strip().split('\n')
        import re

        for line in lines:
            if ':' in line:
                category_part, urls_part = line.split(':', 1)

                # Extract usernames from URLs
                urls = re.findall(r'https://x\.com/([a-zA-Z0-9_]+)', urls_part)

                if 'Giełda' in line or category_part.startswith('1'):
                    accounts['Giełda'] = urls
                elif 'Kryptowaluty' in line or category_part.startswith('2'):
                    accounts['Kryptowaluty'] = urls
                elif 'Gospodarka' in line or category_part.startswith('3'):
                    accounts['Gospodarka'] = urls
                elif 'Polityka' in line or category_part.startswith('4'):
                    accounts['Polityka'] = urls
                elif 'Nowinki AI' in line or category_part.startswith('5'):
                    accounts['Nowinki AI'] = urls
                elif 'Filozofia' in line or category_part.startswith('6'):
                    accounts['Filozofia'] = urls

    except Exception as e:
        print(f"Error reading file: {e}")

    return accounts

def convert_cache_to_comprehensive():
    """Convert cache data to comprehensive format"""
    print("=== CONVERTING CACHE TO COMPREHENSIVE FORMAT ===")

    cache = TweetCacheManager()
    accounts_by_category = parse_accounts_from_file()

    # Get cached data organized by category
    comprehensive_data = {}
    total_tweets = 0
    total_accounts = 0

    for category, usernames in accounts_by_category.items():
        category_tweets = []

        for username in usernames:
            cache_data = cache.load_user_cache(username)
            user_tweets = cache_data.get("tweets", [])

            if user_tweets:
                # Take up to 20 most recent tweets
                recent_tweets = user_tweets[:20]
                category_tweets.extend(recent_tweets)
                total_accounts += 1
                print(f"[LOADED] @{username}: {len(recent_tweets)} tweets")

        if category_tweets:
            comprehensive_data[category] = category_tweets
            total_tweets += len(category_tweets)
            print(f"[CATEGORY] {category}: {len(category_tweets)} tweets from {len([u for u in usernames if cache.load_user_cache(u).get('tweets')])} accounts")

    # Create comprehensive format
    save_data = {
        'timestamp': datetime.now().isoformat(),
        'collection_summary': {
            'total_accounts': total_accounts,
            'total_tweets': total_tweets,
            'new_api_calls': 0,  # From cache
            'categories': len([cat for cat, tweets in comprehensive_data.items() if tweets]),
            'tweets_per_category': {cat: len(tweets) for cat, tweets in comprehensive_data.items()},
            'cache_conversion': True
        },
        'tweets_by_category': comprehensive_data
    }

    # Save to current file
    output_file = 'data/raw/comprehensive_tweets_current.json'
    os.makedirs('data/raw', exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Comprehensive data created!")
    print(f"[STATS] {total_tweets} tweets from {total_accounts} accounts")
    print(f"[SAVED] {output_file}")

    return save_data

if __name__ == "__main__":
    result = convert_cache_to_comprehensive()
    if result:
        print(f"\n[READY] Data ready for Claude analysis!")
        for category, tweets in result['tweets_by_category'].items():
            if tweets:
                accounts = len(set(tweet['username'] for tweet in tweets))
                print(f"  {category}: {len(tweets)} tweets from {accounts} accounts")