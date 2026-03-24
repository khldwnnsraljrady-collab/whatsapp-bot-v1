import os
import logging
import json
from datetime import datetime

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# المتغيرات البيئية
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("لم يتم تعيين TELEGRAM_BOT_TOKEN في متغيرات البيئة")

DEVELOPER_CHAT_ID = os.environ.get("DEVELOPER_CHAT_ID")
if not DEVELOPER_CHAT_ID:
    raise ValueError("لم يتم تعيين DEVELOPER_CHAT_ID في متغيرات البيئة")
DEVELOPER_CHAT_ID = int(DEVELOPER_CHAT_ID)

BASE_URL = os.environ.get("BASE_URL", "https://whatsapp-bot-v1-5.onrender.com/")
GITHUB_FALLBACK_URL = os.environ.get("GITHUB_FALLBACK_URL", "https://khldwnnsraljrady-collab.github.io/whatsapp-bot-v1/")

# مسار ملف حفظ البيانات
DATA_FILE = "bot_data.json"

def load_data():
    """تحميل البيانات من الملف"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    # التأكد من وجود جميع الحقول المطلوبة
                    if "user_stats" not in data:
                        data["user_stats"] = {}
                    if "total_photos_received" not in data:
                        data["total_photos_received"] = 0
                    if "first_start" not in data:
                        data["first_start"] = datetime.now().isoformat()
                    if "last_update" not in data:
                        data["last_update"] = datetime.now().isoformat()
                    return data
        # إذا كان الملف غير موجود أو فارغاً
        return {
            "user_stats": {},
            "total_photos_received": 0,
            "first_start": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return {
            "user_stats": {},
            "total_photos_received": 0,
            "first_start": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }

def save_data(data):
    """حفظ البيانات إلى الملف"""
    try:
        data["last_update"] = datetime.now().isoformat()
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Data saved successfully - Users: {len(data.get('user_stats', {}))}")
        return True
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        return False
