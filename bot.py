import os
import re
import time
import yt_dlp
import telebot
from telebot import types

# =========================
# الإعدادات
# =========================
BOT_TOKEN = "8782424758:AAHrJzl-VGFjVLbBqGmzfdU10sCO-HahYtk"
FORCE_CHANNEL = "@fadifva"   # حط يوزر قناتك هنا
DOWNLOAD_DIR = "downloads"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# =========================
# دوال مساعدة
# =========================
def clean_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:120]

def delete_old_files(folder: str):
    now = time.time()
    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)
        try:
            if os.path.isfile(path) and now - os.path.getmtime(path) > 1800:
                os.remove(path)
        except:
            pass

def format_duration(seconds: int) -> str:
    if not seconds:
        return "غير معروف"
    minutes = seconds // 60
    sec = seconds % 60
    return f"{minutes}:{sec:02d}"

def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def force_subscribe_message(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("اشترك بالقناة", url=f"https://t.me/{FORCE_CHANNEL.replace('@', '')}"))
    markup.add(types.InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_sub"))
    bot.send_message(
        chat_id,
        "لازم تشترك بالقناة أولًا حتى تستخدم البوت 🎵",
        reply_markup=markup
    )

def search_and_download_audio(query: str):
    delete_old_files(DOWNLOAD_DIR)

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title).120s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "default_search": "ytsearch1",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)

        if "entries" in info:
            info = info["entries"][0]

        title = info.get("title", "Unknown Title")
        duration = info.get("duration", 0)
        uploader = info.get("uploader", "Unknown")

        requested_downloads = info.get("requested_downloads", [])
        filepath = None

        if requested_downloads:
            filepath = requested_downloads[0].get("filepath")

        if not filepath:
            ext = info.get("ext", "m4a")
            safe_title = clean_filename(title)
            filepath = os.path.join(DOWNLOAD_DIR, f"{safe_title}.{ext}")

        if not os.path.exists(filepath):
            files = [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)]
            if not files:
                raise Exception("ما كدرّت أنزل الملف الصوتي.")
            filepath = max(files, key=os.path.getmtime)

        return {
            "title": title,
            "duration": duration,
            "uploader": uploader,
            "filepath": filepath,
        }

# =========================
# الأوامر
# =========================
@bot.message_handler(commands=["start"])
def start_command(message):
    user_id = message.from_user.id

    if not is_user_subscribed(user_id):
        force_subscribe_message(message.chat.id)
        return

    bot.reply_to(
        message,
        "هلا بيك 🎵\n\n"
        "اكتب هيج:\n"
        "<code>يوت فيروز سالوني الناس</code>"
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.from_user.id

    if is_user_subscribed(user_id):
        bot.answer_callback_query(call.id, "تم التحقق، اشتراكك صحيح ✅")
        try:
            bot.edit_message_text(
                "تم التحقق من الاشتراك ✅\n\nهسه اكتب:\n<code>يوت اسم الاغنية</code>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        except:
            pass
    else:
        bot.answer_callback_query(call.id, "بعدك غير مشترك ❌", show_alert=True)

@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(message):
    user_id = message.from_user.id
    text = (message.text or "").strip()

    if not is_user_subscribed(user_id):
        force_subscribe_message(message.chat.id)
        return

    if not text.startswith("يوت"):
        return

    query = text[3:].strip()

    if not query:
        bot.reply_to(message, "اكتب اسم الأغنية بعد كلمة يوت")
        return

    status = bot.reply_to(message, f"جاري البحث عن: <b>{query}</b> ...")

    try:
        song = search_and_download_audio(query)

        caption = (
            f"🎵 <b>{song['title']}</b>\n"
            f"👤 <b>القناة:</b> {song['uploader']}\n"
            f"⏱ <b>المدة:</b> {format_duration(song['duration'])}"
        )

        with open(song["filepath"], "rb") as audio_file:
            bot.send_audio(
                chat_id=message.chat.id,
                audio=audio_file,
                caption=caption,
                title=song["title"],
                performer=song["uploader"],
                reply_to_message_id=message.message_id,
                timeout=120
            )

        try:
            bot.delete_message(message.chat.id, status.message_id)
        except:
            pass

        try:
            os.remove(song["filepath"])
        except:
            pass

    except Exception as e:
        try:
            bot.edit_message_text(
                f"صار خطأ أثناء جلب الأغنية\n\n<code>{str(e)}</code>",
                chat_id=message.chat.id,
                message_id=status.message_id,
                parse_mode="HTML"
            )
        except:
            bot.reply_to(message, f"صار خطأ:\n<code>{str(e)}</code>")

print("Bot is running...")
bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
