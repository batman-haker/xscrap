#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_different_endpoints():
    api_key = os.getenv('TWITTER_API_KEY')

    print("=== TwitterAPI.io Endpoint Discovery ===")
    print(f"API Key: {api_key[:15]}..." if api_key else "No API key")

    if not api_key:
        print("ERROR: No API key found")
        return

    # Different possible header formats
    headers_variants = [
        {'x-api-key': api_key},
        {'Authorization': f'Bearer {api_key}'},
        {'Authorization': f'Token {api_key}'},
        {'api-key': api_key},
        {'X-API-KEY': api_key}
    ]

    base_urls = [
        "https://api.twitterapi.io",
        "https://twitterapi.io/api",
        "https://api.twitterapi.io/v1",
        "https://api.twitterapi.io/v2"
    ]

    endpoints = [
        "/twitter/user",
        "/user",
        "/users/by/username/MarekLangalis",
        "/twitter/timeline",
        "/timeline",
        "/tweets/search",
        "/search",
        "/users/search"
    ]

    # Test root endpoint first
    for base_url in base_urls:
        print(f"\n--- Testing base: {base_url} ---")
        for headers in headers_variants:
            try:
                response = requests.get(base_url, headers=headers, timeout=10)
                print(f"Base URL {base_url} with {list(headers.keys())[0]}: {response.status_code}")
                if response.status_code in [200, 401, 403]:  # These indicate the endpoint exists
                    print(f"Response: {response.text[:200]}")
                    break
            except:
                continue

    # Try specific endpoints
    working_base = "https://api.twitterapi.io"
    working_headers = {'x-api-key': api_key}

    print(f"\n--- Testing specific endpoints with {working_base} ---")

    for endpoint in endpoints:
        url = working_base + endpoint
        try:
            # Try GET first
            response = requests.get(url, headers=working_headers, timeout=10)
            print(f"GET {endpoint}: {response.status_code}")

            if response.status_code in [200, 400, 401, 422]:  # Valid responses
                print(f"  Response: {response.text[:200]}...")

            # If it's a search/user endpoint, try with parameters
            if 'user' in endpoint or 'search' in endpoint:
                params = {'q': 'MarekLangalis'} if 'search' in endpoint else {'username': 'MarekLangalis'}
                param_response = requests.get(url, headers=working_headers, params=params, timeout=10)
                print(f"GET {endpoint} with params: {param_response.status_code}")
                if param_response.status_code in [200, 400, 401, 422]:
                    print(f"  Param response: {param_response.text[:200]}...")

        except Exception as e:
            print(f"GET {endpoint}: ERROR - {e}")

    # Try timeline-specific approaches
    print(f"\n--- Testing timeline approaches ---")

    timeline_endpoints = [
        f"/tweets/user/MarekLangalis",
        f"/user/MarekLangalis/tweets",
        f"/twitter/timeline?screen_name=MarekLangalis",
        f"/timeline?user=MarekLangalis",
        f"/users/MarekLangalis/timeline"
    ]

    for endpoint in timeline_endpoints:
        try:
            url = working_base + endpoint
            response = requests.get(url, headers=working_headers, timeout=10)
            print(f"Timeline {endpoint}: {response.status_code}")
            if response.status_code in [200, 400, 401, 422]:
                print(f"  Timeline response: {response.text[:200]}...")
        except Exception as e:
            print(f"Timeline {endpoint}: ERROR - {e}")

if __name__ == "__main__":
    test_different_endpoints()