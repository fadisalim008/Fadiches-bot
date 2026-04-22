from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = "8782424758:AAHrJzl-VGFjVLbBqGmzfdU10sCO-HahYtk"
CHANNEL_USERNAME = "@fadifva"   # غيرها إلى قناتك
OWNER_NAME = "fadi"        # غيرها إلى اسم حقوقك


async def is_user_subscribed(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


def subscribe_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 اشترك بالقناة", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")]
    ])


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 العب الآن", callback_data="play_now")],
        [InlineKeyboardButton("ℹ️ عن البوت", callback_data="about_bot")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    subscribed = await is_user_subscribed(context.bot, user.id)

    if not subscribed:
        text = (
            "🚫 عذرًا، لازم تشترك بقناتنا أولًا حتى تستخدم البوت.\n\n"
            "بعد الاشتراك اضغط على زر التحقق."
        )
        await update.message.reply_text(text, reply_markup=subscribe_keyboard())
        return

    text = (
        f"👋 أهلاً {user.first_name}!\n\n"
        "♟️ أهلاً بك في بوت اللعب الاحترافي بين شخصين.\n"
        "اضغط على الزر بالأسفل حتى تبدأ.\n\n"
        f"Developed by {OWNER_NAME}"
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "check_subscription":
        subscribed = await is_user_subscribed(context.bot, user.id)

        if not subscribed:
            await query.message.reply_text(
                "❌ بعدك غير مشترك بالقناة.\nاشترك أولًا ثم اضغط تحقق من جديد.",
                reply_markup=subscribe_keyboard()
            )
            return

        text = (
            f"✅ تم التحقق بنجاح، أهلاً {user.first_name}!\n\n"
            "🎮 تقدر هسه تستخدم البوت.\n\n"
            f"Developed by {OWNER_NAME}"
        )
        await query.message.reply_text(text, reply_markup=main_menu_keyboard())

    elif query.data == "play_now":
        await query.message.reply_text(
            "🎮 قريبًا راح نربط صفحة اللعب والويب أب.\nهسه الأساس اشتغل بنجاح."
        )

    elif query.data == "about_bot":
        await query.message.reply_text(
            f"♟️ بوت لعب بين شخصين داخل تيليجرام.\n\nحقوق التطوير: {OWNER_NAME}"
        )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot is running...")
app.run_polling()
