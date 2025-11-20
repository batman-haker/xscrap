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

def get_smolarek_chip_tweets():
    """Pobiera ostatnie 10 tweetów z konta T_Smolarek związanych z chipami"""

    api_key = os.getenv('TWITTER_API_KEY')

    if not api_key:
        print("BŁĄD: Brak klucza API w pliku .env")
        return

    print("=== POBIERANIE TWEETÓW T_SMOLAREK - TEMATYKA CHIPY ===\n")

    username = "t_smolarek"

    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

    # Get user info first
    print(f"1. Sprawdzanie konta @{username}...")
    user_url = f"{base_url}/twitter/user/info"
    params = {'userName': username}

    try:
        response = requests.get(user_url, headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                user_data = data.get('data', {})
                print(f"   ✓ Znaleziono: {user_data.get('name', 'N/A')}")
                followers = user_data.get('followersCount', 0)
                print(f"   Obserwujący: {followers:,}" if isinstance(followers, int) else f"   Obserwujący: {followers}")
            else:
                print(f"   ✗ Błąd API: {data.get('msg', 'Nieznany błąd')}")
                return
        elif response.status_code == 429:
            print("   ✗ RATE LIMIT - poczekaj chwilę")
            return
        else:
            print(f"   ✗ Błąd HTTP: {response.status_code}")
            return

    except Exception as e:
        print(f"   ✗ Błąd: {e}")
        return

    # Wait for rate limit
    print("   Czekam 6 sekund (rate limit)...")
    time.sleep(6)

    # Get tweets
    print(f"\n2. Pobieranie tweetów...")
    tweets_url = f"{base_url}/twitter/user/last_tweets"
    params = {'userName': username}

    try:
        response = requests.get(tweets_url, headers=headers, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                all_tweets = data.get('data', {}).get('tweets', [])
                print(f"   ✓ Pobrano {len(all_tweets)} tweetów\n")

                # Filter tweets about chips
                chip_keywords = [
                    'chip', 'chips', 'semiconductor', 'semiconductors',
                    'tsmc', 'nvidia', 'amd', 'intel', 'qualcomm',
                    'asml', 'półprzewodnik', 'półprzewodniki',
                    'procesor', 'procesory', 'gpu', 'cpu',
                    'ai chip', 'chipmaker', 'foundry', 'fab'
                ]

                chip_tweets = []
                for tweet in all_tweets:
                    text = tweet.get('text', '').lower()
                    if any(keyword in text for keyword in chip_keywords):
                        chip_tweets.append(tweet)

                print(f"   ✓ Znaleziono {len(chip_tweets)} tweetów o chipach\n")

                # Display up to 10 chip-related tweets
                display_tweets = chip_tweets[:10]

                if display_tweets:
                    print("="*80)
                    print(f"TWEETY O CHIPACH (@{username})")
                    print("="*80)

                    for i, tweet in enumerate(display_tweets, 1):
                        print(f"\n[{i}] {tweet.get('createdAt', 'N/A')}")
                        print("-"*80)

                        likes = tweet.get('likeCount', 0)
                        retweets = tweet.get('retweetCount', 0)
                        replies = tweet.get('replyCount', 0)
                        views = tweet.get('viewCount', 0)

                        print(f"👁️  Wyświetlenia: {views:,}" if isinstance(views, int) else f"👁️  Wyświetlenia: {views}")
                        print(f"❤️  Polubienia: {likes:,}" if isinstance(likes, int) else f"❤️  Polubienia: {likes}")
                        print(f"🔄 Retweety: {retweets:,}" if isinstance(retweets, int) else f"🔄 Retweety: {retweets}")
                        print(f"💬 Odpowiedzi: {replies:,}" if isinstance(replies, int) else f"💬 Odpowiedzi: {replies}")

                        print(f"\nTreść:")
                        print(tweet.get('text', 'N/A'))

                        if tweet.get('url'):
                            print(f"\n🔗 Link: {tweet.get('url')}")

                        print("-"*80)

                    # Save to file
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"data/raw/smolarek_chips_{timestamp}.json"

                    os.makedirs('data/raw', exist_ok=True)

                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump({
                            'username': username,
                            'fetched_at': timestamp,
                            'total_tweets': len(all_tweets),
                            'chip_tweets_count': len(chip_tweets),
                            'chip_tweets': display_tweets,
                            'keywords_used': chip_keywords
                        }, f, indent=2, ensure_ascii=False)

                    print(f"\n✓ Zapisano do pliku: {filename}")

                else:
                    print("   ✗ Nie znaleziono tweetów o chipach w ostatnich postach")
                    print("\n   Pokazuję ostatnie 10 tweetów bez filtra:\n")

                    for i, tweet in enumerate(all_tweets[:10], 1):
                        print(f"\n[{i}] {tweet.get('createdAt', 'N/A')}")
                        print(tweet.get('text', 'N/A')[:200])
                        print("-"*80)

            else:
                print(f"   ✗ Błąd API: {data.get('msg', 'Nieznany błąd')}")
        elif response.status_code == 429:
            print("   ✗ RATE LIMIT")
        else:
            print(f"   ✗ Błąd HTTP: {response.status_code}")

    except Exception as e:
        print(f"   ✗ Błąd: {e}")

if __name__ == "__main__":
    get_smolarek_chip_tweets()
