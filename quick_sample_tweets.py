#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
import re
from dotenv import load_dotenv

load_dotenv()

def parse_all_accounts():
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
        print(f"Błąd odczytu pliku: {e}")

    return accounts

def get_comprehensive_tweets():
    """Get 10 tweets from ALL accounts across categories"""

    all_accounts = parse_all_accounts()

    api_key = os.getenv('TWITTERAPI_IO_KEY')
    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

    all_tweets = {}

    for category, usernames in sample_accounts.items():
        print(f"\n{category}:")
        category_tweets = []

        for username in usernames:
            print(f"  @{username}...")

            tweets_url = f"{base_url}/twitter/user/last_tweets"
            params = {'userName': username}

            try:
                response = requests.get(tweets_url, headers=headers, params=params, timeout=15)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        tweets = data.get('data', {}).get('tweets', [])
                        if tweets:
                            tweet = tweets[0]
                            tweet_data = {
                                'username': username,
                                'text': tweet.get('text', '')[:200],  # Limit text
                                'created_at': tweet.get('createdAt', ''),
                                'like_count': tweet.get('likeCount', 0),
                                'retweet_count': tweet.get('retweetCount', 0),
                                'reply_count': tweet.get('replyCount', 0),
                                'user_name': tweet.get('user', {}).get('name', username)
                            }
                            category_tweets.append(tweet_data)
                            print(f"    OK")
                        else:
                            print(f"    No tweets")
                    else:
                        print(f"    Error: {data.get('msg', 'Unknown')}")
                else:
                    print(f"    HTTP {response.status_code}")

            except Exception as e:
                print(f"    Error: {e}")

            time.sleep(5.5)  # Rate limit

        all_tweets[category] = category_tweets

    # Save to file
    output_file = 'data/raw/sample_categorized_tweets.json'
    os.makedirs('data/raw', exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_tweets, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: {output_file}")

    total = sum(len(tweets) for tweets in all_tweets.values())
    print(f"Total tweets: {total}")

    return all_tweets

if __name__ == "__main__":
    get_sample_tweets()