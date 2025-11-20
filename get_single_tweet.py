#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def get_marek_tweet():
    api_key = os.getenv('TWITTER_API_KEY')

    print("=== Getting latest tweet from @MarekLangalis ===")

    headers = {'x-api-key': api_key}
    base_url = "https://api.twitterapi.io"

    # Get just 1 tweet from MarekLangalis
    tweets_url = f"{base_url}/twitter/user/last_tweets"
    params = {'userName': 'MarekLangalis'}

    try:
        print("Requesting latest tweet...")
        response = requests.get(tweets_url, headers=headers, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            response_data = response.json()

            if response_data.get('status') == 'success':
                tweets = response_data.get('data', {}).get('tweets', [])

                if tweets:
                    latest_tweet = tweets[0]

                    print("\n" + "="*60)
                    print("LATEST TWEET FROM @MarekLangalis")
                    print("="*60)
                    text = latest_tweet.get('text', 'No text').encode('ascii', 'ignore').decode('ascii')
                    print(f"Text: {text}")
                    print(f"Date: {latest_tweet.get('createdAt', 'Unknown')}")
                    print(f"Likes: {latest_tweet.get('likeCount', 0)}")
                    print(f"Retweets: {latest_tweet.get('retweetCount', 0)}")
                    print(f"Replies: {latest_tweet.get('replyCount', 0)}")
                    print(f"Views: {latest_tweet.get('viewCount', 0)}")
                    print("="*60)

                    return True
                else:
                    print("No tweets found in response")
            else:
                print(f"API error: {response_data.get('msg', 'Unknown error')}")

        elif response.status_code == 429:
            print("Rate limited - wait 5 seconds and try again")
            print("Free tier: 1 request every 5 seconds")

        else:
            print(f"HTTP Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

    return False

if __name__ == "__main__":
    success = get_marek_tweet()

    if success:
        print("\nSUCCESS: Tweet retrieved!")
    else:
        print("\nFAILED: Could not get tweet")
        print("Check your API key at: https://twitterapi.io/dashboard")