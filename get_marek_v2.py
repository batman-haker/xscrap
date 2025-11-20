#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def get_marek_tweet_v2():
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json'
    }

    # Get MarekLangalis tweets
    user_url = "https://api.twitter.com/2/users/by/username/MarekLangalis"

    try:
        user_response = requests.get(user_url, headers=headers)

        if user_response.status_code == 200:
            user_data = user_response.json()
            user_id = user_data['data']['id']

            # Get recent tweets
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                'max_results': 1,
                'tweet.fields': 'created_at,public_metrics,text,lang'
            }

            tweets_response = requests.get(tweets_url, headers=headers, params=params)

            if tweets_response.status_code == 200:
                tweets_data = tweets_response.json()
                tweets = tweets_data.get('data', [])

                if tweets:
                    tweet = tweets[0]

                    # Format for our application
                    formatted_tweet = {
                        'id': tweet['id'],
                        'text': tweet['text'],
                        'created_at': tweet['created_at'],
                        'user': {
                            'screen_name': 'MarekLangalis',
                            'name': 'Marek Łangalis',
                            'followers_count': 8500  # approximate
                        },
                        'retweet_count': tweet['public_metrics']['retweet_count'],
                        'favorite_count': tweet['public_metrics']['like_count'],
                        'reply_count': tweet['public_metrics']['reply_count'],
                        'view_count': tweet['public_metrics'].get('impression_count', 0),
                        'lang': tweet.get('lang', 'pl')
                    }

                    print("="*60)
                    print("LATEST TWEET FROM @MarekLangalis (Twitter API v2)")
                    print("="*60)
                    print(f"Text: {tweet['text']}")
                    print(f"Date: {tweet['created_at']}")
                    print(f"Likes: {tweet['public_metrics']['like_count']}")
                    print(f"Retweets: {tweet['public_metrics']['retweet_count']}")
                    print(f"Replies: {tweet['public_metrics']['reply_count']}")
                    print("="*60)

                    # Save for dashboard
                    dashboard_data = {
                        'polish_finance': [formatted_tweet],
                        'cryptocurrency': [],
                        'us_economy': [],
                        'geopolitics': [],
                        'gold_commodities': []
                    }

                    os.makedirs('data/raw', exist_ok=True)
                    with open('data/raw/twitter_v2_data.json', 'w', encoding='utf-8') as f:
                        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)

                    print("✓ Data saved for dashboard!")
                    return True

        print(f"Error: {user_response.status_code}")
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = get_marek_tweet_v2()
    if success:
        print("\n🎉 Ready for dashboard!")
    else:
        print("\n❌ Failed")