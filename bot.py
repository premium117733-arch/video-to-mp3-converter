import os
import subprocess
import time
import telebot
import imageio_ffmpeg as ffmpeg_lib
from flask import Flask
from threading import Thread

# 🌐 1. Render & UptimeRobot এর জন্য Web Server Setup
app = Flask('')

@app.route('/')
def home():
    return "🤖 Video to MP3 Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()

keep_alive()

# 🔑 2. Telegram Bot Setup
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8965509113:AAFHwWiszGO6cxPjSzxWwFAI5grIyQAi_TY")
bot = telebot.TeleBot(BOT_TOKEN)

# FFmpeg এর জন্য এক্সিকিউটেবল পাথ নেওয়া
FFMPEG_EXE = ffmpeg_lib.get_ffmpeg_exe()

# সব মেসেজের নিচে থাকার ওয়াটারমার্ক/ফুটার
FOOTER = "\n\n⭐ Developed by SAIFUL"

# Start & Help Command
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"👋 স্বাগতম, {user_name}! ✨\n\n"
        "🎬 Video to MP3 Converter Bot-এ আপনাকে স্বাগতম! 🎵\n\n"
        "📌 কিভাবে ব্যবহার করবেন:\n"
        "━ আমাকে যেকোনো Video বা Video Document পাঠান। 📥\n"
        "━ আমি মুহূর্তের মধ্যেই সেটিকে HD MP3 Audio-তে কনভার্ট করে দেব। ⚡\n\n"
        "🚀 শুরু করতে এখনই একটি ভিডিও পাঠান! 🔥"
        f"{FOOTER}"
    )
    bot.reply_to(message, welcome_text)

# Video to MP3 Handler
@bot.message_handler(content_types=['video', 'document'])
def handle_video(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    video_input_path = f"input_{user_id}.mp4"
    audio_output_path = f"output_{user_id}.mp3"
    status_msg = None

    try:
        file_id = None
        if message.content_type == 'video':
            file_id = message.video.file_id
        elif message.content_type == 'document' and message.document.mime_type and message.document.mime_type.startswith('video/'):
            file_id = message.document.file_id
        else:
            return

        status_msg = bot.reply_to(
            message, 
            f"⏳ কাজ শুরু হচ্ছে...\n[▱▱▱▱▱▱▱▱▱▱] 0%{FOOTER}"
        )
        time.sleep(0.5)

        bot.edit_message_text(
            f"📥 ভিডিও ডাউনলোড হচ্ছে...\n[▰▰▰▱▱▱▱▱▱▱] 30%{FOOTER}", 
            chat_id=message.chat.id, 
            message_id=status_msg.message_id
        )

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open(video_input_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.edit_message_text(
            f"⚙️ MP3 এ কনভার্ট করা হচ্ছে...\n[▰▰▰▰▰▰▱▱▱▱] 65%{FOOTER}", 
            chat_id=message.chat.id, 
            message_id=status_msg.message_id
        )

        # FFmpeg দিয়ে অডিও এক্সট্র্যাক্ট
        cmd = f'"{FFMPEG_EXE}" -i "{video_input_path}" -vn -ar 44100 -ac 2 -b:a 192k "{audio_output_path}" -y'
        subprocess.run(cmd, shell=True, check=True)

        bot.edit_message_text(
            f"📤 অডিও ফাইল পাঠানো হচ্ছে...\n[▰▰▰▰▰▰▰▰▰▰] 100%{FOOTER}", 
            chat_id=message.chat.id, 
            message_id=status_msg.message_id
        )
        time.sleep(0.5)

        bot_username = bot.get_me().username
        caption_text = (
            f"🎧 আপনার MP3 ফাইল রেডি!\n\n"
            f"👤 ইউজার: {user_name}\n"
            f"⚡ কনভার্টেড বাই: @{bot_username}"
            f"{FOOTER}"
        )

        with open(audio_output_path, 'rb') as audio:
            bot.send_audio(
                chat_id=message.chat.id, 
                audio=audio, 
                caption=caption_text
            )

        if status_msg:
            bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        if status_msg:
            bot.edit_message_text(
                f"❌ একটি সমস্যা হয়েছে!\n{str(e)}{FOOTER}",
                chat_id=message.chat.id,
                message_id=status_msg.message_id
            )
        else:
            bot.reply_to(message, f"❌ একটি সমস্যা হয়েছে!\n{str(e)}{FOOTER}")

    finally:
        if os.path.exists(video_input_path):
            os.remove(video_input_path)
        if os.path.exists(audio_output_path):
            os.remove(audio_output_path)

print("🤖 Bot is active and running...")
bot.infinity_polling()
