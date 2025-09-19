#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class TweetCacheManager:
    """Intelligent caching system for tweets to save API calls and tokens"""

    def __init__(self, cache_dir="data/cache"):
        self.cache_dir = cache_dir
        self.ensure_cache_dir()

    def ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_tweet_hash(self, username, tweet_text, created_at):
        """Generate unique hash for tweet identification"""
        content = f"{username}:{tweet_text}:{created_at}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def get_user_cache_file(self, username):
        """Get cache file path for specific user"""
        return os.path.join(self.cache_dir, f"{username}_tweets.json")

    def load_user_cache(self, username):
        """Load cached tweets for a user"""
        cache_file = self.get_user_cache_file(username)

        if not os.path.exists(cache_file):
            return {"tweets": [], "last_updated": None}

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache for {username}: {e}")
            return {"tweets": [], "last_updated": None}

    def save_user_cache(self, username, tweets_data):
        """Save tweets to user cache"""
        cache_file = self.get_user_cache_file(username)

        cache_data = {
            "tweets": tweets_data,
            "last_updated": datetime.now().isoformat(),
            "total_tweets": len(tweets_data)
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"[OK] Cached {len(tweets_data)} tweets for @{username}")
        except Exception as e:
            print(f"Error saving cache for {username}: {e}")

    def merge_new_tweets(self, username, new_tweets):
        """Merge new tweets with existing cache, avoiding duplicates"""
        existing_cache = self.load_user_cache(username)
        existing_tweets = existing_cache.get("tweets", [])

        # Create set of existing tweet hashes
        existing_hashes = set()
        for tweet in existing_tweets:
            tweet_hash = self.get_tweet_hash(
                tweet.get('username', ''),
                tweet.get('text', ''),
                tweet.get('created_at', '')
            )
            existing_hashes.add(tweet_hash)

        # Add only new tweets
        merged_tweets = existing_tweets.copy()
        new_count = 0

        for tweet in new_tweets:
            tweet_hash = self.get_tweet_hash(
                tweet.get('username', ''),
                tweet.get('text', ''),
                tweet.get('created_at', '')
            )

            if tweet_hash not in existing_hashes:
                merged_tweets.append(tweet)
                existing_hashes.add(tweet_hash)
                new_count += 1

        # Sort by creation date (newest first)
        merged_tweets.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # Keep only last 100 tweets per user to prevent cache bloat
        merged_tweets = merged_tweets[:100]

        # Save updated cache
        self.save_user_cache(username, merged_tweets)

        print(f"[CACHE] @{username}: {new_count} new tweets added, {len(merged_tweets)} total in cache")
        return merged_tweets, new_count

    def get_cached_tweets_by_category(self, accounts_by_category, max_age_hours=24):
        """Get all cached tweets organized by category"""
        result = {}
        stats = {"total_cached": 0, "total_categories": 0, "cache_hits": 0}

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        for category, usernames in accounts_by_category.items():
            category_tweets = []

            for username in usernames:
                cache_data = self.load_user_cache(username)
                user_tweets = cache_data.get("tweets", [])

                # Filter by age if needed
                fresh_tweets = []
                for tweet in user_tweets:
                    try:
                        tweet_time = datetime.fromisoformat(
                            tweet.get('created_at', '').replace('Z', '+00:00').replace(' +0000', '+00:00')
                        )
                        if tweet_time > cutoff_time:
                            fresh_tweets.append(tweet)
                    except:
                        # If date parsing fails, include the tweet
                        fresh_tweets.append(tweet)

                if fresh_tweets:
                    category_tweets.extend(fresh_tweets[:20])  # Max 20 per user
                    stats["cache_hits"] += 1

            if category_tweets:
                result[category] = category_tweets
                stats["total_cached"] += len(category_tweets)
                stats["total_categories"] += 1

        print(f"[STATS] Cache: {stats['total_cached']} tweets from {stats['cache_hits']} users in {stats['total_categories']} categories")
        return result, stats

    def needs_fresh_data(self, username, max_age_hours=6):
        """Check if user needs fresh data from API"""
        cache_data = self.load_user_cache(username)
        last_updated = cache_data.get("last_updated")

        if not last_updated:
            return True

        try:
            last_update_time = datetime.fromisoformat(last_updated)
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            return last_update_time < cutoff_time
        except:
            return True

    def get_cache_summary(self):
        """Get summary of all cached data"""
        cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('_tweets.json')]

        summary = {
            "total_users": len(cache_files),
            "total_tweets": 0,
            "users": []
        }

        for cache_file in cache_files:
            username = cache_file.replace('_tweets.json', '')
            cache_data = self.load_user_cache(username)

            user_info = {
                "username": username,
                "tweet_count": len(cache_data.get("tweets", [])),
                "last_updated": cache_data.get("last_updated", "Never")
            }

            summary["users"].append(user_info)
            summary["total_tweets"] += user_info["tweet_count"]

        return summary

    def cleanup_old_cache(self, max_age_days=7):
        """Remove tweets older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cleaned_users = 0
        cleaned_tweets = 0

        cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('_tweets.json')]

        for cache_file in cache_files:
            username = cache_file.replace('_tweets.json', '')
            cache_data = self.load_user_cache(username)
            tweets = cache_data.get("tweets", [])

            # Filter out old tweets
            fresh_tweets = []
            for tweet in tweets:
                try:
                    tweet_time = datetime.fromisoformat(
                        tweet.get('created_at', '').replace('Z', '+00:00').replace(' +0000', '+00:00')
                    )
                    if tweet_time > cutoff_time:
                        fresh_tweets.append(tweet)
                    else:
                        cleaned_tweets += 1
                except:
                    # Keep tweets with unparseable dates
                    fresh_tweets.append(tweet)

            if len(fresh_tweets) != len(tweets):
                self.save_user_cache(username, fresh_tweets)
                cleaned_users += 1

        print(f"[CLEANUP] Cleaned {cleaned_tweets} old tweets from {cleaned_users} users")
        return {"users_cleaned": cleaned_users, "tweets_removed": cleaned_tweets}

if __name__ == "__main__":
    # Test the cache manager
    cache = TweetCacheManager()
    summary = cache.get_cache_summary()
    print(f"Cache contains {summary['total_tweets']} tweets from {summary['total_users']} users")