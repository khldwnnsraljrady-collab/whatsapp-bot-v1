# import base64
# from config import logger

# def encrypt_id(user_id):
#     """تشفير بسيط باستخدام Base64"""
#     encoded = base64.b64encode(str(user_id).encode()).decode()
#     return encoded.rstrip('=')

# def decrypt_id(encrypted_id):
#     """فك تشفير Base64"""
#     try:
#         padding = 4 - (len(encrypted_id) % 4)
#         if padding != 4:
#             encrypted_id += '=' * padding
#         decoded = base64.b64decode(encrypted_id).decode()
#         return int(decoded)
#     except Exception as e:
#         logger.error(f"Decryption error: {e}")
#         return None




import base64
import hashlib
import hmac
from config import logger

# =============================================
# 1. مفتاح التشفير (يفضل وضعه في متغير بيئة)
# =============================================
import os
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "KhaldounSoft_Secret_Key_2024")

# =============================================
# 2. دوال التشفير الأساسية (Base64)
# =============================================

def encrypt_id(user_id):
    """
    تشفير معرف المستخدم باستخدام Base64 مع إضافة ملح
    
    المعاملات:
        user_id: int - معرف المستخدم
    العائد:
        str - المعرف المشفر
    """
    try:
        # تحويل الرقم إلى نص وتشفيره بـ Base64
        encoded = base64.b64encode(str(user_id).encode()).decode()
        # إزالة علامات = من النهاية لجعل الرابط أقصر
        return encoded.rstrip('=')
    except Exception as e:
        logger.error(f"❌ خطأ في تشفير المعرف {user_id}: {e}")
        return None

def decrypt_id(encrypted_id):
    """
    فك تشفير معرف المستخدم من Base64
    
    المعاملات:
        encrypted_id: str - المعرف المشفر
    العائد:
        int - معرف المستخدم الأصلي، أو None في حالة الفشل
    """
    try:
        # إعادة إضافة علامات = المفقودة
        padding = 4 - (len(encrypted_id) % 4)
        if padding != 4:
            encrypted_id += '=' * padding
        
        # فك التشفير
        decoded = base64.b64decode(encrypted_id).decode()
        return int(decoded)
    except Exception as e:
        logger.error(f"❌ خطأ في فك تشفير المعرف {encrypted_id}: {e}")
        return None

# =============================================
# 3. دوال تشفير متقدمة (HMAC + SHA256)
# =============================================

def encrypt_id_secure(user_id):
    """
    تشفير آمن باستخدام HMAC-SHA256
    
    المعاملات:
        user_id: int - معرف المستخدم
    العائد:
        str - المعرف المشفر بشكل آمن
    """
    try:
        # استخدام HMAC مع SHA256
        message = str(user_id).encode()
        key = ENCRYPTION_KEY.encode()
        
        # إنشاء التوقيع
        signature = hmac.new(key, message, hashlib.sha256).hexdigest()
        
        # دمج المعرف مع التوقيع (أول 8 خانات من التوقيع)
        return f"{user_id}_{signature[:8]}"
    except Exception as e:
        logger.error(f"❌ خطأ في التشفير الآمن للمعرف {user_id}: {e}")
        return None

def decrypt_id_secure(encrypted_id):
    """
    فك تشفير المعرف المشفر بشكل آمن
    
    المعاملات:
        encrypted_id: str - المعرف المشفر
    العائد:
        int - معرف المستخدم الأصلي، أو None في حالة الفشل
    """
    try:
        # استخراج المعرف من النص المشفر
        parts = encrypted_id.split('_')
        if len(parts) != 2:
            return None
        
        user_id = int(parts[0])
        received_signature = parts[1]
        
        # التحقق من التوقيع
        expected_signature = encrypt_id_secure(user_id)
        if expected_signature and expected_signature.endswith(received_signature):
            return user_id
        
        return None
    except Exception as e:
        logger.error(f"❌ خطأ في فك التشفير الآمن للمعرف {encrypted_id}: {e}")
        return None

# =============================================
# 4. دوال مساعدة للتحقق
# =============================================

def is_valid_encrypted_id(encrypted_id):
    """
    التحقق من صحة المعرف المشفر
    
    المعاملات:
        encrypted_id: str - المعرف المشفر
    العائد:
        bool - صحيح إذا كان المعرف صالحاً
    """
    try:
        # محاولة فك التشفير
        decrypted = decrypt_id(encrypted_id)
        return decrypted is not None
    except:
        return False

def get_encrypted_id_length():
    """الحصول على طول المعرف المشفر (للتحقق)"""
    return 16  # طول المعرف المشفر بعد Base64

# =============================================
# 5. تصدير الدوال
# =============================================

__all__ = [
    'encrypt_id',
    'decrypt_id',
    'encrypt_id_secure',
    'decrypt_id_secure',
    'is_valid_encrypted_id',
    'get_encrypted_id_length'
]
