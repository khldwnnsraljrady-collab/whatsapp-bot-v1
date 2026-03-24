import time
from datetime import datetime
from requests.exceptions import ReadTimeout, ConnectionError
from config import logger, DEVELOPER_CHAT_ID, TOKEN
from app import keep_alive
from bot_handlers import get_bot, setup_bot_commands, update_bot_profile
import telebot

# تشغيل خادم Flask
keep_alive()

# الحصول على كائن البوت
bot, user_stats, total_photos_received = get_bot()

# مسح أي Webhook قديم
try:
    bot.delete_webhook()
    logger.info("Webhook deleted successfully")
    time.sleep(2)
except Exception as e:
    logger.warning(f"Failed to delete webhook: {e}")

# إعداد الأوامر
setup_bot_commands()

# تحديث الملف الشخصي
update_bot_profile()

print("=" * 50)
print("🤖 بوت الكاميرا الذكية")
print(f"⏰ التشغيل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"👥 المستخدمين: {len(user_stats)}")
print(f"🖼️ الصور: {total_photos_received}")
print("=" * 50)

# إشعار للمطور
try:
    bot.send_message(DEVELOPER_CHAT_ID, f"✅ *البوت يعمل*\n\n👥 {len(user_stats)} مستخدم\n🖼️ {total_photos_received} صورة", parse_mode="Markdown")
except:
    pass

# تشغيل البوت
while True:
    try:
        logger.info("Starting bot polling...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"Polling error: {e}")
        time.sleep(10)
