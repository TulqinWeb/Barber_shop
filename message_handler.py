import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from barbershop_db import DataBase

db = DataBase()


async def message_handler(update, context):
    text = update.message.text

    if text == "Foydalanuvchi":
        logging.info(f"Foydalanuvchi yuborgan xabar: {text}")
        keyboard = [
            [InlineKeyboardButton(text="Erkaklar uchun 🧑", callback_data='barber_men')],
            [InlineKeyboardButton(text="Ayollar uchun  👩", callback_data='barber_women')],
            [InlineKeyboardButton(text="Close", callback_data='close')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.message.from_user.id,
                                       text="Tanlang",
                                       reply_markup=reply_markup)

    elif text == "Xizmat ko'rsatish uchun ro'yxatdan o'tish":
        # `ConversationHandler` ichida ishlaydi
        logging.info(f"Foydalanuvchi yuborgan xabar: {text}")
        # `start_register` ConversationHandler orqali ishlaydi.



    else:
        await context.bot.send_message(chat_id=update.message.from_user.id,
                                       text="<b> /start buyrug'i orqali botni qayta ishga tushurishingiz mumkin! </b>",
                                       parse_mode="HTML")
