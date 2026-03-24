# import time
# from datetime import datetime
# from requests.exceptions import ReadTimeout, ConnectionError
# from config import logger
# from app import keep_alive
# from bot_handlers import get_bot

# # تشغيل خادم Flask
# keep_alive()

# # الحصول على كائن البوت
# bot, user_stats, total_photos_received = get_bot()

# print("=" * 50)
# print("🤖 بوت كاميرا الذكاء الاصطناعي (5 صور فقط)")
# print(f"⏰ تم التشغيل في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
# print("🔒 نظام التشفير: Base64 (بسيط)")
# print("=" * 50)

# # تشغيل البوت
# while True:
#     try:
#         logger.info("Starting bot polling...")
#         bot.infinity_polling(timeout=60, long_polling_timeout=60)
#     except (ReadTimeout, ConnectionError) as e:
#         logger.warning(f"Connection error: {e}. Retrying in 5 seconds...")
#         time.sleep(5)
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")
#         time.sleep(10)
import time
from datetime import datetime
from requests.exceptions import ReadTimeout, ConnectionError
from config import logger, DEVELOPER_CHAT_ID
from app import keep_alive
from bot_handlers import get_bot, setup_bot_commands, update_bot_profile

# تشغيل خادم Flask
keep_alive()

# الحصول على كائن البوت
bot, user_stats, total_photos_received = get_bot()

# إعداد قائمة الأوامر في مربع الكتابة
setup_bot_commands()

# تحديث الملف الشخصي للبوت (الاسم والوصف)
update_bot_profile()

print("=" * 50)
print("🤖 بوت كاميرا الذكاء الاصطناعي (5 صور فقط)")
print(f"⏰ تم التشغيل في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"👥 عدد المستخدمين الحالي: {len(user_stats)}")
print("🔒 نظام التشفير: Base64 (بسيط)")
print("📋 قائمة الأوامر: تم تفعيلها")
print("=" * 50)

# إرسال إشعار للمطور بأن البوت يعمل
try:
    bot.send_message(DEVELOPER_CHAT_ID, f"✅ *البوت يعمل الآن!*\n\n👥 عدد المستخدمين: {len(user_stats)}\n🖼️ إجمالي الصور: {total_photos_received}\n\n📋 الأوامر متاحة في القائمة", parse_mode="Markdown")
except:
    pass

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
