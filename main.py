from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, \
    CallbackQueryHandler, ConversationHandler
import logging


from admin import  handle_admin_response
from barber_register import phone_number, name, bio, start_register, verify_telegram_link, gender_selection, \
    region_selected, handle_photos, next_step, handle_location, confirm_and_send_to_admin

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

from config import BOT_TOKEN  # BOT_TOKEN
from send_user_buttons import send_main_menu
from barbershop_db import DataBase

db = DataBase()

from message_handler import message_handler  # message_handler, xabarlarni tutadi
from inline_handler import inline_handler  # inline_handler, ichki kinobkalardagi xabarlarni tutadi


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_main_menu(update=update, context=context, chat_id=update.message.from_user.id)


def cov_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & filters.Regex("^Xizmat ko'rsatish uchun ro'yxatdan o'tish$"),
                           start_register)
        ],
        states={
            "PHONE_NUMBER": [MessageHandler(filters.CONTACT, phone_number)],
            "NAME": [MessageHandler(filters.TEXT, name)],
            "TELEGRAM_LINK": [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_telegram_link)],
            "BIO": [MessageHandler(filters.TEXT, bio)],
            "GENDER": [MessageHandler(filters.TEXT & ~filters.COMMAND, gender_selection)],
            "REGION_SELECTION": [CallbackQueryHandler(region_selected, pattern=r"^barber_region_\d+$")],
            "PHOTO": [MessageHandler(filters.PHOTO, handle_photos)],  # Rasmlarni qabul qilish uchun holat
            "LOCATION": [MessageHandler(filters.LOCATION, handle_location)],  # Joylashuvni olish uchun holat
            "CONFIRMATION": [CallbackQueryHandler(confirm_and_send_to_admin)]
        },
        fallbacks=[
            CommandHandler('next', next_step)  # Agar foydalanuvchi keyingi bosqichga o'tmoqchi bo'lsa
        ]
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlerlarni qo‘shish
    app.add_handler(CommandHandler("start", start))
    app.add_handler(cov_handler())
    app.add_handler(MessageHandler(filters.TEXT, message_handler))
    app.add_handler(CallbackQueryHandler(handle_admin_response, pattern="^(save|delete)$"))
    app.add_handler(CallbackQueryHandler(inline_handler))


    app.run_polling()


if __name__ == '__main__':
    main()
