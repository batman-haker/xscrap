"""
SYNTEZA - Author Analysis Module
Collects and analyzes comprehensive tweet data for deep author insights.
"""
import json
import requests
import time
from datetime import datetime
import os
from typing import List, Dict, Any

class SyntezaCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twitterapi.io"
        self.headers = {"x-api-key": api_key}
        self.rate_limit_delay = 5  # seconds between requests

    def collect_author_tweets(self, username: str, count: int = 50) -> List[Dict[str, Any]]:
        """Collect last N ORIGINAL tweets from author for SYNTEZA analysis using working TwitterAPI.io endpoint"""
        print(f"[SYNTEZA] Collecting up to {count} ORIGINAL tweets from @{username}...")

        all_tweets = []
        original_posts_count = 0
        max_iterations = 10  # Prevent infinite loops
        iteration = 0

        while original_posts_count < count and iteration < max_iterations:
            iteration += 1
            print(f"[BATCH {iteration}] Fetching more tweets... (have {original_posts_count}/{count} originals)")

            # Use the working endpoint from scraper.py with pagination
            url = f"{self.base_url}/twitter/user/last_tweets"
            params = {
                'userName': username,
                'count': 100,  # Try to get more tweets per request
                'include_rts': 'false',  # Exclude retweets at API level if supported
            }

            # Add pagination if we have tweets already (try to get older ones)
            if all_tweets:
                # Use the oldest tweet ID for pagination
                oldest_tweet = min(all_tweets, key=lambda t: t.get('id', ''))
                params['max_id'] = oldest_tweet.get('id')

            try:
                time.sleep(self.rate_limit_delay)  # Rate limit before request
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()

                response_data = response.json()

                # Handle TwitterAPI.io response format
                if response_data.get('status') != 'success':
                    print(f"[ERROR] API error for {username}: {response_data.get('msg', 'Unknown error')}")
                    break

                tweets_data = response_data.get('data', {}).get('tweets', [])
                if not isinstance(tweets_data, list) or len(tweets_data) == 0:
                    print(f"[INFO] No more tweets available")
                    break

                # Process tweets from this batch
                batch_originals = 0
                for tweet in tweets_data:
                    # Skip if we already have this tweet (by ID)
                    tweet_id = tweet.get('id', '')
                    if any(t.get('id') == tweet_id for t in all_tweets):
                        continue

                    tweet_text = tweet.get('text', '')

                    # FILTER 1: Skip retweets (start with "RT @")
                    if tweet_text.startswith('RT @'):
                        continue

                    # FILTER 2: Skip replies (start with "@username")
                    if tweet_text.startswith('@'):
                        continue

                    # FILTER 3: Skip tweets that are just links (very short with only t.co)
                    if len(tweet_text.strip()) < 20 and 't.co/' in tweet_text:
                        continue

                    # This is an original post - add it
                    author = tweet.get('author', {})
                    all_tweets.append({
                        'id': tweet_id,
                        'text': tweet_text,
                        'text_length': len(tweet_text),
                        'created_at': tweet.get('createdAt', ''),
                        'author_info': {
                            'screen_name': author.get('userName', ''),
                            'name': author.get('name', ''),
                            'followers_count': author.get('followers', 0)
                        },
                        'public_metrics': {
                            'retweet_count': tweet.get('retweetCount', 0),
                            'favorite_count': tweet.get('likeCount', 0),
                            'reply_count': tweet.get('replyCount', 0),
                            'view_count': tweet.get('viewCount', 0)
                        },
                        'is_original_post': True,
                        'author': f"@{username}",
                        'collected_at': datetime.now().isoformat()
                    })
                    batch_originals += 1
                    original_posts_count += 1

                    # Stop if we have enough
                    if original_posts_count >= count:
                        break

                print(f"[BATCH {iteration}] Found {batch_originals} originals from {len(tweets_data)} tweets")

                # If this batch had very few originals, we might be hitting older tweets with same pattern
                if batch_originals == 0:
                    print(f"[INFO] No new original tweets in this batch, stopping")
                    break

            except Exception as e:
                print(f"[ERROR] Error in batch {iteration}: {e}")
                break

        print(f"[SUCCESS] Collected {len(all_tweets)} ORIGINAL tweets from @{username} after {iteration} batches")
        return all_tweets[:count]  # Return exactly requested count

    def save_author_data(self, username: str, tweets: List[Dict[str, Any]]) -> str:
        """Save author tweets to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_username = username.replace('@', '')
        filename = f"synteza_{clean_username}_{timestamp}.json"
        filepath = os.path.join("data", "synteza", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        author_data = {
            'metadata': {
                'author': username,
                'collected_at': datetime.now().isoformat(),
                'total_tweets': len(tweets),
                'collection_purpose': 'SYNTEZA_ANALYSIS'
            },
            'tweets': tweets,
            'analysis_ready': True
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(author_data, f, indent=2, ensure_ascii=False)

        print(f"[SAVED] Author data saved: {filepath}")
        return filepath

def main():
    """Test collection for @stocktavia"""
    # Load API key from environment
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv('TWITTER_API_KEY')
    if not api_key:
        print("[ERROR] Missing TWITTER_API_KEY in environment")
        return

    collector = SyntezaCollector(api_key)

    # Collect @stocktavia tweets
    username = "stocktavia"
    tweets = collector.collect_author_tweets(username, count=50)

    if tweets:
        filepath = collector.save_author_data(f"@{username}", tweets)
        print(f"\n[SYNTEZA] Data ready for analysis:")
        print(f"[FILE] {filepath}")
        print(f"[COUNT] Tweets collected: {len(tweets)}")
    else:
        print("[ERROR] No tweets collected")

if __name__ == "__main__":
    main()