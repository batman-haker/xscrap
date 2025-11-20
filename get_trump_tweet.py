#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def get_latest_trump_tweet():
    """Pobiera ostatni tweet Donalda Trumpa"""

    api_key = os.getenv('TWITTER_API_KEY')

    if not api_key:
        print("BŁĄD: Brak klucza API w pliku .env")
        return

    print("=== POBIERANIE OSTATNIEGO TWEETA DONALDA TRUMPA ===\n")

    # Donald Trump's username
    username = "realDonaldTrump"

    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

    # First, get user info
    print(f"1. Sprawdzanie informacji o koncie @{username}...")
    user_url = f"{base_url}/twitter/user/info"
    params = {'userName': username}

    try:
        response = requests.get(user_url, headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                user_data = data.get('data', {})
                print(f"   ✓ Znaleziono konto: {user_data.get('name', 'N/A')}")
                followers = user_data.get('followersCount', 0)
                print(f"   Obserwujący: {followers:,}" if isinstance(followers, int) else f"   Obserwujący: {followers}")
                print(f"   User ID: {user_data.get('userId', 'N/A')}")
            else:
                print(f"   ✗ Błąd API: {data.get('msg', 'Nieznany błąd')}")
                return
        elif response.status_code == 429:
            print("   ✗ RATE LIMIT - poczekaj chwilę")
            return
        elif response.status_code == 402:
            print("   ✗ BRAK KREDYTÓW na koncie API")
            return
        else:
            print(f"   ✗ Błąd HTTP: {response.status_code}")
            print(f"   Odpowiedź: {response.text}")
            return

    except Exception as e:
        print(f"   ✗ Błąd: {e}")
        return

    # Wait to avoid rate limit
    print("   Czekam 6 sekund (rate limit)...")
    time.sleep(6)

    # Now get latest tweets
    print(f"\n2. Pobieranie ostatnich tweetów...")
    tweets_url = f"{base_url}/twitter/user/last_tweets"
    params = {'userName': username}

    try:
        response = requests.get(tweets_url, headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                tweets = data.get('data', {}).get('tweets', [])

                if tweets:
                    print(f"   ✓ Pobrano {len(tweets)} tweetów\n")

                    # Display the latest tweet
                    latest_tweet = tweets[0]
                    print("="*80)
                    print("NAJNOWSZY TWEET:")
                    print("="*80)
                    print(f"Autor: {latest_tweet.get('userName', 'N/A')}")
                    print(f"Data: {latest_tweet.get('createdAt', 'N/A')}")

                    likes = latest_tweet.get('likeCount', 0)
                    retweets = latest_tweet.get('retweetCount', 0)
                    replies = latest_tweet.get('replyCount', 0)

                    print(f"Polubienia: {likes:,}" if isinstance(likes, int) else f"Polubienia: {likes}")
                    print(f"Retweety: {retweets:,}" if isinstance(retweets, int) else f"Retweety: {retweets}")
                    print(f"Odpowiedzi: {replies:,}" if isinstance(replies, int) else f"Odpowiedzi: {replies}")
                    print("\nTreść:")
                    print("-"*80)
                    print(latest_tweet.get('text', 'N/A'))
                    print("="*80)

                    # Save to file
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"data/raw/trump_tweet_{timestamp}.json"

                    os.makedirs('data/raw', exist_ok=True)

                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump({
                            'username': username,
                            'fetched_at': timestamp,
                            'latest_tweet': latest_tweet,
                            'all_tweets': tweets
                        }, f, indent=2, ensure_ascii=False)

                    print(f"\n✓ Zapisano do pliku: {filename}")

                else:
                    print("   ✗ Nie znaleziono żadnych tweetów")
            else:
                print(f"   ✗ Błąd API: {data.get('msg', 'Nieznany błąd')}")
        elif response.status_code == 429:
            print("   ✗ RATE LIMIT")
        elif response.status_code == 402:
            print("   ✗ BRAK KREDYTÓW")
        else:
            print(f"   ✗ Błąd HTTP: {response.status_code}")
            print(f"   Odpowiedź: {response.text}")

    except Exception as e:
        print(f"   ✗ Błąd: {e}")

if __name__ == "__main__":
    get_latest_trump_tweet()
