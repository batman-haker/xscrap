#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serena Integration for Live Markdown Preview
Integration with Serena for real-time Markdown file monitoring and preview
"""

import os
import json
import shutil
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any
import logging

class SerenaIntegration:
    """Integration with Serena for live Markdown preview"""

    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.docs_dir = os.path.join(self.project_root, "docs")
        self.live_dir = os.path.join(self.project_root, "live_preview")

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize directories
        self._setup_directories()

        # Serena config
        self.serena_config = {
            "watch_dirs": [self.docs_dir, self.live_dir, "reports"],
            "auto_reload": True,
            "theme": "github",
            "port": 3000
        }

    def _setup_directories(self):
        """Setup required directories for Serena integration"""
        os.makedirs(self.docs_dir, exist_ok=True)
        os.makedirs(self.live_dir, exist_ok=True)

        # Create .gitkeep files
        for directory in [self.docs_dir, self.live_dir]:
            gitkeep_path = os.path.join(directory, ".gitkeep")
            if not os.path.exists(gitkeep_path):
                with open(gitkeep_path, 'w') as f:
                    f.write("")

    def create_project_documentation(self) -> str:
        """Create comprehensive project documentation"""

        doc_content = f"""# X Financial Analysis Project

## 🎯 Overview
Real-time financial sentiment analysis from X (Twitter) data with AI-powered insights.

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚀 Quick Start

### Launch Dashboard
```bash
streamlit run dashboard.py
```
**Access:** http://localhost:8501

### Run Analysis
```bash
python main.py
```

### Run with Serena Preview
```bash
# Start Serena for live Markdown preview
serena --watch docs reports live_preview --port 3000

# In another terminal
python main.py
```

## 📊 Project Structure

```
x-financial-analyzer/
├── 📊 dashboard.py          # Streamlit web interface
├── 🚀 main.py              # Main application
├── 📁 src/                 # Source code
│   ├── scraper.py          # TwitterAPI.io integration
│   ├── analyzer.py         # Sentiment analysis
│   ├── claude_client.py    # Claude AI integration
│   └── reporter.py         # Markdown report generator
├── ⚙️ config/              # Configuration files
│   ├── accounts.json       # Monitored accounts
│   ├── keywords.json       # Analysis keywords
│   └── categories.json     # Categories & rules
├── 📊 data/               # Data storage
├── 📄 reports/            # Generated reports
├── 📚 docs/               # Documentation
└── 👀 live_preview/       # Live preview files
```

## 🔗 API Configuration

### TwitterAPI.io Setup
```env
TWITTER_API_KEY={os.getenv('TWITTER_API_KEY', 'your_api_key')}
TWITTER_USER_ID={os.getenv('TWITTER_USER_ID', 'your_user_id')}
```

**Rate Limits:** Free tier = 1 request every 5 seconds

### Claude AI Setup
```env
CLAUDE_API_KEY=your_claude_api_key
```

## 📈 Monitored Accounts

### Polish Finance
- **@MarekLangalis** - Entrepreneur, economist ⭐ HIGH PRIORITY

### Cryptocurrency
- @elonmusk - Tesla/X CEO
- @VitalikButerin - Ethereum
- @michael_saylor - MicroStrategy

### US Economy
- @WSJ - Wall Street Journal
- @nytimes - Economic News
- @cnbc - CNBC

### Geopolitics
- @Reuters - Global news
- @ForeignAffairs - Foreign policy

## 🎛️ Dashboard Features

- 📊 **Real-time sentiment monitoring**
- 🎯 **Manual data collection triggers**
- 📈 **Interactive charts (Plotly)**
- 🔍 **Category-wise analysis**
- 🔥 **Top influential tweets**
- ⚙️ **System health monitoring**

## 🤖 AI Analysis Pipeline

1. **Data Collection** → TwitterAPI.io scraping
2. **Sentiment Analysis** → Financial lexicon + TextBlob
3. **AI Insights** → Claude API integration
4. **Report Generation** → Markdown + Streamlit
5. **Live Preview** → Serena integration

## 📊 Analysis Categories

