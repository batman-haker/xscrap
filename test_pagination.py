"""
Test pagination parameters for TwitterAPI.io
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('TWITTER_API_KEY')
headers = {"x-api-key": api_key}
base_url = "https://api.twitterapi.io"
username = "stocktavia"

# Get initial batch to find the oldest tweet ID
print("=== Getting initial tweets ===")
url = f"{base_url}/twitter/user/last_tweets"
params = {'userName': username}

response = requests.get(url, headers=headers, params=params, timeout=30)
data = response.json()

if data.get('status') == 'success':
    tweets = data.get('data', {}).get('tweets', [])
    print(f"Got {len(tweets)} tweets")

    if tweets:
        oldest_tweet = tweets[-1]  # Last in chronological order
        oldest_id = oldest_tweet.get('id', '')
        print(f"Oldest tweet ID: {oldest_id}")
        print(f"Oldest tweet date: {oldest_tweet.get('createdAt', '')}")
        print(f"Oldest tweet text: {oldest_tweet.get('text', '')[:100]}...")

        # Test pagination parameters
        pagination_params = [
            {'userName': username, 'max_id': oldest_id},
            {'userName': username, 'since_id': oldest_id},
            {'userName': username, 'before': oldest_id},
            {'userName': username, 'after': oldest_id},
            {'userName': username, 'cursor': oldest_id},
            {'userName': username, 'offset': 20},
            {'userName': username, 'page': 2},
        ]

        for i, params in enumerate(pagination_params, 1):
            print(f"\n=== Test {i}: {params} ===")
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                data = response.json()

                if data.get('status') == 'success':
                    new_tweets = data.get('data', {}).get('tweets', [])
                    print(f"Got {len(new_tweets)} tweets")

                    if new_tweets:
                        # Check if these are different tweets
                        new_ids = [t.get('id') for t in new_tweets]
                        original_ids = [t.get('id') for t in tweets]

                        unique_tweets = [id for id in new_ids if id not in original_ids]
                        print(f"Unique tweets: {len(unique_tweets)}")

                        if unique_tweets:
                            print(f"SUCCESS! Found new tweets with parameter: {list(params.keys())[-1]}")
                            sample_new = new_tweets[0]
                            print(f"Sample new tweet: {sample_new.get('text', '')[:100]}...")
                        else:
                            print("Same tweets returned")
                else:
                    print(f"API Error: {data.get('msg', 'Unknown error')}")
            except Exception as e:
                print(f"Error: {e}")
else:
    print(f"Initial request failed: {data.get('msg', 'Unknown error')}")