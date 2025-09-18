import requests
import json
import os
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class TwitterAPIClient:
    """Client for TwitterAPI.io service"""

    def __init__(self):
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.user_id = os.getenv('TWITTER_USER_ID')
        self.base_url = "https://api.twitterapi.io"
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        })

        # Rate limiting for free tier: 1 request every 5 seconds
        self.request_delay = 5  # seconds between requests for free tier
        self.last_request_time = None

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _rate_limit_check(self):
        """Check and enforce rate limiting for free tier (1 request per 5 seconds)"""
        if self.last_request_time is None:
            self.last_request_time = datetime.now()
            return

        now = datetime.now()
        time_since_last = (now - self.last_request_time).total_seconds()

        if time_since_last < self.request_delay:
            wait_time = self.request_delay - time_since_last
            self.logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)

        self.last_request_time = datetime.now()

    def get_user_tweets(self, username: str, count: int = 10,
                       since_hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent tweets from a specific user using TwitterAPI.io"""
        self._rate_limit_check()

        endpoint = f"{self.base_url}/twitter/user/last_tweets"
        params = {
            'userName': username  # TwitterAPI.io uses camelCase
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            response_data = response.json()

            # Handle TwitterAPI.io response format
            if response_data.get('status') != 'success':
                self.logger.error(f"API error for {username}: {response_data.get('msg', 'Unknown error')}")
                return []

            tweets_data = response_data.get('data', {}).get('tweets', [])
            if not isinstance(tweets_data, list):
                self.logger.error(f"Unexpected tweets format for {username}")
                return []

            # Filter tweets by time
            since_time = datetime.now() - timedelta(hours=since_hours)
            filtered_tweets = []

            for tweet in tweets_data:
                # Parse TwitterAPI.io date format: "Thu Sep 18 10:23:47 +0000 2025"
                created_at_str = tweet.get('createdAt', '')
                try:
                    tweet_time = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S %z %Y')
                except ValueError:
                    # Skip if date parsing fails
                    self.logger.warning(f"Could not parse date: {created_at_str}")
                    continue

                if tweet_time.replace(tzinfo=None) > since_time:
                    author = tweet.get('author', {})
                    filtered_tweets.append({
                        'id': tweet.get('id'),
                        'text': tweet.get('text', ''),
                        'created_at': created_at_str,
                        'user': {
                            'screen_name': author.get('userName', ''),
                            'name': author.get('name', ''),
                            'followers_count': author.get('followers', 0)
                        },
                        'retweet_count': tweet.get('retweetCount', 0),
                        'favorite_count': tweet.get('likeCount', 0),
                        'reply_count': tweet.get('replyCount', 0),
                        'view_count': tweet.get('viewCount', 0),
                        'hashtags': [],  # Will be extracted from text if needed
                        'urls': [],     # Will be extracted from text if needed
                        'lang': tweet.get('lang', 'unknown')
                    })

            # Limit to requested count
            if count and len(filtered_tweets) > count:
                filtered_tweets = filtered_tweets[:count]

            self.logger.info(f"Retrieved {len(filtered_tweets)} tweets from @{username}")
            return filtered_tweets

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error fetching tweets for {username}: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error for {username}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error for {username}: {e}")
            return []

    def search_tweets(self, query: str, count: int = 10,
                     since_hours: int = 24) -> List[Dict[str, Any]]:
        """Search for tweets containing specific keywords"""
        self._rate_limit_check()

        endpoint = f"{self.base_url}/twitter/search"
        params = {
            'q': query,
            'count': count,
            'result_type': 'recent',
            'include_entities': True
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            search_data = response.json()
            tweets = search_data.get('statuses', [])

            # Filter and format tweets
            since_time = datetime.now() - timedelta(hours=since_hours)
            filtered_tweets = []

            for tweet in tweets:
                tweet_time = datetime.strptime(
                    tweet.get('created_at', ''),
                    '%a %b %d %H:%M:%S %z %Y'
                )

                if tweet_time.replace(tzinfo=None) > since_time:
                    filtered_tweets.append({
                        'id': tweet.get('id_str'),
                        'text': tweet.get('full_text', tweet.get('text', '')),
                        'created_at': tweet.get('created_at'),
                        'user': {
                            'screen_name': tweet.get('user', {}).get('screen_name'),
                            'name': tweet.get('user', {}).get('name'),
                            'followers_count': tweet.get('user', {}).get('followers_count', 0)
                        },
                        'retweet_count': tweet.get('retweet_count', 0),
                        'favorite_count': tweet.get('favorite_count', 0),
                        'hashtags': [
                            tag.get('text', '')
                            for tag in tweet.get('entities', {}).get('hashtags', [])
                        ],
                        'urls': [
                            url.get('expanded_url', '')
                            for url in tweet.get('entities', {}).get('urls', [])
                        ],
                        'search_query': query
                    })

            self.logger.info(f"Found {len(filtered_tweets)} tweets for query: {query}")
            return filtered_tweets

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching tweets for '{query}': {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error for search '{query}': {e}")
            return []


class DataCollector:
    """Main data collection orchestrator"""

    def __init__(self):
        self.twitter_client = TwitterAPIClient()
        self.accounts_config = self._load_accounts_config()
        self.keywords_config = self._load_keywords_config()

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _load_accounts_config(self) -> Dict[str, Any]:
        """Load accounts configuration"""
        try:
            with open('config/accounts.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error("accounts.json not found")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing accounts.json: {e}")
            return {}

    def _load_keywords_config(self) -> Dict[str, Any]:
        """Load keywords configuration"""
        try:
            with open('config/keywords.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error("keywords.json not found")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing keywords.json: {e}")
            return {}

    def collect_all_tweets(self, hours_back: int = 4) -> Dict[str, List[Dict[str, Any]]]:
        """Collect tweets from all configured accounts"""
        all_tweets = {}

        for category, accounts in self.accounts_config.items():
            category_tweets = []

            for account in accounts:
                username = account['username']
                tweets = self.twitter_client.get_user_tweets(
                    username=username,
                    count=20,
                    since_hours=hours_back
                )

                # Add metadata to tweets
                for tweet in tweets:
                    tweet['account_category'] = category
                    tweet['account_priority'] = account.get('priority', 'medium')
                    tweet['collected_at'] = datetime.now().isoformat()

                category_tweets.extend(tweets)

                # Small delay between requests to be respectful
                time.sleep(1)

            all_tweets[category] = category_tweets
            self.logger.info(f"Collected {len(category_tweets)} tweets for {category}")

        return all_tweets

    def save_raw_data(self, tweets_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """Save raw tweets data to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/raw/tweets_{timestamp}.json"

        os.makedirs('data/raw', exist_ok=True)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tweets_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Raw data saved to {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error saving raw data: {e}")
            return ""

    def collect_and_save(self, hours_back: int = 4) -> str:
        """Collect tweets and save raw data"""
        self.logger.info(f"Starting data collection for last {hours_back} hours")

        tweets_data = self.collect_all_tweets(hours_back)
        filename = self.save_raw_data(tweets_data)

        total_tweets = sum(len(tweets) for tweets in tweets_data.values())
        self.logger.info(f"Collection completed. Total tweets: {total_tweets}")

        return filename


if __name__ == "__main__":
    collector = DataCollector()
    collector.collect_and_save()