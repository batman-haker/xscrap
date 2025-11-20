"""
Test TwitterAPI.io endpoints to understand available parameters
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('TWITTER_API_KEY')
headers = {"x-api-key": api_key}
base_url = "https://api.twitterapi.io"

# Test 1: Try different endpoints
endpoints_to_test = [
    "/twitter/user/last_tweets",
    "/twitter/timeline/user",
    "/v1/timeline",
    "/v1/user/tweets"
]

username = "stocktavia"

for endpoint in endpoints_to_test:
    print(f"\n=== Testing {endpoint} ===")
    try:
        # Try different parameter combinations
        test_params = [
            {'userName': username},
            {'userName': username, 'count': 50},
            {'userName': username, 'count': 100},
            {'username': username},
            {'user': username},
            {'screen_name': username},
        ]

        for params in test_params:
            try:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success':
                        tweets = data.get('data', {}).get('tweets', [])
                        print(f"✅ SUCCESS with params {params}: Got {len(tweets)} tweets")

                        # Show first tweet as sample
                        if tweets:
                            first_tweet = tweets[0]
                            print(f"   Sample tweet: {first_tweet.get('text', '')[:100]}...")
                        break
                    else:
                        print(f"❌ API Error with params {params}: {data.get('msg', 'Unknown')}")
                elif response.status_code == 404:
                    print(f"🔍 Endpoint not found with params {params}")
                else:
                    print(f"❌ HTTP {response.status_code} with params {params}")
            except Exception as e:
                print(f"❌ Exception with params {params}: {e}")

    except Exception as e:
        print(f"❌ Failed to test {endpoint}: {e}")

# Test 2: Check what parameters are available in successful response
print(f"\n=== Detailed Analysis of Working Endpoint ===")
url = f"{base_url}/twitter/user/last_tweets"
params = {'userName': username}

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    data = response.json()

    if data.get('status') == 'success':
        tweets = data.get('data', {}).get('tweets', [])
        print(f"Total tweets returned: {len(tweets)}")

        # Analyze tweet structure
        if tweets:
            print("\n--- Sample Tweet Structure ---")
            sample = tweets[0]
            print(json.dumps(sample, indent=2)[:500] + "...")

            # Check if there are pagination hints
            print("\n--- Pagination Info ---")
            data_section = data.get('data', {})
            print(f"Data keys: {list(data_section.keys())}")

    else:
        print(f"API Error: {data}")

except Exception as e:
    print(f"Error: {e}")