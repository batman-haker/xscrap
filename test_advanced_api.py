"""
Test Advanced Search API to understand response format
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('TWITTER_API_KEY')
headers = {"x-api-key": api_key}
base_url = "https://api.twitterapi.io/twitter/tweet/advanced_search"

# Test basic query
username = "stocktavia"
query = f"from:{username}"

params = {
    "query": query,
    "queryType": "Latest"
}

print(f"Testing Advanced Search API...")
print(f"URL: {base_url}")
print(f"Query: {query}")
print(f"Headers: {list(headers.keys())}")

try:
    response = requests.get(base_url, headers=headers, params=params, timeout=30)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        print(f"Full response: {json.dumps(data, indent=2)[:500]}...")

        # Check if it follows the expected format
        if 'tweets' in data:
            tweets = data['tweets']
            print(f"Found {len(tweets)} tweets")
            if tweets:
                sample = tweets[0]
                print(f"Sample tweet keys: {list(sample.keys())}")
                print(f"Sample text: {sample.get('text', '')[:100]}...")
        else:
            print("No 'tweets' key in response")

    else:
        print(f"HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"Exception: {e}")

# Test with simpler query
print(f"\n=== Testing simpler query ===")
simple_params = {
    "query": "python",
    "queryType": "Latest"
}

try:
    response = requests.get(base_url, headers=headers, params=simple_params, timeout=30)
    print(f"Simple query status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Simple query response keys: {list(data.keys())}")
        if 'tweets' in data:
            print(f"Simple query found {len(data['tweets'])} tweets")
    else:
        print(f"Simple query error: {response.text[:200]}")

except Exception as e:
    print(f"Simple query exception: {e}")