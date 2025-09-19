#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
import re
from datetime import datetime
from dotenv import load_dotenv
from tweet_cache_manager import TweetCacheManager

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

def get_user_tweets(api_key, username, max_tweets=10):
    """Get up to 10 tweets from a specific user"""
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

                # Process tweets and limit to max_tweets
                processed_tweets = []
                for i, tweet in enumerate(tweets[:max_tweets]):
                    processed_tweet = {
                        'username': username,
                        'text': tweet.get('text', ''),  # Full text length
                        'created_at': tweet.get('createdAt', ''),
                        'like_count': tweet.get('likeCount', 0),
                        'retweet_count': tweet.get('retweetCount', 0),
                        'reply_count': tweet.get('replyCount', 0),
                        'view_count': tweet.get('viewCount', 0),
                        'user_name': tweet.get('user', {}).get('name', username),
                        'tweet_index': i + 1
                    }
                    processed_tweets.append(processed_tweet)

                return processed_tweets
            else:
                print(f"  API Error: {data.get('msg', 'Unknown')}")
                return []
        else:
            print(f"  HTTP {response.status_code}")
            return []

    except Exception as e:
        print(f"  Error: {e}")
        return []

def collect_comprehensive_tweets(force_refresh=False, max_age_hours=6):
    """Intelligent tweet collection with caching and deduplication"""

    print("=== INTELIGENTNE POBIERANIE TWEETÓW Z CACHE ===\n")

    # Initialize cache manager
    cache = TweetCacheManager()
    all_accounts = parse_all_accounts()
    api_key = os.getenv('TWITTERAPI_IO_KEY')

    if not api_key:
        print("BŁĄD: Brak klucza API. Sprawdź plik .env")
        return None

    # First, check what we have in cache
    cached_data, cache_stats = cache.get_cached_tweets_by_category(all_accounts, max_age_hours)

    print(f"[CACHE] Status: {cache_stats['total_cached']} fresh tweets w cache")
    print(f"[INFO] {cache_stats['cache_hits']} uzytkownikow z aktualnymi danymi")

    comprehensive_data = cached_data.copy()
    total_tweets_collected = cache_stats['total_cached']
    new_api_calls = 0
    processed_accounts = 0

    total_accounts = sum(len(accounts) for accounts in all_accounts.values())
    print(f"\n[CHECK] Sprawdzam {total_accounts} kont pod katem potrzeby odswiezenia...")

    if not force_refresh:
        # Smart refresh - only fetch users that need fresh data
        users_to_refresh = []
        for category, usernames in all_accounts.items():
            for username in usernames:
                if cache.needs_fresh_data(username, max_age_hours):
                    users_to_refresh.append((category, username))

        print(f"[REFRESH] {len(users_to_refresh)} kont wymaga odswiezenia danych")
    else:
        print("[FORCE] Wymuszam pelne odswiezenie wszystkich kont")
        users_to_refresh = [(cat, user) for cat, users in all_accounts.items() for user in users]

    if not users_to_refresh:
        print("[OK] Wszystkie dane sa aktualne! Uzywam cache.")
    else:
        print(f"\n[API] Pobieram swieze dane dla {len(users_to_refresh)} kont...")

        for i, (category, username) in enumerate(users_to_refresh, 1):
            processed_accounts += 1
            progress = (processed_accounts / len(users_to_refresh)) * 100
            print(f"  [{processed_accounts:2d}/{len(users_to_refresh)}] ({progress:5.1f}%) @{username}... ", end="")

            new_tweets = get_user_tweets(api_key, username, max_tweets=20)
            new_api_calls += 1

            if new_tweets:
                # Merge with cache and get statistics
                merged_tweets, new_count = cache.merge_new_tweets(username, new_tweets)

                # Update comprehensive data for this category
                if category not in comprehensive_data:
                    comprehensive_data[category] = []

                # Replace old data for this user with fresh merged data
                comprehensive_data[category] = [
                    tweet for tweet in comprehensive_data[category]
                    if tweet.get('username') != username
                ]
                comprehensive_data[category].extend(merged_tweets[:20])  # Max 20 per user

                total_tweets_collected += new_count
                print(f"[+{new_count}] nowych")
            else:
                print("[SKIP] brak")

            # Rate limiting - 5 seconds between requests
            if processed_accounts < len(users_to_refresh):
                time.sleep(5.5)

    for category, usernames in all_accounts.items():
        if not usernames:
            continue

        print(f"\n{category.upper()} ({len(usernames)} kont):")
        category_tweets = []

        for username in usernames:
            processed_accounts += 1
            progress = (processed_accounts / total_accounts) * 100

            print(f"  [{processed_accounts:2d}/{total_accounts}] @{username}... ", end="")

            tweets = get_user_tweets(api_key, username, max_tweets=10)

            if tweets:
                category_tweets.extend(tweets)
                total_tweets_collected += len(tweets)
                print(f"OK ({len(tweets)} tweetów)")
            else:
                print("BRAK")

            # Rate limiting - 5 seconds between requests
            if processed_accounts < total_accounts:  # Don't wait after the last request
                time.sleep(5.5)

        comprehensive_data[category] = category_tweets

        print(f"  Razem w kategorii {category}: {len(category_tweets)} tweetów")

    # Save comprehensive data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'data/raw/comprehensive_tweets_{timestamp}.json'
    os.makedirs('data/raw', exist_ok=True)

    # Also save as current data
    current_file = 'data/raw/comprehensive_tweets_current.json'

    save_data = {
        'timestamp': datetime.now().isoformat(),
        'collection_summary': {
            'total_accounts': total_accounts,
            'total_tweets': total_tweets_collected,
            'new_api_calls': new_api_calls,
            'categories': len([cat for cat, tweets in comprehensive_data.items() if tweets]),
            'tweets_per_category': {cat: len(tweets) for cat, tweets in comprehensive_data.items()},
            'cache_stats': cache_stats
        },
        'tweets_by_category': comprehensive_data
    }

    # Save both files
    for file_path in [output_file, current_file]:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

    print(f"\n" + "="*60)
    print("PODSUMOWANIE POBIERANIA:")
    print("="*60)
    print(f"Przebadane konta: {total_accounts}")
    print(f"Pobrane tweety: {total_tweets_collected}")
    print(f"Średnio na konto: {total_tweets_collected/total_accounts:.1f}")
    print(f"Aktywne kategorie: {len([cat for cat, tweets in comprehensive_data.items() if tweets])}")
    print(f"\nDane zapisane do:")
    print(f"  - {output_file}")
    print(f"  - {current_file}")

    # Category breakdown
    print(f"\nRozkład według kategorii:")
    for category, tweets in comprehensive_data.items():
        if tweets:
            accounts_in_category = len(set(tweet['username'] for tweet in tweets))
            avg_per_account = len(tweets) / accounts_in_category if accounts_in_category > 0 else 0
            print(f"  {category}: {len(tweets)} tweetów z {accounts_in_category} kont (śr. {avg_per_account:.1f})")

    return save_data

