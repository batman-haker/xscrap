#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_twitter_v2():
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    print("=== Testing Twitter API v2 ===")

    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json'
    }

    # Get user ID for MarekLangalis
    user_url = "https://api.twitter.com/2/users/by/username/MarekLangalis"

    try:
        print("Getting user info...")
        user_response = requests.get(user_url, headers=headers)
        print(f"User Status: {user_response.status_code}")

        if user_response.status_code == 200:
            user_data = user_response.json()
            user_id = user_data['data']['id']
            print(f"User ID: {user_id}")

            # Get tweets
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                'max_results': 5,
                'tweet.fields': 'created_at,public_metrics,text'
            }

            print("Getting tweets...")
            tweets_response = requests.get(tweets_url, headers=headers, params=params)
            print(f"Tweets Status: {tweets_response.status_code}")

            if tweets_response.status_code == 200:
                tweets_data = tweets_response.json()
                tweets = tweets_data.get('data', [])

                if tweets:
                    latest = tweets[0]
                    print("\n" + "="*50)
                    print("LATEST TWEET - Twitter API v2")
                    print("="*50)
                    print(f"Text: {latest.get('text', '')}")
                    print(f"Created: {latest.get('created_at', '')}")
                    metrics = latest.get('public_metrics', {})
                    print(f"Likes: {metrics.get('like_count', 0)}")
                    print(f"Retweets: {metrics.get('retweet_count', 0)}")
                    print(f"Replies: {metrics.get('reply_count', 0)}")
                    print("="*50)
                    return True

            else:
                print(f"Tweets error: {tweets_response.text}")
        else:
            print(f"User error: {user_response.text}")

    except Exception as e:
        print(f"Error: {e}")

    return False

if __name__ == "__main__":
    success = test_twitter_v2()
    if success:
        print("\nSUCCESS: Twitter API v2 working!")
    else:
        print("\nFAILED: Check credentials")