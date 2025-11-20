#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime

def prepare_demo_data():
    """Prepare demo data for fund manager analysis"""

    # Load sample tweets
    with open('data/raw/sample_categorized_tweets.json', 'r', encoding='utf-8') as f:
        sample_data = json.load(f)

    # Convert to comprehensive format
    comprehensive_data = {
        "timestamp": datetime.now().isoformat(),
        "collection_summary": {
            "total_accounts": 12,
            "total_tweets": sum(len(tweets) for tweets in sample_data.values()),
            "categories": len(sample_data),
            "tweets_per_category": {cat: len(tweets) for cat, tweets in sample_data.items()}
        },
        "tweets_by_category": sample_data
    }

    # Save as comprehensive data
    os.makedirs('data/raw', exist_ok=True)
    with open('data/raw/comprehensive_tweets_current.json', 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, indent=2, ensure_ascii=False)

    print("Demo data prepared for fund manager analysis")
    return comprehensive_data

if __name__ == "__main__":
    prepare_demo_data()