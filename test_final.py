#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

def test_correct_endpoints():
    api_key = os.getenv('TWITTER_API_KEY')

    print("=== TwitterAPI.io Test - Correct Endpoints ===")
    print(f"API Key: {api_key}")
    print("Free tier: 1 request every 5 seconds")

    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

    # Test 1: Get user info
    print(f"\n1. Getting user info for @MarekLangalis...")
    user_info_url = f"{base_url}/twitter/user/info"

    # Try different parameter formats
    param_variants = [
        {'username': 'MarekLangalis'},
        {'screen_name': 'MarekLangalis'},
        {'user': 'MarekLangalis'},
        {'q': 'MarekLangalis'}
    ]

    user_data = None
    for params in param_variants:
        print(f"Trying with params: {params}")
        try:
            response = requests.get(user_info_url, headers=headers, params=params, timeout=30)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                print("SUCCESS: User info retrieved!")
                user_data = response.json()
                print(f"User info: {json.dumps(user_data, indent=2)}")
                break
            elif response.status_code == 429:
                print("Rate limited - waiting 6 seconds...")
                time.sleep(6)
            else:
                print(f"Response: {response.text}")

            time.sleep(1)  # Small delay between variants
        except Exception as e:
            print(f"Error: {e}")

    # Wait before next request
    print("Waiting 6 seconds before next request...")
    time.sleep(6)

    # Test 2: Get user's last tweets
    print(f"\n2. Getting last tweets for @MarekLangalis...")
    tweets_url = f"{base_url}/twitter/user/last_tweets"

    tweet_params_variants = [
        {'username': 'MarekLangalis', 'count': 1},
        {'screen_name': 'MarekLangalis', 'count': 1},
        {'user': 'MarekLangalis', 'limit': 1},
        {'q': 'MarekLangalis', 'max_results': 1}
    ]

    for params in tweet_params_variants:
        print(f"Trying tweets with params: {params}")
        try:
            response = requests.get(tweets_url, headers=headers, params=params, timeout=30)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                print("SUCCESS: Tweets retrieved!")
                tweets_data = response.json()
                print(f"Tweets response: {json.dumps(tweets_data, indent=2)}")

                # Try to extract the latest tweet
                if isinstance(tweets_data, dict):
                    tweets = tweets_data.get('data', tweets_data.get('tweets', []))
                elif isinstance(tweets_data, list):
                    tweets = tweets_data
                else:
                    tweets = []

                if tweets and len(tweets) > 0:
                    latest_tweet = tweets[0]
                    print(f"\n=== LATEST TWEET FROM @MarekLangalis ===")
                    print(f"Text: {latest_tweet.get('text', latest_tweet.get('full_text', 'No text'))}")
                    print(f"Created: {latest_tweet.get('created_at')}")
                    print(f"Retweets: {latest_tweet.get('retweet_count', 0)}")
                    print(f"Likes: {latest_tweet.get('favorite_count', latest_tweet.get('like_count', 0))}")
                    print("=== SUCCESS! ===")
                    return True
                else:
                    print("No tweets found in response")

                break
            elif response.status_code == 429:
                print("Rate limited - need to wait longer")
                print(f"Response: {response.text}")
                time.sleep(6)
            else:
                print(f"Response: {response.text}")

            time.sleep(2)  # Delay between variants
        except Exception as e:
            print(f"Error: {e}")

    return False

if __name__ == "__main__":
    success = test_correct_endpoints()
    if success:
        print("\nAPI test successful! You can now use the application.")
    else:
        print("\nAPI test incomplete. Check https://twitterapi.io/dashboard for account status.")
        print("The API key works but may need proper parameters or more credits.")