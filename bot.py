import os
import re
import time
import glob
import yt_dlp
import telebot
from telebot import types

BOT_TOKEN = "8782424758:AAHrJzl-VGFjVLbBqGmzfdU10sCO-HahYtk"
FORCE_CHANNEL = "@fadifva"   # غيرها ليوزر قناتك
DOWNLOAD_DIR = "downloads"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


def clean_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name)[:100]


def delete_old_files():
    now = time.time()
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        try:
            if os.path.isfile(f) and now - os.path.getmtime(f) > 1800:
                os.remove(f)
        except:
            pass


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
    bot.send_message(chat_id, "لازم تشترك بالقناة أولاً حتى تستخدم البوت 🎵", reply_markup=markup)


def format_duration(seconds):
    if not seconds:
        return "غير معروف"
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def search_and_download_audio(query: str):
    delete_old_files()

    before_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*")))

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title).80s.%(ext)s"),
        "default_search": "ytsearch1",
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)

        if "entries" in info:
            info = info["entries"][0]

        title = info.get("title", "Unknown Title")
        uploader = info.get("uploader", "Unknown")
        duration = info.get("duration", 0)

    after_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*")))
    new_files = list(after_files - before_files)

    if not new_files:
        all_files = list(after_files)
        if not all_files:
            raise Exception("ما كدر أحمل ملف الأغنية من يوتيوب")
        filepath = max(all_files, key=os.path.getmtime)
    else:
        filepath = max(new_files, key=os.path.getmtime)

    if not os.path.exists(filepath):
        raise Exception("ملف الصوت ما انحفظ بعد التحميل")

    return {
        "title": title,
        "uploader": uploader,
        "duration": duration,
        "filepath": filepath
    }


@bot.message_handler(commands=["start"])
def start_command(message):
    if not is_user_subscribed(message.from_user.id):
        force_subscribe_message(message.chat.id)
        return

    bot.reply_to(
        message,
        "هلا بيك 🎵\n\n"
        "اكتب هيج:\n"
        "<code>يوت فيروز نسم علينا الهوى</code>"
    )


@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    if is_user_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "تم التحقق ✅")
        try:
            bot.edit_message_text(
                "تم التحقق من الاشتراك ✅\n\nاكتب الآن:\n<code>يوت اسم الأغنية</code>",
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
    text = (message.text or "").strip()

    if not is_user_subscribed(message.from_user.id):
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
