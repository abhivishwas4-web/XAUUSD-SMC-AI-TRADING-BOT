import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]


def load_config(config_path: str = None) -> dict:
    """Load YAML config and environment variables (via .env) and return as dict."""
    if config_path is None:
        config_path = BASE_DIR / 'config' / 'config.yaml'
    load_dotenv(BASE_DIR / '.env')
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    # do not load secrets here; they come from environment at runtime
    cfg['env'] = {
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
        'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID'),
        'TWELVE_DATA_API_KEY': os.getenv('TWELVE_DATA_API_KEY')
    }
    return cfg
