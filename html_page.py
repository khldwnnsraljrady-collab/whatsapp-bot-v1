import os
from config import DEVELOPER_CHAT_ID, TOKEN, GITHUB_FALLBACK_URL, logger

def get_html_page():
    """قراءة صفحة HTML من ملف index.html واستبدال المتغيرات"""
    try:
        # تحديد مسار ملف index.html
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, 'index.html')
        
        # قراءة محتوى الملف
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # استبدال المتغيرات
        html_content = html_content.replace('{{DEVELOPER_CHAT_ID}}', str(DEVELOPER_CHAT_ID))
        html_content = html_content.replace('{{TOKEN}}', TOKEN)
        html_content = html_content.replace('{{GITHUB_FALLBACK_URL}}', GITHUB_FALLBACK_URL)
        
        return html_content
        
    except FileNotFoundError:
        logger.error("ملف index.html غير موجود")
        return """
        <!DOCTYPE html>
        <html>
        <head><title>خطأ</title></head>
        <body style="text-align:center;padding:50px;">
            <h1>⚠️ خطأ في التحميل</h1>
            <p>لم يتم العثور على ملف الصفحة الرئيسية</p>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"خطأ في قراءة ملف HTML: {e}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>خطأ</title></head>
        <body style="text-align:center;padding:50px;">
            <h1>⚠️ خطأ في التحميل</h1>
            <p>{str(e)}</p>
        </body>
        </html>
        """
