#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

def single_api_test():
    api_key = os.getenv('TWITTER_API_KEY')

    print("=== Single API Request Test ===")
    print(f"API Key: {api_key}")
    print(f"User ID from .env: {os.getenv('TWITTER_USER_ID')}")

    # Wait a bit to avoid rapid requests
    print("Waiting 2 seconds to avoid rate limiting...")
    time.sleep(2)

    # Try the simplest possible request
    headers = {'x-api-key': api_key}

    # Try different approaches based on TwitterAPI.io docs
    test_urls = [
        "https://api.twitterapi.io/v1/users/by/username/MarekLangalis",
        "https://api.twitterapi.io/v2/users/by/username/MarekLangalis",
        "https://api.twitterapi.io/users/by/username/MarekLangalis",
        "https://api.twitterapi.io/v1/tweets/search?query=from:MarekLangalis&max_results=1",
        "https://api.twitterapi.io/v2/tweets/search?query=from:MarekLangalis&max_results=1"
    ]

    for url in test_urls:
        print(f"\nTesting: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")

            if response.status_code == 200:
                print("SUCCESS! This endpoint works!")
                data = response.json()
                print(f"Data: {json.dumps(data, indent=2)[:500]}...")
                break
            elif response.status_code == 429:
                print("Rate limit exceeded - need to add credits to account")
            elif response.status_code == 401:
                print("Unauthorized - check API key")
            elif response.status_code == 402:
                print("Payment required - need to add credits")

            # Wait between requests
            time.sleep(1)

        except Exception as e:
            print(f"Error: {e}")

    # Check account status if possible
    print(f"\nTo check your account status and add credits:")
    print(f"Visit: https://twitterapi.io/dashboard")
    print(f"Your API key: {api_key}")

if __name__ == "__main__":
    single_api_test()