| Category | Weight | Risk Level | Accounts |
|----------|---------|------------|----------|
| Polish Finance | 1.5 | Medium | @MarekLangalis |
| Cryptocurrency | 1.2 | High | @elonmusk, @VitalikButerin |
| US Economy | 1.5 | Medium | @WSJ, @nytimes |
| Geopolitics | 1.4 | High | @Reuters |

## ⚡ Usage Examples

### Quick Analysis
```bash
# Collect last 4 hours of data
python main.py --mode collect --hours 4

# Run sentiment analysis
python main.py --mode analyze

# Generate report
python main.py --mode report
```

### Automated Monitoring
```bash
# Start scheduler (runs in background)
python main.py --mode scheduler
```

**Schedule:**
- Every 1 hour: Tweet collection
- Every 4 hours: Full analysis
- Daily 8:00 AM: Daily report
- Sunday 9:00 AM: Weekly report

## 🔧 Troubleshooting

### Rate Limiting
- Free tier: 1 request per 5 seconds
- Upgrade at https://twitterapi.io/dashboard

### Unicode Issues (Windows)
- Use `py` instead of `python`
- Check system locale settings

### API Errors
```bash
# Validate configuration
python main.py --validate
```

## 📊 Sample Output

**Latest Analysis:**
- **Total Tweets:** {self._get_latest_tweet_count()}
- **Overall Sentiment:** {self._get_latest_sentiment()}
- **Top Category:** {self._get_top_category()}
- **Risk Level:** Medium

## 🔄 Live Updates

This document is automatically updated when:
- New analysis completes
- Configuration changes
- System status updates

**Last Update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*Generated by X Financial Analyzer*
*Dashboard: http://localhost:8501*
*Serena Preview: http://localhost:3000*
"""

        doc_path = os.path.join(self.docs_dir, "README.md")

        try:
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)

            self.logger.info(f"Project documentation created: {doc_path}")
            return doc_path

        except Exception as e:
            self.logger.error(f"Failed to create documentation: {e}")
            return ""

    def _get_latest_tweet_count(self) -> int:
        """Get latest tweet count from data"""
        try:
            import glob
            data_files = glob.glob(os.path.join(self.project_root, "data/processed/analysis_*.json"))
            if data_files:
                latest_file = max(data_files, key=os.path.getctime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('total_tweets', 0)
        except:
            pass
        return 0

    def _get_latest_sentiment(self) -> str:
        """Get latest overall sentiment"""
        try:
            import glob
            data_files = glob.glob(os.path.join(self.project_root, "data/processed/analysis_*.json"))
            if data_files:
                latest_file = max(data_files, key=os.path.getctime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('overall_sentiment', {}).get('sentiment_label', 'Unknown')
        except:
            pass
        return "Unknown"

    def _get_top_category(self) -> str:
        """Get category with most activity"""
        try:
            import glob
            data_files = glob.glob(os.path.join(self.project_root, "data/processed/analysis_*.json"))
            if data_files:
                latest_file = max(data_files, key=os.path.getctime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    categories = data.get('categories', {})
                    if categories:
                        top_cat = max(categories.keys(), key=lambda k: categories[k].get('tweet_count', 0))
                        return top_cat.replace('_', ' ').title()
        except:
            pass
        return "Unknown"

    def create_live_analysis_file(self, analysis_data: Dict[str, Any]) -> str:
        """Create live analysis file for Serena preview"""

        timestamp = datetime.now()

        live_content = f"""# 📊 Live Analysis - {timestamp.strftime('%H:%M:%S')}

## 🎯 Current Market Sentiment

**Overall:** {analysis_data.get('overall_sentiment', {}).get('sentiment_label', 'Unknown')}
**Score:** {analysis_data.get('overall_sentiment', {}).get('overall_score', 0.0):.2f}
**Confidence:** {analysis_data.get('overall_sentiment', {}).get('confidence', 0.0):.1%}
**Total Tweets:** {analysis_data.get('total_tweets', 0)}

## 📈 Category Breakdown

