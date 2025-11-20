"""
Simple test of TwitterAPI.io to see available data
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

# Test with different count parameters
counts_to_test = [20, 50, 100, 200]

for count in counts_to_test:
    print(f"\n=== Testing count={count} ===")

    url = f"{base_url}/twitter/user/last_tweets"
    params = {'userName': username, 'count': count}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        data = response.json()

        if data.get('status') == 'success':
            tweets = data.get('data', {}).get('tweets', [])
            print(f"Requested: {count}, Got: {len(tweets)} tweets")

            # Count original vs retweets
            originals = 0
            retweets = 0
            for tweet in tweets:
                text = tweet.get('text', '')
                if text.startswith('RT @'):
                    retweets += 1
                else:
                    originals += 1

            print(f"Originals: {originals}, Retweets: {retweets}")

            # Show date range
            if tweets:
                first_date = tweets[0].get('createdAt', '')
                last_date = tweets[-1].get('createdAt', '')
                print(f"Date range: {last_date} to {first_date}")

        else:
            print(f"API Error: {data.get('msg', 'Unknown error')}")

    except Exception as e:
        print(f"Error: {e}")