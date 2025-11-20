#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

def test_with_username():
    api_key = os.getenv('TWITTER_API_KEY')

    print("=== TwitterAPI.io Test - userName parameter ===")
    print("Testing with userName (camelCase) parameter...")
    print("Waiting 10 seconds to reset rate limit...")
    time.sleep(10)

    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

    # Test user info with userName parameter
    print(f"\nGetting user info for @MarekLangalis...")
    user_info_url = f"{base_url}/twitter/user/info"
    params = {'userName': 'MarekLangalis'}

    try:
        response = requests.get(user_info_url, headers=headers, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("SUCCESS: User info retrieved!")
            user_data = response.json()
            print(f"User info: {json.dumps(user_data, indent=2)}")

            # Wait 6 seconds
            print("Waiting 6 seconds...")
            time.sleep(6)

            # Now get tweets
            print(f"\nGetting tweets...")
            tweets_url = f"{base_url}/twitter/user/last_tweets"
            tweet_params = {'userName': 'MarekLangalis'}

            tweet_response = requests.get(tweets_url, headers=headers, params=tweet_params, timeout=30)
            print(f"Tweet Status: {tweet_response.status_code}")

            if tweet_response.status_code == 200:
                print("SUCCESS: Tweets retrieved!")
                tweets_data = tweet_response.json()
                print(f"Tweets: {json.dumps(tweets_data, indent=2)}")

                # Extract latest tweet
                if isinstance(tweets_data, list) and len(tweets_data) > 0:
                    tweet = tweets_data[0]
                elif isinstance(tweets_data, dict):
                    tweets = tweets_data.get('data', tweets_data.get('tweets', []))
                    if tweets:
                        tweet = tweets[0]
                    else:
                        tweet = None

                if tweet:
                    print(f"\n=== LATEST TWEET FROM @MarekLangalis ===")
                    print(f"Text: {tweet.get('text', tweet.get('full_text', 'No text'))}")
                    print(f"Date: {tweet.get('created_at')}")
                    print(f"Retweets: {tweet.get('retweet_count', 0)}")
                    print(f"Likes: {tweet.get('favorite_count', tweet.get('like_count', 0))}")
                    print("=== MISSION ACCOMPLISHED! ===")
                    return True
                else:
                    print("Could not extract tweet from response")
            else:
                print(f"Tweets failed: {tweet_response.text}")

        elif response.status_code == 429:
            print("Still rate limited - need to wait longer or upgrade account")
            print(f"Response: {response.text}")
        else:
            print(f"User info failed: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

    return False

if __name__ == "__main__":
    success = test_with_username()
    if success:
        print("\n✅ SUCCESS! TwitterAPI.io is working correctly.")
        print("Your application can now fetch tweets from @MarekLangalis")
    else:
        print("\n⚠️ API key works but may need more time between requests or account upgrade.")