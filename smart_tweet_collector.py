#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Tweet Collector - Automatyczne pobieranie z respektowaniem rate limitów
Czeka 15 minut między requestami do Twitter API v2
"""
import requests
import json
import time
import os
from datetime import datetime
import sys

# Konfiguracja
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAAEK4QEAAAAAViLvNU%2FIgR%2FwwQOy2wy63iRey08%3DgTgI2xoNKbKd9lNMN2vFRpM8cJAqiW2eAzdu9eWG472mb1xpSv"
OUTPUT_DIR = "data/cache"
RATE_LIMIT_WAIT = 900  # 15 minut = 900 sekund

class SmartTweetCollector:
    def __init__(self):
        self.bearer_token = BEARER_TOKEN
        self.output_dir = OUTPUT_DIR
        self.last_request_time = 0

        # Upewnij się że katalog istnieje
        os.makedirs(self.output_dir, exist_ok=True)

    def wait_for_rate_limit(self):
        """Czeka jeśli minęło mniej niż 15 minut od ostatniego requesta"""
        time_since_last = time.time() - self.last_request_time

        if time_since_last < RATE_LIMIT_WAIT and self.last_request_time > 0:
            wait_time = RATE_LIMIT_WAIT - time_since_last
            minutes = int(wait_time / 60)
            seconds = int(wait_time % 60)

            print(f"\n[RATE LIMIT] Czekam {minutes}m {seconds}s do nastepnego requesta...")
            print(f"[INFO] Ostatni request byl {int(time_since_last)}s temu")

            # Countdown
            for remaining in range(int(wait_time), 0, -30):
                mins = remaining // 60
                secs = remaining % 60
                print(f"  Pozostalo: {mins}m {secs}s...", end='\r')
                time.sleep(min(30, remaining))

            print("\n[OK] Rate limit OK, kontynuuje...")

    def get_user_id(self, username):
        """Pobiera user_id na podstawie username"""
        print(f"\n[1/3] Pobieram user_id dla @{username}...")

        url = f"https://api.twitter.com/2/users/by/username/{username}"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        try:
            response = requests.get(url, headers=headers, verify=False)

            if response.status_code == 200:
                data = response.json()
                user_id = data['data']['id']
                user_name = data['data']['name']
                print(f"[OK] Znaleziono: {user_name} (ID: {user_id})")
                return user_id
            else:
                print(f"[ERROR] Status {response.status_code}: {response.text}")
                return None

        except Exception as e:
            print(f"[ERROR] Wyjatek: {e}")
            return None

    def fetch_tweets(self, username, count=10):
        """Pobiera tweety od danego użytkownika"""

        # Czekaj na rate limit
        self.wait_for_rate_limit()

        # Pobierz user_id
        user_id = self.get_user_id(username)
        if not user_id:
            return None

        # Pobierz tweety
        print(f"\n[2/3] Pobieram {count} tweetow od @{username}...")

        url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        params = {
            "max_results": min(count, 100),  # API max = 100
            "tweet.fields": "created_at,public_metrics,text,author_id,conversation_id,entities,lang,possibly_sensitive,referenced_tweets,reply_settings",
            "exclude": "retweets,replies"
        }

        try:
            response = requests.get(url, headers=headers, params=params, verify=False)
            self.last_request_time = time.time()

            if response.status_code == 200:
                data = response.json()
                tweets = data.get('data', [])
                print(f"[OK] Pobrano {len(tweets)} tweetow")
                return {
                    'username': username,
                    'user_id': user_id,
                    'tweets': tweets,
                    'meta': data.get('meta', {}),
                    'collected_at': datetime.now().isoformat()
                }

            elif response.status_code == 429:
                print(f"[RATE LIMIT] Hit! Czekam 15 minut...")
                time.sleep(RATE_LIMIT_WAIT)
                return self.fetch_tweets(username, count)  # Retry

            else:
                print(f"[ERROR] Status {response.status_code}: {response.text}")
                return None

        except Exception as e:
            print(f"[ERROR] Wyjatek: {e}")
            return None

    def save_tweets(self, data, username):
        """Zapisuje tweety do pliku JSON"""
        if not data:
            print("[ERROR] Brak danych do zapisania")
            return None

        print(f"\n[3/3] Zapisuje tweety do pliku...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{username}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)

        # Format dla LLM
        formatted_data = {
            "meta": {
                "username": data['username'],
                "user_id": data['user_id'],
                "total_tweets": len(data['tweets']),
                "collected_at": data['collected_at'],
                "query_params": {
                    "exclude": "retweets, replies",
                    "original_posts_only": True
                }
            },
            "tweets": data['tweets']
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=2)

            print(f"[OK] Zapisano: {filepath}")
            print(f"[OK] Rozmiar: {os.path.getsize(filepath)} bajtow")
            return filepath

        except Exception as e:
            print(f"[ERROR] Zapis nie powiodl sie: {e}")
            return None

    def collect_from_multiple_authors(self, authors, tweets_per_author=10):
        """Pobiera tweety od wielu autorów z automatycznym czekaniem"""
        print("="*60)
        print("SMART TWEET COLLECTOR")
        print("="*60)
        print(f"Autorow do pobrania: {len(authors)}")
        print(f"Tweetow na autora: {tweets_per_author}")
        print(f"Laczny czas (przyblizony): {len(authors) * 15} minut")
        print("="*60)

        results = []

        for idx, author in enumerate(authors, 1):
            print(f"\n>>> AUTOR {idx}/{len(authors)}: @{author}")

            # Pobierz tweety
            data = self.fetch_tweets(author, tweets_per_author)

            if data:
                # Zapisz
                filepath = self.save_tweets(data, author)

                if filepath:
                    results.append({
                        'username': author,
                        'file': filepath,
                        'tweets_count': len(data['tweets']),
                        'status': 'success'
                    })
                else:
                    results.append({
                        'username': author,
                        'status': 'save_failed'
                    })
            else:
                results.append({
                    'username': author,
                    'status': 'fetch_failed'
                })

            # Info o następnym autorze
            if idx < len(authors):
                print(f"\n[KOLEJNY] Za 15 minut: @{authors[idx]}")

        # Podsumowanie
        print("\n" + "="*60)
        print("PODSUMOWANIE")
        print("="*60)

        success = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] != 'success']

        print(f"Sukces: {len(success)}/{len(authors)}")

        for r in success:
            print(f"  [OK] @{r['username']} - {r['tweets_count']} tweetow -> {r['file']}")

        if failed:
            print(f"\nNie udalo sie: {len(failed)}")
            for r in failed:
                print(f"  [FAIL] @{r['username']} - {r['status']}")

        return results

def main():
    """Główna funkcja - przykłady użycia"""

    # Wyłącz SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    collector = SmartTweetCollector()

    # Sprawdź argumenty
    if len(sys.argv) < 2:
        print("UZYCIE:")
        print("  Jeden autor:")
        print("    py smart_tweet_collector.py kot_b0t")
        print("    py smart_tweet_collector.py kot_b0t 50")
        print("")
        print("  Wielu autorow:")
        print("    py smart_tweet_collector.py kot_b0t,elonmusk,naval")
        print("    py smart_tweet_collector.py kot_b0t,elonmusk 20")
        return

    # Parse argumenty
    authors_arg = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    # Lista autorów (rozdzielona przecinkami)
    authors = [a.strip() for a in authors_arg.split(',')]

    if len(authors) == 1:
        # Jeden autor
        print(f"Pobieram {count} tweetow od @{authors[0]}...")
        data = collector.fetch_tweets(authors[0], count)
        if data:
            collector.save_tweets(data, authors[0])
    else:
        # Wielu autorów
        collector.collect_from_multiple_authors(authors, count)

if __name__ == "__main__":
    main()
