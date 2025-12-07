from cryptography.fernet import Fernet
import base64
from typing import Optional
from .config import config
from .logger import logger

class AESEncryption:
    def __init__(self):
        # Ensure key is 32 bytes for AES-256
        key = config.AES_SECRET_KEY[:32].ljust(32, '0')
        self.fernet = Fernet(base64.urlsafe_b64encode(key.encode()))
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

encryption = AESEncryption()