"""

        categories = analysis_data.get('categories', {})
        for category, data in categories.items():
            if data.get('tweet_count', 0) > 0:
                sentiment_label = data.get('sentiment_label', 'Unknown')
                sentiment_score = data.get('weighted_sentiment', 0.0)
                tweet_count = data.get('tweet_count', 0)

                # Emoji based on sentiment
                if sentiment_score > 0.3:
                    emoji = "🚀"
                elif sentiment_score > 0:
                    emoji = "📈"
                elif sentiment_score < -0.3:
                    emoji = "📉"
                else:
                    emoji = "➡️"

                live_content += f"### {emoji} {category.replace('_', ' ').title()}\n"
                live_content += f"- **Sentiment:** {sentiment_label} ({sentiment_score:+.2f})\n"
                live_content += f"- **Tweets:** {tweet_count}\n"
                live_content += f"- **Activity:** {'High' if tweet_count > 10 else 'Medium' if tweet_count > 5 else 'Low'}\n\n"

        # Top tweets
        top_tweets = analysis_data.get('top_tweets', [])[:3]
        if top_tweets:
            live_content += "## 🔥 Most Influential Tweets\n\n"
            for i, tweet in enumerate(top_tweets, 1):
                user = tweet.get('user', {})
                username = user.get('screen_name', 'Unknown')
                text = tweet.get('text', '')[:150] + '...' if len(tweet.get('text', '')) > 150 else tweet.get('text', '')
                impact = tweet.get('impact_score', 0.0)

                live_content += f"**{i}. @{username}** (Impact: {impact:.2f})\n"
                live_content += f"> {text}\n\n"

        # Insights
        insights = analysis_data.get('insights', [])
        if insights:
            live_content += "## 🔍 Key Insights\n\n"
            for insight in insights[:5]:
                live_content += f"- {insight}\n"
            live_content += "\n"

        live_content += f"""
---
**Last Update:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Auto-refresh:** Every 30 seconds
**Dashboard:** http://localhost:8501
"""

        live_path = os.path.join(self.live_dir, "current_analysis.md")

        try:
            with open(live_path, 'w', encoding='utf-8') as f:
                f.write(live_content)

            self.logger.info(f"Live analysis updated: {live_path}")
            return live_path

        except Exception as e:
            self.logger.error(f"Failed to create live analysis: {e}")
            return ""

    def start_serena_server(self) -> bool:
        """Start Serena server for live preview"""
        try:
            # Check if Serena is installed
            result = subprocess.run(['serena', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.warning("Serena not found. Install with: npm install -g @serena-org/serena")
                return False

            # Start Serena server
            cmd = [
                'serena',
                '--watch', self.docs_dir,
                '--watch', self.live_dir,
                '--watch', 'reports',
                '--port', str(self.serena_config['port']),
                '--auto-reload'
            ]

            subprocess.Popen(cmd, cwd=self.project_root)
            self.logger.info(f"Serena server started on port {self.serena_config['port']}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start Serena server: {e}")
            return False

    def get_serena_url(self) -> str:
        """Get Serena server URL"""
        return f"http://localhost:{self.serena_config['port']}"

    def create_serena_config(self) -> str:
        """Create Serena configuration file"""
        config_path = os.path.join(self.project_root, "serena.config.json")

        config = {
            "title": "X Financial Analyzer - Live Preview",
            "description": "Real-time financial sentiment analysis",
            "theme": "github",
            "port": self.serena_config['port'],
            "watch": [
                "docs",
                "live_preview",
                "reports"
            ],
            "autoReload": True,
            "plugins": ["mermaid", "katex"]
        }

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            self.logger.info(f"Serena config created: {config_path}")
            return config_path

        except Exception as e:
            self.logger.error(f"Failed to create Serena config: {e}")
            return ""


if __name__ == "__main__":
    # Initialize Serena integration
    serena = SerenaIntegration()

    # Create project documentation
    doc_path = serena.create_project_documentation()
    print(f"Project documentation: {doc_path}")

    # Create Serena config
    config_path = serena.create_serena_config()
    print(f"Serena config: {config_path}")

    print(f"\nTo start live preview:")
    print(f"1. Install Serena: npm install -g @serena-org/serena")
    print(f"2. Run: serena --config serena.config.json")
    print(f"3. Open: {serena.get_serena_url()}")