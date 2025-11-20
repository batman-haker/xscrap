#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_api():
    api_key = os.getenv('TWITTER_API_KEY')

    print("=== API Test ===")
    print(f"API Key: {api_key[:15]}..." if api_key else "No API key")

    if not api_key:
        print("ERROR: No API key found")
        return

    # Test basic connection
    base_url = "https://api.twitterapi.io"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Try user lookup for MarekLangalis
    user_endpoint = f"{base_url}/twitter/user"
    params = {'screen_name': 'MarekLangalis'}

    print(f"\nTesting: {user_endpoint}")
    print(f"Params: {params}")

    try:
        response = requests.get(user_endpoint, params=params, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 401:
            print("\nERROR: Unauthorized - API key invalid or expired")
            print("Check your API key at: https://twitterapi.io/dashboard")

        elif response.status_code == 200:
            print("SUCCESS: User found!")
            data = response.json()
            print(f"User: {data.get('name', 'Unknown')}")

            # Try getting timeline
            timeline_endpoint = f"{base_url}/twitter/timeline"
            timeline_params = {
                'screen_name': 'MarekLangalis',
                'count': 1
            }

            print(f"\nTesting timeline: {timeline_endpoint}")
            timeline_response = requests.get(timeline_endpoint, params=timeline_params, headers=headers, timeout=30)
            print(f"Timeline Status: {timeline_response.status_code}")

            if timeline_response.status_code == 200:
                tweets = timeline_response.json()
                if tweets and len(tweets) > 0:
                    tweet = tweets[0]
                    print(f"\nLatest tweet:")
                    print(f"Text: {tweet.get('text', tweet.get('full_text', 'No text'))}")
                    print(f"Date: {tweet.get('created_at')}")
                else:
                    print("No tweets found")
            else:
                print(f"Timeline error: {timeline_response.text}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_api()