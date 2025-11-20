#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

def check_user_and_following():
    api_key = os.getenv('TWITTERAPI_IO_KEY')
    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

    username = "Tomasz16066938"

    print(f"=== SPRAWDZANIE KONTA @{username} ===\n")

    # 1. Sprawdź informacje o użytkowniku
    print("1. Sprawdzanie czy uzytkownik istnieje:")
    user_url = f"{base_url}/twitter/user/info"
    params = {'userName': username}

    try:
        response = requests.get(user_url, headers=headers, params=params, timeout=15)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   Odpowiedz API: {data.get('status', 'unknown')}")

            if data.get('status') == 'success':
                user_data = data.get('data', {})
                print(f"   ✓ UZYTKOWNIK ZNALEZIONY!")
                print(f"   Username: @{user_data.get('userName', 'N/A')}")
                print(f"   Name: {user_data.get('name', 'N/A')}")
                print(f"   Followers: {user_data.get('followersCount', 0):,}")
                print(f"   Following: {user_data.get('followingCount', 0):,}")
                print(f"   Protected: {user_data.get('protected', False)}")

                # 2. Jeśli user istnieje, spróbuj pobrać following
                time.sleep(6)  # Rate limit
                print(f"\n2. Pobieranie listy obserwowanych przez @{username}:")

                following_url = f"{base_url}/twitter/user/following"
                following_params = {'userName': username}

                following_response = requests.get(following_url, headers=headers, params=following_params, timeout=20)
                print(f"   Status: {following_response.status_code}")

                if following_response.status_code == 200:
                    following_data = following_response.json()
                    print(f"   Odpowiedz API: {following_data.get('status', 'unknown')}")

                    if following_data.get('status') == 'success':
                        following_list = following_data.get('data', {}).get('following', [])
                        print(f"   ✓ SUKCES! Pobrano {len(following_list)} obserwowanych")

                        # Pokazuj pierwsze 5
                        for i, user in enumerate(following_list[:5], 1):
                            username_followed = user.get('userName', 'N/A')
                            name = user.get('name', 'N/A')
                            print(f"   {i}. @{username_followed} ({name})")

                        if len(following_list) > 5:
                            print(f"   ... i {len(following_list) - 5} więcej")

                        return True
                    else:
                        error_msg = following_data.get('msg', 'Nieznany błąd')
                        print(f"   ✗ BŁĄD: {error_msg}")
                else:
                    print(f"   ✗ HTTP ERROR: {following_response.status_code}")

            else:
                error_msg = data.get('msg', 'Nieznany błąd')
                print(f"   ✗ UŻYTKOWNIK NIE ZNALEZIONY: {error_msg}")

        else:
            print(f"   ✗ HTTP ERROR: {response.status_code}")
            print(f"   Odpowiedź: {response.text[:200]}")

    except Exception as e:
        print(f"   ✗ BŁĄD: {e}")

    return False

if __name__ == "__main__":
    success = check_user_and_following()
    if not success:
        print("\nNIE UDAŁO SIĘ pobrać danych")
        print("Sprawdź saldo kredytów na: https://twitterapi.io/dashboard")