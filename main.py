#!/usr/bin/env python3
"""
X Financial Analysis - Main Application
Automated financial sentiment analysis from X (Twitter) data
"""

import os
import sys
import json
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Optional

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper import DataCollector
from src.analyzer import DataProcessor
from src.claude_client import ClaudeAnalyst
from src.reporter import MarkdownReporter
from src.utils import ensure_directories, setup_logging, health_check, validate_api_keys


class FinancialAnalyzer:
    """Main application orchestrator"""

    def __init__(self):
        # Setup environment
        ensure_directories()
        self.logger = setup_logging()

        # Initialize components
        try:
            self.data_collector = DataCollector()
            self.data_processor = DataProcessor()
            self.claude_analyst = ClaudeAnalyst()
            self.reporter = MarkdownReporter()
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            sys.exit(1)

        self.logger.info("Financial Analyzer initialized successfully")

    def validate_setup(self) -> bool:
        """Validate system setup before running"""
        self.logger.info("Validating system setup...")

        # Check API keys
        api_keys = validate_api_keys()
        missing_keys = [key for key, valid in api_keys.items() if not valid]

        if missing_keys:
            self.logger.error(f"Missing API keys: {missing_keys}")
            self.logger.error("Please configure your .env file with required API keys")
            return False

        # Run health check
        health = health_check()
        if health['health_score'] < 0.8:
            self.logger.warning(f"System health score: {health['health_score']:.1%}")
            self.logger.warning("Some components may not work correctly")

        self.logger.info("System validation completed")
        return True

    def run_collection_cycle(self, hours_back: int = 4) -> Optional[str]:
        """Run a complete data collection and analysis cycle"""
        self.logger.info(f"Starting collection cycle for last {hours_back} hours")

        try:
            # Step 1: Collect tweets
            self.logger.info("Step 1: Collecting tweets...")
            raw_data_file = self.data_collector.collect_and_save(hours_back)

            if not raw_data_file:
                self.logger.error("Failed to collect tweet data")
                return None

            # Step 2: Process and analyze data
            self.logger.info("Step 2: Processing and analyzing data...")
            processed_data_file = self.data_processor.load_and_process(raw_data_file)

            if not processed_data_file:
                self.logger.error("Failed to process tweet data")
                return None

            # Load processed data for reporting
            with open(processed_data_file, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)

            # Step 3: Generate Claude analysis
            self.logger.info("Step 3: Generating AI insights...")
            claude_analysis = self.claude_analyst.analyze_market_sentiment(processed_data)

            # Step 4: Generate executive summary
            self.logger.info("Step 4: Creating executive summary...")
            executive_summary = self.claude_analyst.generate_executive_summary(
                processed_data, claude_analysis
            )

            # Step 5: Generate report
            self.logger.info("Step 5: Generating report...")
            report_content = self.reporter.generate_daily_report(
                processed_data, claude_analysis, executive_summary
            )

            report_file = self.reporter.save_report(report_content, 'daily')

            if report_file:
                self.logger.info(f"Collection cycle completed successfully. Report: {report_file}")
                return report_file
            else:
                self.logger.error("Failed to save report")
                return None

        except Exception as e:
            self.logger.error(f"Error in collection cycle: {e}")
            return None

    def run_sentiment_analysis(self) -> None:
        """Run sentiment analysis on latest data"""
        self.logger.info("Running sentiment analysis...")

        try:
            # Find latest raw data
            import glob
            raw_files = glob.glob('data/raw/tweets_*.json')

            if not raw_files:
                self.logger.warning("No raw data files found for analysis")
                return

            latest_raw_file = max(raw_files, key=os.path.getctime)
            self.logger.info(f"Analyzing data from: {latest_raw_file}")

            # Process the data
            processed_data_file = self.data_processor.load_and_process(latest_raw_file)

            if processed_data_file:
                self.logger.info(f"Sentiment analysis completed: {processed_data_file}")
            else:
                self.logger.error("Sentiment analysis failed")

        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {e}")

    def generate_daily_report(self) -> None:
        """Generate daily report from latest processed data"""
        self.logger.info("Generating daily report...")

        try:
            # Find latest processed data
            import glob
            processed_files = glob.glob('data/processed/analysis_*.json')

            if not processed_files:
                self.logger.warning("No processed data files found for reporting")
                return

            latest_processed_file = max(processed_files, key=os.path.getctime)
            self.logger.info(f"Generating report from: {latest_processed_file}")

            # Load processed data
            with open(latest_processed_file, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)

            # Generate Claude analysis
            claude_analysis = self.claude_analyst.analyze_market_sentiment(processed_data)

            # Generate executive summary
            executive_summary = self.claude_analyst.generate_executive_summary(
                processed_data, claude_analysis
            )

            # Generate report
            report_content = self.reporter.generate_daily_report(
                processed_data, claude_analysis, executive_summary
            )

            report_file = self.reporter.save_report(report_content, 'daily')

            if report_file:
                self.logger.info(f"Daily report generated: {report_file}")
            else:
                self.logger.error("Failed to generate daily report")

        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")

    def generate_weekly_report(self) -> None:
        """Generate weekly summary report"""
        self.logger.info("Generating weekly report...")

        try:
            # Find daily reports from the last week
            import glob
            daily_reports = glob.glob('reports/daily/raport_daily_*.md')

            # Filter reports from last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            recent_reports = []

            for report_file in daily_reports:
                file_time = datetime.fromtimestamp(os.path.getctime(report_file))
                if file_time > week_ago:
                    recent_reports.append(report_file)

            if not recent_reports:
                self.logger.warning("No daily reports found for weekly summary")
                return

            # Generate weekly report
            weekly_content = self.reporter.generate_weekly_report(recent_reports)
            weekly_file = self.reporter.save_report(weekly_content, 'weekly')

            if weekly_file:
                self.logger.info(f"Weekly report generated: {weekly_file}")
            else:
                self.logger.error("Failed to generate weekly report")

        except Exception as e:
            self.logger.error(f"Error generating weekly report: {e}")

    def setup_scheduler(self) -> None:
        """Setup automated scheduling"""
        self.logger.info("Setting up automated scheduler...")

        # Schedule according to the plan:
        # - Every 1 hour: Collect new tweets
        # - Every 4 hours: Run sentiment analysis
        # - Daily at 8:00: Generate daily report
        # - Weekly on Sundays: Generate weekly report

        # Hourly tweet collection
        schedule.every().hour.do(lambda: self.data_collector.collect_and_save(1))

        # Every 4 hours: Full analysis cycle
        schedule.every(4).hours.do(lambda: self.run_collection_cycle(4))

        # Daily report at 8:00 AM
        schedule.every().day.at("08:00").do(self.generate_daily_report)

        # Weekly report on Sundays at 9:00 AM
        schedule.every().sunday.at("09:00").do(self.generate_weekly_report)

        self.logger.info("Scheduler configured with the following jobs:")
        self.logger.info("- Hourly: Tweet collection")
        self.logger.info("- Every 4 hours: Full analysis cycle")
        self.logger.info("- Daily 8:00 AM: Daily report")
        self.logger.info("- Sunday 9:00 AM: Weekly report")

    def run_scheduler(self) -> None:
        """Run the automated scheduler"""
        self.logger.info("Starting automated scheduler...")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")

    def run_manual_cycle(self) -> None:
        """Run a manual collection and analysis cycle"""
        self.logger.info("Running manual analysis cycle...")

        report_file = self.run_collection_cycle()

        if report_file:
            print(f"\n✅ Analysis completed successfully!")
            print(f"📊 Report saved to: {report_file}")
            print(f"\n📈 To view the report:")
            print(f"   Open: {os.path.abspath(report_file)}")
        else:
            print("\n❌ Analysis failed. Check logs for details.")


