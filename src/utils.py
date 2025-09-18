import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import glob


def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        'data/raw',
        'data/processed',
        'data/archive',
        'reports/daily',
        'reports/weekly',
        'reports/analysis',
        'logs'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def get_latest_file(pattern: str) -> Optional[str]:
    """Get the latest file matching a pattern"""
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)


def cleanup_old_files(directory: str, days_to_keep: int = 30):
    """Clean up old files in a directory"""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

    for file_path in glob.glob(os.path.join(directory, '*')):
        if os.path.isfile(file_path):
            file_date = datetime.fromtimestamp(os.path.getctime(file_path))
            if file_date < cutoff_date:
                try:
                    os.remove(file_path)
                    print(f"Removed old file: {file_path}")
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")


def load_json_config(file_path: str) -> Dict[str, Any]:
    """Load JSON configuration file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file {file_path}: {e}")
        return {}


def save_json_data(data: Dict[str, Any], file_path: str) -> bool:
    """Save data to JSON file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON data to {file_path}: {e}")
        return False


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """Format timestamp for filenames"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime('%Y%m%d_%H%M%S')


def parse_timestamp_from_filename(filename: str) -> Optional[datetime]:
    """Parse timestamp from filename"""
    try:
        # Extract timestamp pattern YYYYMMDD_HHMMSS from filename
        parts = filename.split('_')
        if len(parts) >= 2:
            date_str = parts[-2]
            time_str = parts[-1].split('.')[0]  # Remove extension
            return datetime.strptime(f"{date_str}_{time_str}", '%Y%m%d_%H%M%S')
    except:
        pass
    return None


def validate_api_keys() -> Dict[str, bool]:
    """Validate that required API keys are present"""
    required_keys = [
        'TWITTER_API_KEY',
        'TWITTER_USER_ID',
        'CLAUDE_API_KEY'
    ]

    validation_results = {}
    for key in required_keys:
        value = os.getenv(key)
        validation_results[key] = bool(value and len(value.strip()) > 0)

    return validation_results


def calculate_file_size(file_path: str) -> str:
    """Calculate and format file size"""
    try:
        size_bytes = os.path.getsize(file_path)
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    except:
        return "Unknown"


def create_backup(source_file: str, backup_dir: str = 'data/archive') -> str:
    """Create a backup of a file"""
    import shutil

    os.makedirs(backup_dir, exist_ok=True)

    timestamp = format_timestamp()
    filename = os.path.basename(source_file)
    name, ext = os.path.splitext(filename)
    backup_filename = f"{name}_{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        shutil.copy2(source_file, backup_path)
        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        return ""


def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging"""
    import platform
    import psutil

    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available,
        'disk_free': psutil.disk_usage('.').free
    }


def health_check() -> Dict[str, Any]:
    """Perform system health check"""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'directories': {},
        'api_keys': {},
        'system': {},
        'files': {}
    }

    # Check directories
    required_dirs = [
        'data/raw', 'data/processed', 'data/archive',
        'reports/daily', 'reports/weekly', 'reports/analysis',
        'config', 'src', 'logs'
    ]

    for directory in required_dirs:
        health_status['directories'][directory] = os.path.exists(directory)

    # Check API keys
    health_status['api_keys'] = validate_api_keys()

    # Check system resources
    try:
        health_status['system'] = get_system_info()
    except:
        health_status['system'] = {'error': 'Unable to get system info'}

    # Check important files
    important_files = [
        'config/accounts.json',
        'config/keywords.json',
        'config/categories.json',
        'src/scraper.py',
        'src/analyzer.py',
        'src/claude_client.py',
        'src/reporter.py'
    ]

    for file_path in important_files:
        health_status['files'][file_path] = os.path.exists(file_path)

    # Overall health score
    total_checks = (
        len(health_status['directories']) +
        len(health_status['api_keys']) +
        len(health_status['files'])
    )

    passed_checks = (
        sum(health_status['directories'].values()) +
        sum(health_status['api_keys'].values()) +
        sum(health_status['files'].values())
    )

    health_status['health_score'] = passed_checks / total_checks if total_checks > 0 else 0.0
    health_status['status'] = 'healthy' if health_status['health_score'] > 0.8 else 'issues_detected'

    return health_status


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Retry function with exponential backoff"""
    import time

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e

            delay = base_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)


def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency amounts"""
    if currency == 'USD':
        return f"${amount:,.2f}"
    elif currency == 'PLN':
        return f"{amount:,.2f} PLN"
    elif currency == 'EUR':
        return f"€{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_percentage(value: float) -> str:
    """Format percentage values"""
    return f"{value:.2%}"


def truncate_string(text: str, max_length: int = 100) -> str:
    """Truncate string with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value"""
    try:
        return numerator / denominator if denominator != 0 else default
    except:
        return default


if __name__ == "__main__":
    # Run health check
    ensure_directories()
    health = health_check()

    print("=== System Health Check ===")
    print(f"Overall Status: {health['status']}")
    print(f"Health Score: {health['health_score']:.1%}")

    print("\nDirectories:")
    for directory, exists in health['directories'].items():
        status = "✓" if exists else "✗"
        print(f"  {status} {directory}")

    print("\nAPI Keys:")
    for key, valid in health['api_keys'].items():
        status = "✓" if valid else "✗"
        print(f"  {status} {key}")

    print("\nFiles:")
    for file_path, exists in health['files'].items():
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")