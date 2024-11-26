from barbershop_db import DataBase
from config import ADMIN_ID

db = DataBase()


async def handle_admin_decision(update, context):
    query = update.callback_query
    await query.answer()

    # Callback data ni ajratish
    action = query.data  # "save" yoki "delete"

    # Admin huquqini tekshirish
    if str(update.effective_user.id) not in ADMIN_ID:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Sizda bu amalni bajarish huquqi yo'q."
        )

    # user_data dan ma'lumot olish
    user_data = context.user_data
    name = user_data.get("name")
    phone = user_data.get("phone_number")
    telegram_link = user_data.get("telegram_link")
    region_name = user_data.get("region_name")
    gender = user_data.get("gender")
    bio = user_data.get("bio")
    latitude = user_data.get("latitude")
    longitude = user_data.get("longitude")
    photos = user_data.get("photos", [])

    # Bazaga saqlash yoki o'chirish
    if action == "save":
        # Region ID ni olish yoki yaratish
        regions = db.get_all_regions()
        region_id = next((reg["region_id"] for reg in regions if reg["region_name"] == region_name), None)

        if not region_id:
            db.create_region(region_name)
            regions = db.get_all_regions()
            region_id = next(reg["region_id"] for reg in regions if reg["region_name"] == region_name)

        # Ma'lumotlarni bazaga saqlash
        db.create_barber(name, telegram_link, phone, gender, bio, region_id, latitude, longitude)

        barber = db.cursor.execute(
            "SELECT barber_id FROM barbers WHERE name = %s AND phone = %s", (name, phone)
        ).fetchone()

        if barber:
            barber_id = barber[0]
            for photo in photos:
                db.insert_photo(barber_id, photo)

            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="✅ Ma'lumotlar bazaga muvaffaqiyatli saqlandi!"
            )
        else:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="❌ Ma'lumotlar bazaga saqlanmadi. Iltimos, yana urinib ko'ring."
            )

    elif action == "delete":
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="❌ Ma'lumotlar o'chirildi!"
        )

    # Tugmachalarni o'chirish
    await query.edit_message_reply_markup(reply_markup=None)

    # user_data ni tozalash
    context.user_data.clear()
