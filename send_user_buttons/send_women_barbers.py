from telegram import InlineKeyboardButton, InlineKeyboardMarkup


async def send_women_barbers(context, barbers, chat_id, message_id=None):
    buttons = []
    for barber in barbers:
        print(barber)
        buttons.append(
            [InlineKeyboardButton(
                text=f"{barber["name"]}",
                callback_data=f"barber_{barber['barber_id']}_F"
            )]
        )
    buttons.append([InlineKeyboardButton(text="Orqaga", callback_data='region_back_F')])
    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)


    if message_id:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<b> Sartaroshni tanlang </b>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="<b> Sartaroshni tanlang </b>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
