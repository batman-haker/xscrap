"""
Test advanced pagination with TwitterAPI.io
Based on documentation that confirms pagination is supported
"""
import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('TWITTER_API_KEY')
headers = {"x-api-key": api_key}
base_url = "https://api.twitterapi.io"
username = "stocktavia"

all_tweets = []
max_pages = 5  # Limit to prevent excessive API calls

for page in range(1, max_pages + 1):
    print(f"\n=== PAGE {page} ===")

    url = f"{base_url}/twitter/user/last_tweets"

    # Try different pagination approaches
    if page == 1:
        params = {'userName': username}
    else:
        # Use the oldest tweet from previous batch for pagination
        if all_tweets:
            oldest_tweet = all_tweets[-1]
            oldest_id = oldest_tweet.get('id', '')

            # Try different pagination parameter names
            pagination_attempts = [
                {'userName': username, 'max_id': str(int(oldest_id) - 1)},  # Subtract 1 to avoid duplicate
                {'userName': username, 'before': oldest_id},
                {'userName': username, 'until': oldest_id},
                {'userName': username, 'older_than': oldest_id}
            ]

            success = False
            for attempt_params in pagination_attempts:
                try:
                    response = requests.get(url, headers=headers, params=attempt_params, timeout=30)
                    data = response.json()

                    if data.get('status') == 'success':
                        new_tweets = data.get('data', {}).get('tweets', [])

                        # Check if we got new tweets
                        existing_ids = [t.get('id') for t in all_tweets]
                        unique_new = [t for t in new_tweets if t.get('id') not in existing_ids]

                        if unique_new:
                            print(f"SUCCESS with {list(attempt_params.keys())[-1]}: got {len(unique_new)} new tweets")
                            all_tweets.extend(unique_new)
                            success = True
                            break
                        else:
                            print(f"No new tweets with {list(attempt_params.keys())[-1]}")
                    else:
                        print(f"API error with {list(attempt_params.keys())[-1]}: {data.get('msg')}")

                except Exception as e:
                    print(f"Exception with {list(attempt_params.keys())[-1]}: {e}")

            if not success:
                print("No pagination method worked, stopping")
                break

    if page == 1:
        # First page
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            data = response.json()

            if data.get('status') == 'success':
                tweets = data.get('data', {}).get('tweets', [])
                all_tweets.extend(tweets)
                print(f"Got {len(tweets)} tweets in first batch")
            else:
                print(f"API Error: {data.get('msg', 'Unknown error')}")
                break
        except Exception as e:
            print(f"Error: {e}")
            break

    # Rate limiting
    if page < max_pages:
        time.sleep(5)

# Summary
print(f"\n=== SUMMARY ===")
print(f"Total tweets collected: {len(all_tweets)}")

if all_tweets:
    # Count originals
    originals = 0
    for tweet in all_tweets:
        text = tweet.get('text', '')
        if not text.startswith('RT @') and not text.startswith('@'):
            originals += 1

    print(f"Original posts: {originals}")
    print(f"Date range: {all_tweets[-1].get('createdAt')} to {all_tweets[0].get('createdAt')}")

    # Save to test file
    with open('pagination_test_result.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_tweets': len(all_tweets),
            'original_posts': originals,
            'tweets': all_tweets
        }, f, indent=2, ensure_ascii=False)

    print("Results saved to pagination_test_result.json")