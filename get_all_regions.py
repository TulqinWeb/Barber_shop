from telegram import InlineKeyboardButton, InlineKeyboardMarkup


async def get_all_regions(context, regions, chat_id):
    buttons = []
    for region in regions:
        buttons.append(
            [InlineKeyboardButton(
                text=f"{region["region_name"]}",
                callback_data=f"barber_region_{region['region_id']}")
        ])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await context.bot.send_message(
        chat_id=chat_id,
        text="<b> Hududni tanlang </b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


