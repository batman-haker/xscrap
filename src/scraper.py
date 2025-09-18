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
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })

        # Rate limiting
        self.requests_per_hour = 100  # Free tier limit
        self.request_timestamps = []

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        now = datetime.now()
        # Remove timestamps older than 1 hour
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if now - ts < timedelta(hours=1)
        ]

        if len(self.request_timestamps) >= self.requests_per_hour:
            wait_time = 3600 - (now - self.request_timestamps[0]).total_seconds()
            self.logger.warning(f"Rate limit reached. Waiting {wait_time:.0f} seconds")
            time.sleep(wait_time)
            self.request_timestamps = []

        self.request_timestamps.append(now)

    def get_user_tweets(self, username: str, count: int = 10,
                       since_hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent tweets from a specific user"""
        self._rate_limit_check()

        endpoint = f"{self.base_url}/twitter/timeline"
        params = {
            'screen_name': username,
            'count': count,
            'include_rts': False,
            'exclude_replies': True
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            tweets_data = response.json()
            if not isinstance(tweets_data, list):
                self.logger.error(f"Unexpected response format for {username}")
                return []

            # Filter tweets by time
            since_time = datetime.now() - timedelta(hours=since_hours)
            filtered_tweets = []

            for tweet in tweets_data:
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
                        ]
                    })

            self.logger.info(f"Retrieved {len(filtered_tweets)} tweets from @{username}")
            return filtered_tweets

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching tweets for {username}: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error for {username}: {e}")
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