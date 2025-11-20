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

def get_smolarek_tweets(count=50):
    """Pobiera ostatnie tweety z konta t_smolarek"""

    api_key = os.getenv('TWITTER_API_KEY')

    if not api_key:
        print("BŁĄD: Brak klucza API w pliku .env")
        return None

    print(f"=== POBIERANIE {count} TWEETÓW T_SMOLAREK ===\n")

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
                return None
        elif response.status_code == 429:
            print("   ✗ RATE LIMIT - poczekaj chwilę")
            return None
        else:
            print(f"   ✗ Błąd HTTP: {response.status_code}")
            return None

    except Exception as e:
        print(f"   ✗ Błąd: {e}")
        return None

    # Wait for rate limit
    print("   Czekam 6 sekund (rate limit)...")
    time.sleep(6)

    # Get tweets - API typically returns 20 tweets per request
    # We'll need to make multiple requests to get 50
    print(f"\n2. Pobieranie tweetów...")

    all_tweets = []
    cursor = None
    requests_made = 0
    max_requests = 3  # To get ~60 tweets (20 per request)

    tweets_url = f"{base_url}/twitter/user/last_tweets"

    while len(all_tweets) < count and requests_made < max_requests:
        params = {'userName': username}
        if cursor:
            params['cursor'] = cursor

        try:
            response = requests.get(tweets_url, headers=headers, params=params, timeout=15)
            requests_made += 1

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    tweet_data = data.get('data', {})
                    tweets = tweet_data.get('tweets', [])

                    if tweets:
                        all_tweets.extend(tweets)
                        print(f"   ✓ Pobrano {len(tweets)} tweetów (łącznie: {len(all_tweets)})")

                        # Check if there's a cursor for next page
                        cursor = tweet_data.get('cursor')

                        if not cursor or len(all_tweets) >= count:
                            break

                        # Wait before next request
                        if requests_made < max_requests:
                            print("   Czekam 6 sekund przed kolejnym zapytaniem...")
                            time.sleep(6)
                    else:
                        print("   ✗ Brak więcej tweetów")
                        break
                else:
                    print(f"   ✗ Błąd API: {data.get('msg', 'Nieznany błąd')}")
                    break
            elif response.status_code == 429:
                print("   ✗ RATE LIMIT")
                break
            else:
                print(f"   ✗ Błąd HTTP: {response.status_code}")
                break

        except Exception as e:
            print(f"   ✗ Błąd: {e}")
            break

    # Trim to exactly the requested count
    all_tweets = all_tweets[:count]

    if all_tweets:
        print(f"\n   ✓ KOŃCOWO POBRANO: {len(all_tweets)} tweetów\n")

        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/raw/smolarek_all_tweets_{timestamp}.json"

        os.makedirs('data/raw', exist_ok=True)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'username': username,
                'fetched_at': timestamp,
                'total_tweets': len(all_tweets),
                'tweets': all_tweets
            }, f, indent=2, ensure_ascii=False)

        print(f"✓ Zapisano do pliku: {filename}")

        # Display summary
        print("\n" + "="*80)
        print("PODSUMOWANIE TEMATÓW:")
        print("="*80)

        # Count mentions of key topics
        topics = {
            'NVIDIA': 0,
            'ASML': 0,
            'TSMC': 0,
            'Chiny': 0,
            'AI': 0,
            'półprzewodniki/chipy': 0,
            'USA': 0,
            'Europa/UE': 0,
            'geopolityka': 0
        }

        for tweet in all_tweets:
            text = tweet.get('text', '').lower()

            if 'nvidia' in text or '$nvda' in text:
                topics['NVIDIA'] += 1
            if 'asml' in text:
                topics['ASML'] += 1
            if 'tsmc' in text or '$tsm' in text:
                topics['TSMC'] += 1
            if 'chin' in text or '🇨🇳' in text:
                topics['Chiny'] += 1
            if ' ai ' in text or 'ai,' in text or 'ai.' in text or 'ai!' in text:
                topics['AI'] += 1
            if 'chip' in text or 'półprzewodnik' in text or 'semiconductor' in text:
                topics['półprzewodniki/chipy'] += 1
            if 'usa' in text or '🇺🇸' in text or 'ameryk' in text:
                topics['USA'] += 1
            if 'europ' in text or '🇪🇺' in text or 'ue ' in text or 'unii' in text:
                topics['Europa/UE'] += 1
            if 'geopolit' in text or 'handel' in text or 'restrykcj' in text or 'sankcj' in text:
                topics['geopolityka'] += 1

        for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f"  {topic}: {count} tweetów")

        return filename
    else:
        print("   ✗ Nie udało się pobrać tweetów")
        return None

if __name__ == "__main__":
    get_smolarek_tweets(50)
