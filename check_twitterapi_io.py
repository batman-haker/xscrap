#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

def check_twitterapi_io_capabilities():
    api_key = os.getenv('TWITTER_API_KEY')

    print("=== SPRAWDZANIE FUNKCJI TWITTERAPI.IO ===\n")

    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

    test_username = "MarekLangalis"

    # Test 1: User info
    print("1. Informacje o uzytkowniku:")
    user_url = f"{base_url}/twitter/user/info"
    params = {'userName': test_username}

    try:
        response = requests.get(user_url, headers=headers, params=params, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("   OK DZIALA - mozna pobierac dane uzytkownika")
                user_data = data.get('data', {})
                print(f"   Followers: {user_data.get('followersCount', 'N/A')}")
                print(f"   Following: {user_data.get('followingCount', 'N/A')}")
            else:
                print(f"   BLAD API: {data.get('msg', 'Nieznany blad')}")
        elif response.status_code == 429:
            print("   RATE LIMIT - poczekaj 5 sekund")
        else:
            print(f"   BLAD HTTP: {response.status_code}")

    except Exception as e:
        print(f"   BLAD: {e}")

    time.sleep(6)  # Rate limit dla free tier

    # Test 2: User tweets
    print("\n2. Tweety uzytkownika:")
    tweets_url = f"{base_url}/twitter/user/last_tweets"
    params = {'userName': test_username}

    try:
        response = requests.get(tweets_url, headers=headers, params=params, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                tweets = data.get('data', {}).get('tweets', [])
                print(f"   OK DZIALA - pobrano {len(tweets)} tweetow")
            else:
                print(f"   BLAD API: {data.get('msg', 'Nieznany blad')}")
        elif response.status_code == 429:
            print("   RATE LIMIT - poczekaj 5 sekund")
        else:
            print(f"   BLAD HTTP: {response.status_code}")

    except Exception as e:
        print(f"   BLAD: {e}")

    time.sleep(6)

    # Test 3: Following list - KLUCZOWE!
    print("\n3. Lista obserwowanych (KLUCZOWE!):")
    following_url = f"{base_url}/twitter/user/following"
    params = {'userName': 'Tomasz16066938'}  # Test na koncie ktorego szukamy

    try:
        response = requests.get(following_url, headers=headers, params=params, timeout=15)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                following_list = data.get('data', {}).get('following', [])
                print(f"   OK DZIALA! - pobrano {len(following_list)} obserwowanych")

                if following_list:
                    print("   Przyklad obserwowanych:")
                    for i, user in enumerate(following_list[:3], 1):
                        username = user.get('userName', 'N/A')
                        name = user.get('name', 'N/A')
                        print(f"   {i}. @{username} ({name})")

            else:
                print(f"   BLAD API: {data.get('msg', 'Nieznany blad')}")
        elif response.status_code == 429:
            print("   RATE LIMIT - poczekaj 5 sekund")
        elif response.status_code == 402:
            print("   BRAK KREDYTOW - konto wyczerpane")
        else:
            print(f"   BLAD HTTP: {response.status_code}")
            print(f"   Odpowiedz: {response.text[:200]}")

    except Exception as e:
        print(f"   BLAD: {e}")

    time.sleep(6)

    # Test 4: Followers list
    print("\n4. Lista obserwujacych:")
    followers_url = f"{base_url}/twitter/user/followers"
    params = {'userName': test_username}

    try:
        response = requests.get(followers_url, headers=headers, params=params, timeout=15)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                followers_list = data.get('data', {}).get('followers', [])
                print(f"   OK DZIALA! - pobrano {len(followers_list)} obserwujacych")
            else:
                print(f"   BLAD API: {data.get('msg', 'Nieznany blad')}")
        elif response.status_code == 429:
            print("   RATE LIMIT")
        elif response.status_code == 402:
            print("   BRAK KREDYTOW")
        else:
            print(f"   BLAD HTTP: {response.status_code}")

    except Exception as e:
        print(f"   BLAD: {e}")

    print("\n" + "="*60)
    print("PODSUMOWANIE TWITTERAPI.IO:")
    print("="*60)
    print("Free tier - 1 request co 5 sekund")
    print("Prawdopodobnie DOSTEPNE:")
    print("- Informacje o uzytkownikach")
    print("- Tweety uzytkownikow")
    print("- Lista obserwowanych (following) ← TO CHCEMY!")
    print("- Lista obserwujacych (followers)")
    print("\nALE: wymaga kredytow (nawet na free tier)")

if __name__ == "__main__":
    check_twitterapi_io_capabilities()