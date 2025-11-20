#!/usr/bin/env python3
"""
Fetch 100 tweets from kot_b0t using Twitter API v2 with pagination
"""
import requests
import json
import time
from datetime import datetime

# Configuration
USER_ID = "1222026166241902592"  # kot_b0t
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAAEK4QEAAAAAViLvNU%2FIgR%2FwwQOy2wy63iRey08%3DgTgI2xoNKbKd9lNMN2vFRpM8cJAqiW2eAzdu9eWG472mb1xpSv"
OUTPUT_FILE = "data/cache/kot_b0t_100_tweets.json"

def fetch_tweets(user_id, bearer_token, max_results=100):
    """Fetch tweets using Twitter API v2"""

    url = f"https://api.twitter.com/2/users/{user_id}/tweets"

    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }

    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics,text",
        "exclude": "retweets,replies"
    }

    all_tweets = []
    request_count = 0
    max_requests = 5  # Safety limit

    print(f"Starting to fetch up to {max_results} tweets...")

    while len(all_tweets) < max_results and request_count < max_requests:
        request_count += 1

        try:
            print(f"\nRequest #{request_count}: Fetching tweets...")
            response = requests.get(url, headers=headers, params=params, verify=False)

            if response.status_code == 429:
                print("Rate limit hit! Waiting 60 seconds...")
                time.sleep(60)
                continue

            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                print(response.text)
                break

            data = response.json()

            if "data" not in data:
                print("No data in response")
                break

            tweets = data["data"]
            all_tweets.extend(tweets)

            print(f"Fetched {len(tweets)} tweets (Total: {len(all_tweets)})")

            # Check if there's more data
            if "meta" in data and "next_token" in data["meta"]:
                params["pagination_token"] = data["meta"]["next_token"]
                print(f"More data available, continuing...")
                time.sleep(2)  # Small delay between requests
            else:
                print("No more tweets available")
                break

        except Exception as e:
            print(f"Exception: {e}")
            break

    return all_tweets

def save_tweets(tweets, output_file):
    """Save tweets to JSON file"""

    formatted_tweets = []

    for idx, tweet in enumerate(tweets, 1):
        formatted_tweet = {
            "username": "kot_b0t",
            "user_name": "Kot Bot",
            "text": tweet.get("text", ""),
            "created_at": tweet.get("created_at", ""),
            "like_count": tweet.get("public_metrics", {}).get("like_count", 0),
            "retweet_count": tweet.get("public_metrics", {}).get("retweet_count", 0),
            "reply_count": tweet.get("public_metrics", {}).get("reply_count", 0),
            "view_count": tweet.get("public_metrics", {}).get("impression_count", 0),
            "tweet_id": tweet.get("id", ""),
            "tweet_index": idx
        }
        formatted_tweets.append(formatted_tweet)

    output_data = {
        "tweets": formatted_tweets,
        "last_updated": datetime.now().isoformat(),
        "total_tweets": len(formatted_tweets),
        "user_id": USER_ID
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(formatted_tweets)} tweets to {output_file}")

def main():
    print("=" * 60)
    print("Twitter Tweet Fetcher - kot_b0t (100 tweets)")
    print("=" * 60)

    # Fetch tweets
    tweets = fetch_tweets(USER_ID, BEARER_TOKEN, max_results=100)

    if not tweets:
        print("\nNo tweets fetched!")
        return

    # Save to file
    save_tweets(tweets, OUTPUT_FILE)

    print("\n" + "=" * 60)
    print(f"COMPLETE! Fetched {len(tweets)} tweets")
    print("=" * 60)

if __name__ == "__main__":
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    main()
