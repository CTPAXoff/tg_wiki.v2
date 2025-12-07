import logging
import os
from datetime import datetime

def setup_logging():
    """Setup logging to file with ERROR and WARNING levels only"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"telegram_parser_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "WARNING")),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
        ]
    )
    
    # Suppress debug logs from telethon
    telethon_logger = logging.getLogger("telethon")
    telethon_logger.setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

logger = setup_logging()