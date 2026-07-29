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
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8965509113:AAFNdxC7bnPA4mMfX9AYD4MBvLYjflNIA_A")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# FFmpeg এর জন্য এক্সিকিউটেবল পাথ নেওয়া
FFMPEG_EXE = ffmpeg_lib.get_ffmpeg_exe()

# ওয়াটারমার্ক/ফুটার
FOOTER = "\n\n⭐ Developed by SAIFUL"

# ইউজারের ভাষা সংরক্ষণের জন্য ডিকশনারি
user_languages = {}

def get_lang(user_id):
    return user_languages.get(user_id, 'bn')  # ডিফল্ট ভাষা বাংলা (bn)

# ভাষা অনুযায়ী টেক্সট সংরক্ষণ
TEXTS = {
    'bn': {
        'welcome': "👋 স্বাগতম, {name}! ✨\n\n🎬 Video to MP3 Converter Bot-এ আপনাকে স্বাগতম! 🎵\n\n📌 কিভাবে ব্যবহার করবেন:\n━ আমাকে যেকোনো Video বা Video Document পাঠান। 📥\n━ আমি মুহূর্তের মধ্যেই সেটিকে HD MP3 Audio-তে কনভার্ট করে দেব। ⚡\n\n🌐 আপনার পছন্দের ভাষা নির্বাচন করুন / Select Language:",
        'set_bn': "✅ ভাষা পরিবর্তিত হয়ে 🇧🇩 বাংলা নির্বাচন করা হয়েছে!\n\n🚀 শুরু করতে এখনই একটি ভিডিও পাঠান! 🔥",
        'set_en': "✅ Language changed to 🇬🇧 English!\n\n🚀 Send any video to get started! 🔥",
        'start_work': "⏳ কাজ শুরু হচ্ছে...\n[▱▱▱▱▱▱▱▱▱▱] 0%",
        'downloading': "📥 ভিডিও ডাউনলোড হচ্ছে...\n[▰▰▰▱▱▱▱▱▱▱] 30%",
        'converting': "⚙️ MP3 এ কনভার্ট করা হচ্ছে...\n[▰▰▰▰▰▰▱▱▱▱] 65%",
        'uploading': "📤 অডিও ফাইল পাঠানো হচ্ছে...\n[▰▰▰▰▰▰▰▰▰▰] 100%",
        'ready': "🎧 আপনার MP3 ফাইল রেডি!\n\n👤 ইউজার: {name}\n⚡ কনভার্টেড বাই: @{bot_username}",
        'error': "❌ একটি সমস্যা হয়েছে!\n{error_msg}"
    },
    'en': {
        'welcome': "👋 Welcome, {name}! ✨\n\n🎬 Welcome to Video to MP3 Converter Bot! 🎵\n\n📌 How to use:\n━ Send or forward me any Video or Video Document. 📥\n━ I will instantly convert it to high quality MP3 Audio. ⚡\n\n🌐 Select your preferred language:",
        'set_bn': "✅ ভাষা পরিবর্তিত হয়ে 🇧🇩 বাংলা নির্বাচন করা হয়েছে!\n\n🚀 শুরু করতে এখনই একটি ভিডিও পাঠান! 🔥",
        'set_en': "✅ Language changed to 🇬🇧 English!\n\n🚀 Send any video to get started! 🔥",
        'start_work': "⏳ Work in progress...\n[▱▱▱▱▱▱▱▱▱▱] 0%",
        'downloading': "📥 Downloading video...\n[▰▰▰▱▱▱▱▱▱▱] 30%",
        'converting': "⚙️ Converting to MP3...\n[▰▰▰▰▰▰▱▱▱▱] 65%",
        'uploading': "📤 Uploading audio file...\n[▰▰▰▰▰▰▰▰▰▰] 100%",
        'ready': "🎧 Your MP3 file is ready!\n\n👤 User: {name}\n⚡ Converted by: @{bot_username}",
        'error': "❌ An error occurred!\n{error_msg}"
    }
}

# 3. Start & Help Command (ভাষার বাটন সহ)
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    lang = get_lang(user_id)
    
    # ইনলাইন ভাষা নির্বাচনের বাটন তৈরি
    markup = telebot.types.InlineKeyboardMarkup()
    btn_bn = telebot.types.InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn")
    btn_en = telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    markup.add(btn_bn, btn_en)
    
    welcome_text = TEXTS[lang]['welcome'].format(name=user_name) + FOOTER
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode=None)

# 4. ভাষা পরিবর্তনের বাটন হ্যান্ডলার
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_language(call):
    user_id = call.from_user.id
    if call.data == 'lang_bn':
        user_languages[user_id] = 'bn'
        msg = TEXTS['bn']['set_bn'] + FOOTER
    else:
        user_languages[user_id] = 'en'
        msg = TEXTS['en']['set_en'] + FOOTER
        
    bot.answer_callback_query(call.id, "Language Updated!")
    bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode=None)

# 5. Video to MP3 Handler
@bot.message_handler(content_types=['video', 'document'])
def handle_video(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    lang = get_lang(user_id)
    txt = TEXTS[lang]
    
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

        # ১. প্রসেস শুরু
        status_msg = bot.reply_to(
            message, 
            txt['start_work'] + FOOTER,
            parse_mode=None
        )
        time.sleep(0.5)

        # ২. ডাউনলোড
        bot.edit_message_text(
            txt['downloading'] + FOOTER, 
            chat_id=message.chat.id, 
            message_id=status_msg.message_id,
            parse_mode=None
        )

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open(video_input_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # ৩. কনভার্ট
        bot.edit_message_text(
            txt['converting'] + FOOTER, 
            chat_id=message.chat.id, 
            message_id=status_msg.message_id,
            parse_mode=None
        )

        # FFmpeg দিয়ে অডিও এক্সট্র্যাক্ট
        cmd = f'"{FFMPEG_EXE}" -i "{video_input_path}" -vn -ar 44100 -ac 2 -b:a 192k "{audio_output_path}" -y'
        subprocess.run(cmd, shell=True, check=True)

        # ৪. আপলোড
        bot.edit_message_text(
            txt['uploading'] + FOOTER, 
            chat_id=message.chat.id, 
            message_id=status_msg.message_id,
            parse_mode=None
        )
        time.sleep(0.5)

        bot_username = bot.get_me().username
        caption_text = txt['ready'].format(name=user_name, bot_username=bot_username) + FOOTER

        with open(audio_output_path, 'rb') as audio:
            bot.send_audio(
                chat_id=message.chat.id, 
                audio=audio, 
                caption=caption_text,
                parse_mode=None
            )

        if status_msg:
            bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        error_text = txt['error'].format(error_msg=str(e)) + FOOTER
        if status_msg:
            try:
                bot.edit_message_text(
                    error_text,
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                    parse_mode=None
                )
            except Exception:
                bot.reply_to(message, error_text, parse_mode=None)
        else:
            bot.reply_to(message, error_text, parse_mode=None)

    finally:
        if os.path.exists(video_input_path):
            os.remove(video_input_path)
        if os.path.exists(audio_output_path):
            os.remove(audio_output_path)

print("🤖 Bot is active and running with Multi-Language Support...")
bot.infinity_polling()
