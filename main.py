import os
import threading
from flask import Flask
import telebot
import yt_dlp
from PIL import Image, ImageEnhance

# Render-এর ওয়েব সার্ভিস সচল রাখার সার্ভার
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# টেলিগ্রাম বট সেটআপ
BOT_TOKEN = "8653912427:AAEIPhMgZgHFWPGZzIpt_nkfobeXbDhojfs"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message, 
        "স্বাগতম!\n\n"
        "📥 যেকোনো ভিডিও লিঙ্ক (FB, YT, TikTok, Insta, Pinterest) পাঠান, ডাউনলোড ফাইল পেয়ে যাবেন।\n"
        "🖼️ অথবা কোনো ঘোলা ছবি পাঠান, পরিষ্কার (Enhance) করে দেওয়া হবে।"
    )

# লিঙ্ক ডাউনলোডার (yt-dlp)
@bot.message_handler(func=lambda m: m.text and m.text.startswith(('http://', 'https://')))
def handle_link(message):
    url = message.text.strip()
    status = bot.reply_to(message, "⏳ প্রসেসিং শুরু হয়েছে...")
    
    file_path = f"video_{message.chat.id}.mp4"
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': file_path,
        'max_filesize': 48 * 1024 * 1024
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        bot.edit_message_text("📤 ফাইল পাঠানো হচ্ছে...", message.chat.id, status.message_id)
        with open(file_path, 'rb') as f:
            bot.send_video(message.chat.id, f, caption="✅ ডাউনলোড সম্পন্ন!")
            
        if os.path.exists(file_path):
            os.remove(file_path)
        bot.delete_message(message.chat.id, status.message_id)
    except Exception:
        bot.edit_message_text("❌ ফাইল ডাউনলোড করা সম্ভব হয়নি। লিঙ্কটি পাবলিক কি না চেক করুন।", message.chat.id, status.message_id)

# ইমেজ এনহ্যান্সার (Pillow)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    status = bot.reply_to(message, "✨ ছবি পরিষ্কার করা হচ্ছে...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        in_path = f"raw_{message.chat.id}.jpg"
        out_path = f"clean_{message.chat.id}.jpg"
        
        with open(in_path, 'wb') as f:
            f.write(downloaded)
            
        img = Image.open(in_path)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        img = ImageEnhance.Contrast(img).enhance(1.15)
        img.save(out_path, quality=95)
        
        with open(out_path, 'rb') as f:
            bot.send_photo(message.chat.id, f, caption="✨ পরিষ্কার করা ছবি:")
            
        os.remove(in_path)
        os.remove(out_path)
        bot.delete_message(message.chat.id, status.message_id)
    except Exception:
        bot.edit_message_text("❌ ছবি প্রসেস করতে ব্যর্থ হয়েছে।", message.chat.id, status.message_id)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.infinity_polling()
