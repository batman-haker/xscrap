#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def get_user_following(username):
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json'
    }

    try:
        # First get user ID
        user_url = f"https://api.twitter.com/2/users/by/username/{username}"
        user_response = requests.get(user_url, headers=headers)

        if user_response.status_code == 200:
            user_data = user_response.json()
            user_id = user_data['data']['id']
            print(f"User ID for @{username}: {user_id}")

            # Get following list
            following_url = f"https://api.twitter.com/2/users/{user_id}/following"
            params = {
                'max_results': 100,  # Max allowed per request
                'user.fields': 'name,username,description,public_metrics,verified'
            }

            following_response = requests.get(following_url, headers=headers, params=params)

            if following_response.status_code == 200:
                following_data = following_response.json()
                following_users = following_data.get('data', [])

                print(f"\n{'='*80}")
                print(f"ACCOUNTS FOLLOWED BY @{username.upper()}")
                print(f"{'='*80}")
                print(f"Total following: {len(following_users)}")
                print(f"{'='*80}")

                for i, user in enumerate(following_users, 1):
                    name = user.get('name', 'Unknown')
                    username_followed = user.get('username', 'unknown')
                    description = user.get('description', 'No description')
                    followers = user.get('public_metrics', {}).get('followers_count', 0)
                    verified = user.get('verified', False)

                    # Truncate description for display
                    if len(description) > 100:
                        description = description[:100] + "..."

                    verify_mark = " ✓" if verified else ""

                    print(f"{i:3d}. @{username_followed}{verify_mark}")
                    print(f"     {name}")
                    print(f"     {description}")
                    print(f"     Followers: {followers:,}")
                    print()

                # Save to file
                output_file = f'data/raw/{username}_following.json'
                os.makedirs('data/raw', exist_ok=True)

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'user': username,
                        'user_id': user_id,
                        'following_count': len(following_users),
                        'following': following_users,
                        'retrieved_at': following_data.get('meta', {})
                    }, f, indent=2, ensure_ascii=False)

                print(f"✓ Data saved to {output_file}")
                return True

            else:
                print(f"Following API Error {following_response.status_code}: {following_response.text}")
                return False

        else:
            print(f"User API Error {user_response.status_code}: {user_response.text}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    username = "Tomasz16066938"
    success = get_user_following(username)

    if success:
        print(f"\nSUCCESS: Retrieved following list for @{username}")
    else:
        print(f"\nFAILED: Could not get following list for @{username}")
        print("Note: Following list endpoint requires elevated Twitter API access")