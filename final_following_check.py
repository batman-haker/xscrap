#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

def final_check():
    api_key = os.getenv('TWITTERAPI_IO_KEY')
    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

    username = "elonmusk"

    print(f"=== OSTATECZNY TEST DLA @{username} ===")

    # Test user info
    print("\n1. User info:")
    user_url = f"{base_url}/twitter/user/info"
    params = {'userName': username}

    try:
        response = requests.get(user_url, headers=headers, params=params, timeout=15)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                user_data = data.get('data', {})
                print("SUKCES - uzytkownik znaleziony!")
                print(f"Username: @{user_data.get('userName', 'N/A')}")
                print(f"Name: {user_data.get('name', 'N/A')}")
                print(f"Following count: {user_data.get('followingCount', 0)}")
                print(f"Protected: {user_data.get('protected', False)}")

                time.sleep(6)

                # Test following
                print("\n2. Following list:")
                following_url = f"{base_url}/twitter/user/following"
                following_params = {'userName': username}

                following_response = requests.get(following_url, headers=headers, params=following_params, timeout=20)
                print(f"Status: {following_response.status_code}")

                if following_response.status_code == 200:
                    following_data = following_response.json()
                    print(f"API Status: {following_data.get('status', 'unknown')}")
                    print(f"Message: {following_data.get('msg', 'No message')}")

                    if following_data.get('status') == 'success':
                        following_list = following_data.get('data', {}).get('following', [])
                        print(f"SUKCES! Pobrano {len(following_list)} obserwowanych!")

                        # Zapisz do pliku
                        if following_list:
                            output_file = f'data/raw/{username}_following_final.json'
                            os.makedirs('data/raw', exist_ok=True)

                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump({
                                    'username': username,
                                    'following_count': len(following_list),
                                    'following': following_list
                                }, f, indent=2, ensure_ascii=False)

                            print(f"Dane zapisane do: {output_file}")

                            print("\nPierwszych 10 obserwowanych:")
                            for i, user in enumerate(following_list[:10], 1):
                                print(f"{i}. @{user.get('userName', 'N/A')} - {user.get('name', 'N/A')}")

                        return True
                    else:
                        print(f"BLAD: {following_data.get('msg', 'Unknown error')}")

                else:
                    print(f"HTTP Error: {following_response.status_code}")
                    print(f"Response: {following_response.text}")

            else:
                print(f"User not found: {data.get('msg', 'Unknown error')}")

        else:
            print(f"HTTP Error: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

    return False

if __name__ == "__main__":
    success = final_check()
    print(f"\nWynik: {'SUKCES' if success else 'NIEPOWODZENIE'}")