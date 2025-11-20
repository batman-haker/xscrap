#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def extract_tweet_texts(json_file):
    """Wydobywa teksty tweetów do głębokiej analizy"""

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tweets = data.get('tweets', [])

    print("="*80)
    print("PEŁNE TEKSTY TWEETÓW T_SMOLAREK DO ANALIZY")
    print("="*80)
    print(f"\nLiczba tweetów: {len(tweets)}\n")

    output_file = f"data/analysis/smolarek_tweets_full_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    os.makedirs('data/analysis', exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("="*80 + "\n")
        out.write("WSZYSTKIE TWEETY T_SMOLAREK - PEŁNA TREŚĆ\n")
        out.write("="*80 + "\n\n")

        for i, tweet in enumerate(tweets, 1):
            text = tweet.get('text', '')
            date = tweet.get('createdAt', 'N/A')
            likes = tweet.get('likeCount', 0)
            views = tweet.get('viewCount', 0)
            retweets = tweet.get('retweetCount', 0)

            tweet_info = f"\n[TWEET {i}]\n"
            tweet_info += f"Data: {date}\n"
            tweet_info += f"Wyświetlenia: {views:,} | Polubienia: {likes:,} | Retweety: {retweets:,}\n"
            tweet_info += f"{'-'*80}\n"
            tweet_info += f"{text}\n"
            tweet_info += f"{'='*80}\n"

            out.write(tweet_info)

            # Also print to console (limited)
            if i <= 5:  # Print first 5 to console
                print(tweet_info)

        if len(tweets) > 5:
            print(f"\n... (pozostałe {len(tweets) - 5} tweetów zapisane w pliku)\n")

    print(f"\n✓ Pełne teksty zapisane do: {output_file}")
    return output_file

if __name__ == "__main__":
    import glob

    files = glob.glob('data/raw/smolarek_all_tweets_*.json')
    if files:
        json_file = max(files)
        print(f"Analizuję: {json_file}\n")
        extract_tweet_texts(json_file)
    else:
        print("Nie znaleziono pliku z tweetami!")
