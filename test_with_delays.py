#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

def test_with_proper_delays():
    api_key = os.getenv('TWITTER_API_KEY')

    print("=== TwitterAPI.io Test with 5-second delays ===")
    print(f"API Key: {api_key}")
    print("Free tier: 1 request every 5 seconds")

    headers = {'x-api-key': api_key}

    # Test 1: User lookup
    print(f"\n1. Testing user lookup for @MarekLangalis...")
    user_url = "https://api.twitterapi.io/v2/users/by/username/MarekLangalis"

    try:
        response = requests.get(user_url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("SUCCESS: User found!")
            user_data = response.json()
            print(f"User: {json.dumps(user_data, indent=2)}")

            user_id = user_data.get('data', {}).get('id')
            if user_id:
                print(f"User ID for MarekLangalis: {user_id}")

                # Wait 6 seconds before next request (to be safe)
                print("Waiting 6 seconds for next request...")
                time.sleep(6)

                # Test 2: Get tweets
                print(f"\n2. Getting tweets for user ID: {user_id}")
                tweets_url = f"https://api.twitterapi.io/v2/users/{user_id}/tweets"
                params = {
                    'max_results': 1,  # Just 1 tweet as requested
                    'tweet.fields': 'created_at,public_metrics'
                }

                tweet_response = requests.get(tweets_url, headers=headers, params=params, timeout=30)
                print(f"Tweet Status: {tweet_response.status_code}")

                if tweet_response.status_code == 200:
                    tweets_data = tweet_response.json()
                    print(f"SUCCESS: Tweets retrieved!")
                    print(f"Response: {json.dumps(tweets_data, indent=2)}")

                    tweets = tweets_data.get('data', [])
                    if tweets:
                        latest_tweet = tweets[0]
                        print(f"\n=== LATEST TWEET FROM @MarekLangalis ===")
                        print(f"Text: {latest_tweet.get('text')}")
                        print(f"Created: {latest_tweet.get('created_at')}")
                        metrics = latest_tweet.get('public_metrics', {})
                        print(f"Retweets: {metrics.get('retweet_count', 0)}")
                        print(f"Likes: {metrics.get('like_count', 0)}")
                        print(f"Replies: {metrics.get('reply_count', 0)}")
                        print("=== SUCCESS! ===")
                        return True
                    else:
                        print("No tweets found in response")
                else:
                    print(f"Tweet request failed: {tweet_response.text}")

        elif response.status_code == 429:
            print("Still rate limited. Wait longer between requests.")
            print(f"Response: {response.text}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

    return False

if __name__ == "__main__":
    success = test_with_proper_delays()
    if success:
        print("\n✅ API test successful! TwitterAPI.io is working.")
        print("You can now use the main application with rate limiting.")
    else:
        print("\n❌ API test failed. Check the output above for details.")
        print("Visit https://twitterapi.io/dashboard to check your account.")