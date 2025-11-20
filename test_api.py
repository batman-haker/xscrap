#!/usr/bin/env python3
"""
Test script for TwitterAPI.io connection
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_twitter_api():
    """Test connection to TwitterAPI.io"""

    api_key = os.getenv('TWITTER_API_KEY')
    user_id = os.getenv('TWITTER_USER_ID')

    print("=== Twitter API Test ===")
    print(f"API Key: {api_key[:20]}..." if api_key else "API Key: NOT FOUND")
    print(f"User ID: {user_id}")

    if not api_key:
        print("❌ TWITTER_API_KEY not found in .env file")
        return False

    # Test endpoint - get user info for MarekLangalis
    base_url = "https://api.twitterapi.io"

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Try to get user information first
    print("\n--- Testing user lookup for @MarekLangalis ---")

    try:
        # Method 1: Try user lookup
        user_endpoint = f"{base_url}/twitter/user"
        user_params = {'screen_name': 'MarekLangalis'}

        print(f"Requesting: {user_endpoint}")
        print(f"Params: {user_params}")
        print(f"Headers: Authorization: Bearer {api_key[:20]}...")

        response = requests.get(user_endpoint, params=user_params, headers=headers, timeout=30)

        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            user_data = response.json()
            print("✅ User lookup successful!")
            print(f"User data: {json.dumps(user_data, indent=2)}")

            # Now try to get tweets from this user
            print("\n--- Testing timeline for @MarekLangalis ---")
            return test_user_timeline('MarekLangalis', headers)

        else:
            print(f"❌ User lookup failed")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error during user lookup: {e}")
        return False

def test_user_timeline(username, headers):
    """Test getting user timeline"""

    base_url = "https://api.twitterapi.io"
    timeline_endpoint = f"{base_url}/twitter/timeline"

    params = {
        'screen_name': username,
        'count': 1,  # Just 1 tweet as requested
        'include_rts': False,
        'exclude_replies': True
    }

    try:
        print(f"Requesting: {timeline_endpoint}")
        print(f"Params: {params}")

        response = requests.get(timeline_endpoint, params=params, headers=headers, timeout=30)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            tweets_data = response.json()
            print("✅ Timeline request successful!")

            if isinstance(tweets_data, list) and len(tweets_data) > 0:
                tweet = tweets_data[0]
                print(f"\n📄 Latest tweet from @{username}:")
                print(f"Text: {tweet.get('text', tweet.get('full_text', 'No text'))}")
                print(f"Created: {tweet.get('created_at')}")
                print(f"Retweets: {tweet.get('retweet_count', 0)}")
                print(f"Likes: {tweet.get('favorite_count', 0)}")
                return True
            else:
                print("⚠️ No tweets found or empty response")
                print(f"Response: {json.dumps(tweets_data, indent=2)}")
                return False
        else:
            print(f"❌ Timeline request failed")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error during timeline request: {e}")
        return False

def test_alternative_endpoints():
    """Test alternative API endpoints"""

    api_key = os.getenv('TWITTER_API_KEY')
    base_url = "https://api.twitterapi.io"

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    print("\n--- Testing alternative endpoints ---")

    # Try search endpoint
    search_endpoint = f"{base_url}/twitter/search"
    search_params = {
        'q': 'from:MarekLangalis',
        'count': 1,
        'result_type': 'recent'
    }

    try:
        print(f"Trying search: {search_endpoint}")
        response = requests.get(search_endpoint, params=search_params, headers=headers, timeout=30)
        print(f"Search Status Code: {response.status_code}")

        if response.status_code == 200:
            search_data = response.json()
            print("✅ Search successful!")
            print(f"Search results: {json.dumps(search_data, indent=2)[:500]}...")
            return True
        else:
            print(f"❌ Search failed: {response.text}")

    except Exception as e:
        print(f"❌ Search error: {e}")

    return False

if __name__ == "__main__":
    print("Starting TwitterAPI.io connection test...")

    # Test main API
    success = test_twitter_api()

    if not success:
        print("\nTrying alternative endpoints...")
        test_alternative_endpoints()

    print("\n=== Test Complete ===")