def quick_refresh():
    """Quick refresh - only fetch very recent data (last 3 hours)"""
    print("[MODE] Quick refresh - last 3 hours, 20 tweets per account")
    return collect_comprehensive_tweets(force_refresh=False, max_age_hours=3)

def daily_refresh():
    """Daily refresh - standard 6-hour refresh cycle"""
    print("[MODE] Daily refresh - last 6 hours, 20 tweets per account")
    return collect_comprehensive_tweets(force_refresh=False, max_age_hours=6)

def force_full_refresh():
    """Force complete refresh of all accounts"""
    print("[MODE] Full refresh - 20 tweets per account from all users")
    return collect_comprehensive_tweets(force_refresh=True, max_age_hours=0)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "quick":
            result = quick_refresh()
        elif mode == "force":
            result = force_full_refresh()
        else:
            result = daily_refresh()
    else:
        result = daily_refresh()

    if result:
        total = result['collection_summary']['total_tweets']
        accounts = result['collection_summary']['total_accounts']
        api_calls = result['collection_summary'].get('new_api_calls', 0)
        print(f"\n[SUCCESS] SUKCES!")
        print(f"[STATS] Tweets: {total} | Konta: {accounts} | API calls: {api_calls}")
        print("[READY] Dane gotowe do analizy przez Ray Dalio AI!")
    else:
        print("\n[ERROR] NIEPOWODZENIE")

    # Display usage info
    print(f"\n[HELP] Uzycie:")
    print(f"   python {__file__} quick  # Szybkie odświeżenie (3h)")
    print(f"   python {__file__} daily  # Standardowe odświeżenie (6h)")
    print(f"   python {__file__} force  # Wymuś pełne odświeżenie")