"""
SYNTEZA Advanced Collector - Using TwitterAPI.io Advanced Search API
Collects comprehensive tweet data with pagination beyond normal limits.
"""
import json
import requests
import time
from datetime import datetime
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class SyntezaAdvancedCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
        self.headers = {"x-api-key": api_key}
        self.rate_limit_delay = 5  # 5 seconds for free tier

    def collect_author_tweets_advanced(self, username: str, count: int = 50) -> List[Dict[str, Any]]:
        """
        Collect tweets from specific user using Advanced Search API with pagination
        """
        print(f"[SYNTEZA ADVANCED] Collecting {count} tweets from @{username}...")

        # Use advanced search query to get tweets from specific user
        # Exclude retweets and replies at query level
        query = f"from:{username} -filter:retweets -filter:replies"

        all_tweets = []
        seen_tweet_ids = set()
        cursor = None
        last_min_id = None
        max_retries = 3
        iteration = 0

        while len(all_tweets) < count:
            iteration += 1
            print(f"[BATCH {iteration}] Fetching tweets... (have {len(all_tweets)}/{count})")

            # Prepare query parameters
            params = {
                "query": query,
                "queryType": "Latest"
            }

            # Add pagination parameters
            if cursor:
                params["cursor"] = cursor
            elif last_min_id:
                # Use max_id for deeper historical search
                params["query"] = f"{query} max_id:{last_min_id}"

            retry_count = 0
            while retry_count < max_retries:
                try:
                    time.sleep(self.rate_limit_delay)  # Rate limiting

                    response = requests.get(self.base_url, headers=self.headers, params=params)
                    response.raise_for_status()

                    data = response.json()

                    # Advanced Search API returns tweets directly (different format than basic API)
                    tweets = data.get("tweets", [])
                    has_next_page = data.get("has_next_page", False)
                    cursor = data.get("next_cursor", None)

                    if not isinstance(tweets, list):
                        print(f"[ERROR] Unexpected response format: {list(data.keys())}")
                        return all_tweets

                    print(f"[BATCH {iteration}] Got {len(tweets)} tweets from API")

                    # Filter out duplicates and process tweets
                    new_tweets = []
                    for tweet in tweets:
                        tweet_id = tweet.get("id")
                        if tweet_id not in seen_tweet_ids:
                            seen_tweet_ids.add(tweet_id)

                            # Additional filtering for original posts
                            tweet_text = tweet.get('text', '')

                            # Check if it's a reply using API fields
                            is_reply = tweet.get('isReply', False)
                            if is_reply:
                                continue

                            # Skip if it's a retweet (backup filter)
                            if tweet_text.startswith('RT @'):
                                continue

                            # Skip if it starts with @ but allow quotes/mentions within text
                            if tweet_text.startswith('@') and is_reply:
                                continue

                            # Process and add tweet
                            processed_tweet = {
                                'id': tweet_id,
                                'text': tweet_text,
                                'text_length': len(tweet_text),
                                'created_at': tweet.get('createdAt', ''),
                                'author_info': {
                                    'screen_name': tweet.get('author', {}).get('username', username),
                                    'name': tweet.get('author', {}).get('name', ''),
                                    'followers_count': tweet.get('author', {}).get('followersCount', 0)
                                },
                                'public_metrics': {
                                    'retweet_count': tweet.get('retweetCount', 0),
                                    'favorite_count': tweet.get('likeCount', 0),
                                    'reply_count': tweet.get('replyCount', 0),
                                    'quote_count': tweet.get('quoteCount', 0),
                                    'view_count': tweet.get('viewCount', 0),
                                    'bookmark_count': tweet.get('bookmarkCount', 0)
                                },
                                'is_original_post': True,
                                'author': f"@{username}",
                                'collected_at': datetime.now().isoformat(),
                                'source': 'advanced_search_api'
                            }

                            new_tweets.append(processed_tweet)
                            all_tweets.append(processed_tweet)

                    print(f"[BATCH {iteration}] Added {len(new_tweets)} unique original tweets")

                    # Update pagination info
                    if new_tweets:
                        last_min_id = new_tweets[-1].get("id")

                    # Check if we should continue
                    if len(all_tweets) >= count:
                        print(f"[SUCCESS] Reached target of {count} tweets")
                        break

                    if not new_tweets and not has_next_page:
                        print(f"[INFO] No more tweets available")
                        break

                    # Continue with next page
                    if not has_next_page and new_tweets:
                        cursor = None  # Reset cursor for max_id pagination

                    break  # Success, exit retry loop

                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        print(f"[ERROR] Failed after {max_retries} attempts: {e}")
                        return all_tweets[:count]

                    if hasattr(response, 'status_code') and response.status_code == 429:
                        print("[RATE LIMIT] Waiting 5 seconds...")
                        time.sleep(5)
                    else:
                        print(f"[RETRY {retry_count}] Error: {e}")
                        time.sleep(2 ** retry_count)

            # If no progress made, stop
            if not new_tweets and not has_next_page:
                break

        final_tweets = all_tweets[:count]  # Return exactly requested count
        print(f"[SUCCESS] Collected {len(final_tweets)} original tweets from @{username}")
        return final_tweets

    def save_author_data(self, username: str, tweets: List[Dict[str, Any]]) -> str:
        """Save author tweets to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_username = username.replace('@', '')
        filename = f"synteza_advanced_{clean_username}_{timestamp}.json"
        filepath = os.path.join("data", "synteza", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        author_data = {
            'metadata': {
                'author': f"@{username}",
                'collected_at': datetime.now().isoformat(),
                'total_tweets': len(tweets),
                'collection_purpose': 'SYNTEZA_ANALYSIS',
                'api_source': 'twitterapi.io_advanced_search',
                'filters_applied': ['no_retweets', 'no_replies', 'original_posts_only']
            },
            'tweets': tweets,
            'analysis_ready': True
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(author_data, f, indent=2, ensure_ascii=False)

        print(f"[SAVED] Author data saved: {filepath}")
        return filepath

def main():
    """Collect tweets from @stocktavia using Advanced Search API"""
    api_key = os.getenv('TWITTER_API_KEY')
    if not api_key:
        print("[ERROR] Missing TWITTER_API_KEY in environment")
        return

    collector = SyntezaAdvancedCollector(api_key)

    # Collect 50 original tweets from naval
    username = "naval"
    tweets = collector.collect_author_tweets_advanced(username, count=50)

    if tweets:
        filepath = collector.save_author_data(username, tweets)
        print(f"\n[SYNTEZA] Advanced collection completed!")
        print(f"[FILE] {filepath}")
        print(f"[COUNT] Original tweets: {len(tweets)}")

        # Show sample with proper encoding
        if tweets:
            try:
                print(f"[SAMPLE] Latest tweet: {tweets[0]['text'][:100]}...")
            except UnicodeEncodeError:
                print(f"[SAMPLE] Latest tweet: [Contains special characters]")
    else:
        print("[ERROR] No tweets collected")

if __name__ == "__main__":
    main()