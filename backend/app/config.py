import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AES_SECRET_KEY: str = os.getenv("AES_SECRET_KEY", "default-secret-key-32-chars-long")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./telegram_parser.db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")
    
    # SQLite settings
    SQLITE_BUSY_TIMEOUT: int = 5000
    
    # Telegram settings
    TELETHON_API_ID: int = int(os.getenv("TELETHON_API_ID", "0"))
    TELETHON_API_HASH: str = os.getenv("TELETHON_API_HASH", "")
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0

config = Config()