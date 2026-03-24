import base64
from config import logger

def encrypt_id(user_id):
    """تشفير بسيط باستخدام Base64"""
    encoded = base64.b64encode(str(user_id).encode()).decode()
    return encoded.rstrip('=')

def decrypt_id(encrypted_id):
    """فك تشفير Base64"""
    try:
        padding = 4 - (len(encrypted_id) % 4)
        if padding != 4:
            encrypted_id += '=' * padding
        decoded = base64.b64decode(encrypted_id).decode()
        return int(decoded)
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        return None
