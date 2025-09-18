#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def check_api_capabilities():
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json'
    }

    print("=== SPRAWDZANIE DOSTEPNYCH FUNKCJI TWITTER API v2 ===\n")

    test_username = "MarekLangalis"

    # Test 1: User lookup (basic)
    print("1. Pobieranie informacji o uzytkowniku:")
    user_url = f"https://api.twitter.com/2/users/by/username/{test_username}"
    try:
        response = requests.get(user_url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   OK DZIALA - mozna pobierac dane uzytkownika")
        else:
            print(f"   BLAD: {response.json()}")
    except Exception as e:
        print(f"   BLAD: {e}")

    # Test 2: User tweets (basic)
    print("\n2. Pobieranie tweetow uzytkownika:")
    user_id = None
    if response.status_code == 200:
        user_id = response.json()['data']['id']
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {'max_results': 5}

        try:
            tweets_response = requests.get(tweets_url, headers=headers, params=params)
            print(f"   Status: {tweets_response.status_code}")
            if tweets_response.status_code == 200:
                print("   OK DZIALA - mozna pobierac tweety")
            else:
                print(f"   BLAD: {tweets_response.json()}")
        except Exception as e:
            print(f"   BLAD: {e}")

    # Test 3: Following list (elevated access required)
    print("\n3. Lista obserwowanych:")
    if user_id:
        following_url = f"https://api.twitter.com/2/users/{user_id}/following"
    else:
        print("   POMINIETO - brak user_id")
        following_url = None
    if following_url:
        try:
            following_response = requests.get(following_url, headers=headers)
        print(f"   Status: {following_response.status_code}")
        if following_response.status_code == 200:
            print("   OK DZIALA - mozna pobierac liste obserwowanych")
        else:
            error_data = following_response.json()
            print(f"   BRAK DOSTEPU: {error_data.get('title', 'Nieznany blad')}")
            if 'client-not-enrolled' in str(error_data):
                print("   Wymaga wyzszego poziomu dostepu API")
    except Exception as e:
        print(f"   BLAD: {e}")

    # Test 4: Followers list (elevated access required)
    print("\n4. Lista obserwujacych:")
    if user_id:
        followers_url = f"https://api.twitter.com/2/users/{user_id}/followers"
    else:
        print("   POMINIETO - brak user_id")
        followers_url = None
    if followers_url:
        try:
            followers_response = requests.get(followers_url, headers=headers)
        print(f"   Status: {followers_response.status_code}")
        if followers_response.status_code == 200:
            print("   OK DZIALA - mozna pobierac liste obserwujacych")
        else:
            error_data = followers_response.json()
            print(f"   BRAK DOSTEPU: {error_data.get('title', 'Nieznany blad')}")
            if 'client-not-enrolled' in str(error_data):
                print("   Wymaga wyzszego poziomu dostepu API")
    except Exception as e:
        print(f"   BLAD: {e}")

    # Test 5: Search tweets (basic but limited)
    print("\n5. Wyszukiwanie tweetow:")
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    params = {'query': 'bitcoin', 'max_results': 10}
    try:
        search_response = requests.get(search_url, headers=headers, params=params)
        print(f"   Status: {search_response.status_code}")
        if search_response.status_code == 200:
            print("   OK DZIALA - mozna wyszukiwac tweety")
        else:
            error_data = search_response.json()
            print(f"   BRAK DOSTEPU: {error_data.get('title', 'Nieznany blad')}")
    except Exception as e:
        print(f"   BLAD: {e}")

    print("\n" + "="*60)
    print("PODSUMOWANIE - CO MOZESZ ROBIC Z DARMOWYM API:")
    print("="*60)
    print("OK Pobieranie informacji o uzytkownikach")
    print("OK Pobieranie tweetow konkretnych uzytkownikow")
    print("OK Podstawowe wyszukiwanie tweetow (ograniczone)")
    print("NIE Lista obserwowanych (wymaga Elevated Access)")
    print("NIE Lista obserwujacych (wymaga Elevated Access)")
    print("NIE Zaawansowane wyszukiwanie (wymaga Academic Research)")
    print("\nTwoje API ma podstawowy dostep (Essential/Free tier)")

if __name__ == "__main__":
    check_api_capabilities()