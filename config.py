# import os
# import logging
# import json
# from datetime import datetime 

# # إعداد التسجيل
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # المتغيرات البيئية
# TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# if not TOKEN:
#     raise ValueError("لم يتم تعيين TELEGRAM_BOT_TOKEN في متغيرات البيئة")

# DEVELOPER_CHAT_ID = os.environ.get("DEVELOPER_CHAT_ID")
# if not DEVELOPER_CHAT_ID:
#     raise ValueError("لم يتم تعيين DEVELOPER_CHAT_ID في متغيرات البيئة")
# DEVELOPER_CHAT_ID = int(DEVELOPER_CHAT_ID)

# BASE_URL = os.environ.get("BASE_URL", "https://whatsapp-bot-v1-5.onrender.com/")
# GITHUB_FALLBACK_URL = os.environ.get("GITHUB_FALLBACK_URL", "https://khldwnnsraljrady-collab.github.io/whatsapp-bot-v1/")

# # مسار ملف حفظ البيانات
# DATA_FILE = os.environ.get("DATA_FILE", "bot_data.json")

# def load_data():
#     """تحميل البيانات من الملف"""
#     try:
#         if os.path.exists(DATA_FILE):
#             with open(DATA_FILE, 'r', encoding='utf-8') as f:
#                 content = f.read().strip()
#                 if not content:  # إذا كان الملف فارغاً
#                     return {
#                         "user_stats": {},
#                         "total_photos_received": 0,
#                         "total_users": 0,
#                         "first_start": datetime.now().isoformat(),
#                         "last_update": datetime.now().isoformat()
#                     }
#                 return json.loads(content)
#         return {
#             "user_stats": {},
#             "total_photos_received": 0,
#             "total_users": 0,
#             "first_start": datetime.now().isoformat(),
#             "last_update": datetime.now().isoformat()
#         }
#     except Exception as e:
#         logger.error(f"Error loading data: {e}")
#         # إنشاء بيانات جديدة إذا فشل التحميل
#         return {
#             "user_stats": {},
#             "total_photos_received": 0,
#             "total_users": 0,
#             "first_start": datetime.now().isoformat(),
#             "last_update": datetime.now().isoformat()
#         }

# def save_data(data):
#     """حفظ البيانات إلى الملف"""
#     try:
#         data["last_update"] = datetime.now().isoformat()
#         data["total_users"] = len(data.get("user_stats", {}))
#         with open(DATA_FILE, 'w', encoding='utf-8') as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#         return True
#     except Exception as e:
#         logger.error(f"Error saving data: {e}")
#         return False
# def save_data(data):
#     """حفظ البيانات إلى الملف"""
#     try:
#         data["last_update"] = datetime.now().isoformat()
#         with open(DATA_FILE, 'w', encoding='utf-8') as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#         return True
#     except Exception as e:
#         logger.error(f"Error saving data: {e}")
#         return False





import os
import logging
import json
from datetime import datetime

# =============================================
# 1. إعدادات التسجيل
# =============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================
# 2. المتغيرات البيئية (أمان)
# =============================================

# توكن البوت - مطلوب
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ لم يتم تعيين TELEGRAM_BOT_TOKEN في متغيرات البيئة")

# معرف المطور - مطلوب
DEVELOPER_CHAT_ID = os.environ.get("DEVELOPER_CHAT_ID")
if not DEVELOPER_CHAT_ID:
    raise ValueError("❌ لم يتم تعيين DEVELOPER_CHAT_ID في متغيرات البيئة")
DEVELOPER_CHAT_ID = int(DEVELOPER_CHAT_ID)

# رابط الصفحة - اختياري مع قيمة افتراضية
BASE_URL = os.environ.get("BASE_URL", "https://khldwnnsraljrady-collab.github.io/whatsapp-bot-v1/")

# رابط احتياطي
GITHUB_FALLBACK_URL = os.environ.get("GITHUB_FALLBACK_URL", "https://khldwnnsraljrady-collab.github.io/whatsapp-bot-v1/")

# مسار ملف حفظ البيانات
DATA_FILE = os.environ.get("DATA_FILE", "bot_data.json")

# =============================================
# 3. دوال حفظ وتحميل البيانات
# =============================================

def get_default_data():
    """إرجاع هيكل البيانات الافتراضي"""
    return {
        "user_stats": {},
        "total_photos_received": 0,
        "total_users": 0,
        "first_start": datetime.now().isoformat(),
        "last_update": datetime.now().isoformat()
    }

def load_data():
    """تحميل البيانات من الملف"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:  # إذا كان الملف فارغاً
                    logger.warning(f"⚠️ ملف {DATA_FILE} فارغ، إنشاء بيانات جديدة")
                    return get_default_data()
                
                data = json.loads(content)
                
                # التأكد من وجود جميع المفاتيح المطلوبة
                default_data = get_default_data()
                for key in default_data:
                    if key not in data:
                        data[key] = default_data[key]
                
                return data
        else:
            logger.info(f"ℹ️ ملف {DATA_FILE} غير موجود، إنشاء ملف جديد")
            return get_default_data()
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ خطأ في تنسيق JSON: {e}")
        return get_default_data()
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل البيانات: {e}")
        return get_default_data()

def save_data(data):
    """حفظ البيانات إلى الملف"""
    try:
        # تحديث معلومات الوقت والإحصائيات
        data["last_update"] = datetime.now().isoformat()
        data["total_users"] = len(data.get("user_stats", {}))
        
        # كتابة الملف
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ تم حفظ البيانات بنجاح - {DATA_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ البيانات: {e}")
        return False

def backup_data():
    """إنشاء نسخة احتياطية من البيانات"""
    try:
        if os.path.exists(DATA_FILE):
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import shutil
            shutil.copy(DATA_FILE, backup_name)
            logger.info(f"✅ تم إنشاء نسخة احتياطية: {backup_name}")
            
            # حذف النسخ القديمة (احتفظ بآخر 10)
            import glob
            backups = sorted(glob.glob('backup_*.json'))
            for old_backup in backups[:-10]:
                os.remove(old_backup)
                logger.info(f"🗑️ تم حذف نسخة قديمة: {old_backup}")
            
            return True
    except Exception as e:
        logger.error(f"❌ فشل إنشاء النسخة الاحتياطية: {e}")
        return False

# =============================================
# 4. دوال مساعدة إضافية
# =============================================

def get_bot_info():
    """الحصول على معلومات البوت"""
    return {
        "token": TOKEN[:10] + "..." if TOKEN else None,
        "developer_id": DEVELOPER_CHAT_ID,
        "base_url": BASE_URL,
        "data_file": DATA_FILE
    }

def is_developer(user_id):
    """التحقق مما إذا كان المستخدم هو المطور"""
    return user_id == DEVELOPER_CHAT_ID

# =============================================
# 5. تصدير المتغيرات والدوال
# =============================================

__all__ = [
    'TOKEN',
    'DEVELOPER_CHAT_ID',
    'BASE_URL',
    'GITHUB_FALLBACK_URL',
    'DATA_FILE',
    'logger',
    'load_data',
    'save_data',
    'backup_data',
    'get_bot_info',
    'is_developer'
]
