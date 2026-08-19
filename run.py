run.py

from src.utils.config import load_config

if __name__ == "__main__":
    cfg = load_config()
    print("XAUUSD-SMC-AI-TRADING-BOT: configuration loaded for provider=", cfg.get('provider'))
