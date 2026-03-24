import time
from datetime import datetime
from requests.exceptions import ReadTimeout, ConnectionError
from config import logger
from app import keep_alive
from bot_handlers import get_bot

# تشغيل خادم Flask
keep_alive()

# الحصول على كائن البوت
bot, user_stats, total_photos_received = get_bot()

print("=" * 50)
print("🤖 بوت كاميرا الذكاء الاصطناعي (5 صور فقط)")
print(f"⏰ تم التشغيل في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🔒 نظام التشفير: Base64 (بسيط)")
print("=" * 50)

# تشغيل البوت
while True:
    try:
        logger.info("Starting bot polling...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except (ReadTimeout, ConnectionError) as e:
        logger.warning(f"Connection error: {e}. Retrying in 5 seconds...")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        time.sleep(10)
