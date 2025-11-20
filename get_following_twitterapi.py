#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

def get_following_twitterapi_io(username):
    api_key = os.getenv('TWITTERAPI_IO_KEY')

    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

    print(f"=== LISTA OBSERWOWANYCH PRZEZ @{username.upper()} ===")
    print("Uzywam twitterapi.io...")

    # Get following list
    following_url = f"{base_url}/twitter/user/following"
    params = {'userName': username}

    try:
        print("Pobieranie listy obserwowanych...")
        response = requests.get(following_url, headers=headers, params=params, timeout=20)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data.get('status') == 'success':
                following_data = data.get('data', {})
                following_list = following_data.get('following', [])

                print(f"\nSUKCES! Pobrano {len(following_list)} obserwowanych uzytkownikow:")
                print("=" * 80)

                for i, user in enumerate(following_list, 1):
                    username_followed = user.get('userName', 'N/A')
                    name = user.get('name', 'Brak nazwy')
                    description = user.get('description', 'Brak opisu')
                    followers = user.get('followersCount', 0)
                    verified = user.get('verified', False)

                    # Obciecie opisu
                    if len(description) > 80:
                        description = description[:80] + "..."

                    verify_mark = " [VERIFIED]" if verified else ""

                    print(f"{i:3d}. @{username_followed}{verify_mark}")
                    print(f"     {name}")
                    print(f"     {description}")
                    print(f"     Followers: {followers:,}")
                    print()

                # Zapisz do pliku
                output_file = f'data/raw/{username}_following_twitterapi.json'
                os.makedirs('data/raw', exist_ok=True)

                output_data = {
                    'username': username,
                    'following_count': len(following_list),
                    'following': following_list,
                    'source': 'twitterapi.io',
                    'api_response': data
                }

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)

                print(f"Dane zapisane do: {output_file}")
                return True

            else:
                error_msg = data.get('msg', 'Nieznany blad')
                print(f"BLAD API: {error_msg}")
                return False

        elif response.status_code == 429:
            print("RATE LIMIT - za duzo zapytan, poczekaj 5 sekund")
            return False

        elif response.status_code == 402:
            print("BRAK KREDYTOW - konto wyczerpane")
            return False

        elif response.status_code == 401:
            print("UNAUTHORIZED - nieprawidlowy API key")
            return False

        else:
            print(f"HTTP ERROR {response.status_code}")
            print(f"Odpowiedz: {response.text}")
            return False

    except Exception as e:
        print(f"BLAD: {e}")
        return False

if __name__ == "__main__":
    # Najpierw test z znanym userem
    print("TEST 1 - znany uzytkownik @MarekLangalis:")
    test_success = get_following_twitterapi_io("MarekLangalis")

    if test_success:
        print("\nEndpoint dziala! Teraz sprawdzam @Tomasz16066938...")
        time.sleep(6)  # Rate limit

        target_username = "Tomasz16066938"
        success = get_following_twitterapi_io(target_username)

        if success:
            print(f"\nGOTOWE! Lista obserwowanych przez @{target_username} pobrana!")
        else:
            print(f"\nNIE UDALO SIE pobrać listy dla @{target_username}")
            print("Mozliwe przyczyny:")
            print("- Uzytkownik nie istnieje lub zmienil nazwe")
            print("- Konto prywatne/chronione")
            print("- TwitterAPI.io nie moze znalezc tego uzytkownika")
    else:
        print("\nEndpoint nie dziala lub brak kredytow")
        print("Sprawdź na: https://twitterapi.io/dashboard")