def main():
    """Main application entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='X Financial Analysis Tool')
    parser.add_argument('--mode', choices=['manual', 'scheduler', 'collect', 'analyze', 'report'],
                       default='manual', help='Run mode')
    parser.add_argument('--hours', type=int, default=4,
                       help='Hours back to collect data (default: 4)')
    parser.add_argument('--validate', action='store_true',
                       help='Validate setup and exit')

    args = parser.parse_args()

    # Initialize analyzer
    try:
        analyzer = FinancialAnalyzer()
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        sys.exit(1)

    # Validate setup
    if not analyzer.validate_setup():
        print("[ERROR] System validation failed")
        sys.exit(1)

    if args.validate:
        print("[SUCCESS] System validation passed")
        sys.exit(0)

    # Run based on mode
    if args.mode == 'manual':
        analyzer.run_manual_cycle()

    elif args.mode == 'scheduler':
        analyzer.setup_scheduler()
        analyzer.run_scheduler()

    elif args.mode == 'collect':
        print(f"Collecting tweets for last {args.hours} hours...")
        raw_file = analyzer.data_collector.collect_and_save(args.hours)
        if raw_file:
            print(f"✅ Data collected: {raw_file}")
        else:
            print("❌ Data collection failed")

    elif args.mode == 'analyze':
        analyzer.run_sentiment_analysis()

    elif args.mode == 'report':
        analyzer.generate_daily_report()


if __name__ == "__main__":
    main()