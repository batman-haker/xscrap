#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_api():
    api_key = os.getenv('TWITTER_API_KEY')

    print("=== TwitterAPI.io Test ===")
    print(f"API Key: {api_key[:15]}..." if api_key else "No API key")

    if not api_key:
        print("ERROR: No API key found")
        return

    # Correct headers for TwitterAPI.io
    base_url = "https://api.twitterapi.io"
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }

    # Try user lookup for MarekLangalis
    user_endpoint = f"{base_url}/twitter/user"
    params = {'screen_name': 'MarekLangalis'}

    print(f"\nTesting user lookup: {user_endpoint}")
    print(f"Params: {params}")
    print(f"Headers: x-api-key: {api_key[:15]}...")

    try:
        response = requests.get(user_endpoint, params=params, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 401:
            print("ERROR: Still unauthorized")
            print(f"Response: {response.text}")
            print("Please check API key at: https://twitterapi.io/dashboard")

        elif response.status_code == 200:
            print("SUCCESS: User found!")
            data = response.json()
            print(f"User data received: {json.dumps(data, indent=2)}")

            # Try getting timeline
            print(f"\nTesting timeline...")
            timeline_endpoint = f"{base_url}/twitter/timeline"
            timeline_params = {
                'screen_name': 'MarekLangalis',
                'count': 1,
                'include_rts': False,
                'exclude_replies': True
            }

            timeline_response = requests.get(timeline_endpoint, params=timeline_params, headers=headers, timeout=30)
            print(f"Timeline Status: {timeline_response.status_code}")

            if timeline_response.status_code == 200:
                tweets = timeline_response.json()
                print(f"Timeline response type: {type(tweets)}")
                print(f"Timeline response: {json.dumps(tweets, indent=2)}")

                if isinstance(tweets, list) and len(tweets) > 0:
                    tweet = tweets[0]
                    print(f"\n=== LATEST TWEET FROM @MarekLangalis ===")
                    print(f"Text: {tweet.get('text', tweet.get('full_text', 'No text'))}")
                    print(f"Date: {tweet.get('created_at')}")
                    print(f"Retweets: {tweet.get('retweet_count', 0)}")
                    print(f"Likes: {tweet.get('favorite_count', 0)}")
                    print("=== SUCCESS ===")
                else:
                    print("No tweets found in response")
            else:
                print(f"Timeline error: {timeline_response.text}")

        else:
            print(f"Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_api()