#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
import re
from dotenv import load_dotenv

load_dotenv()

def parse_accounts_from_file():
    """Parse accounts from lista kont.txt"""
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
            print(f"Przetwarzanie linii: {line[:100]}")
            if ':' in line:
                category_part, urls_part = line.split(':', 1)
                category_name = category_part.strip()

                # Extract usernames from URLs - better regex
                urls = re.findall(r'https://x\.com/([a-zA-Z0-9_]+)', urls_part)
                print(f"Znalezione URLs: {urls}")

                if 'Giełda' in line or category_name.startswith('1'):
                    accounts['Giełda'] = urls
                elif 'Kryptowaluty' in line or category_name.startswith('2'):
                    accounts['Kryptowaluty'] = urls
                elif 'Gospodarka' in line or category_name.startswith('3'):
                    accounts['Gospodarka'] = urls
                elif 'Polityka' in line or category_name.startswith('4'):
                    accounts['Polityka'] = urls
                elif 'Nowinki AI' in line or category_name.startswith('5'):
                    accounts['Nowinki AI'] = urls
                elif 'Filozofia' in line or category_name.startswith('6'):
                    accounts['Filozofia'] = urls

    except Exception as e:
        print(f"Błąd odczytu pliku: {e}")

    return accounts

def get_latest_tweet(username):
    """Get latest tweet from user using twitterapi.io"""
    api_key = os.getenv('TWITTERAPI_IO_KEY')
    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

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
                    return {
                        'username': username,
                        'text': tweet.get('text', ''),
                        'created_at': tweet.get('createdAt', ''),
                        'like_count': tweet.get('likeCount', 0),
                        'retweet_count': tweet.get('retweetCount', 0),
                        'reply_count': tweet.get('replyCount', 0),
                        'view_count': tweet.get('viewCount', 0),
                        'user_name': tweet.get('user', {}).get('name', username)
                    }
            else:
                print(f"@{username}: {data.get('msg', 'Błąd API')}")
        elif response.status_code == 429:
            print(f"@{username}: Rate limit")
        elif response.status_code == 402:
            print(f"@{username}: Brak kredytów")
        else:
            print(f"@{username}: HTTP {response.status_code}")

    except Exception as e:
        print(f"@{username}: Błąd - {e}")

    return None

def collect_all_tweets():
    """Collect latest tweets from all categorized accounts"""
    print("=== POBIERANIE NAJNOWSZYCH TWEETÓW ===\n")

    accounts = parse_accounts_from_file()
    all_tweets = {}

    for category, usernames in accounts.items():
        print(f"\n{category.upper()} ({len(usernames)} kont):")
        category_tweets = []

        for username in usernames:
            print(f"  Pobieranie @{username}...")
            tweet = get_latest_tweet(username)

            if tweet:
                category_tweets.append(tweet)
                print(f"    OK Pobrano: {tweet['text'][:50]}...")
            else:
                print(f"    BRAK danych")

            time.sleep(5.5)  # Rate limit dla twitterapi.io

        all_tweets[category] = category_tweets
        print(f"  Razem: {len(category_tweets)}/{len(usernames)} tweetów")

    # Zapisz do pliku
    output_file = 'data/raw/categorized_tweets.json'
    os.makedirs('data/raw', exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_tweets, f, indent=2, ensure_ascii=False)

    print(f"\nOK Dane zapisane do: {output_file}")

    # Statystyki
    total_tweets = sum(len(tweets) for tweets in all_tweets.values())
    print(f"\nPODSUMOWANIE:")
    print(f"Pobrano {total_tweets} tweetów z {sum(len(accounts[cat]) for cat in accounts)} kont")

    for category, tweets in all_tweets.items():
        if tweets:
            print(f"  {category}: {len(tweets)} tweetów")

    return all_tweets

if __name__ == "__main__":
    # Pokaż parsed accounts
    accounts = parse_accounts_from_file()
    print("Znalezione konta:")
    for category, usernames in accounts.items():
        print(f"{category}: {len(usernames)} kont - {usernames}")

    print("\nCzy rozpocząć pobieranie? (y/n): ", end="")

    # Auto start for testing
    print("y")
    collect_all_tweets()