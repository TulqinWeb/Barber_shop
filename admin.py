from barbershop_db import DataBase
from config import ADMIN_ID

db = DataBase()


async def handle_admin_decision(update, context):
    query = update.callback_query
    await query.answer()
    callback_data = query.data

    # Admin qismi
    user_data = context.bot_data.get(query.from_user.id)
    if not user_data:
        await context.bot.send_message(chat_id=query.from_user.id, text="Ma'lumotlar topilmadi.")
        return

    # Admin huquqini tekshirish
    if str(update.effective_user.id) not in ADMIN_ID:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Sizda bu amalni bajarish huquqi yo'q."
        )
        return

    # Bazaga saqlash yoki o'chirish
    if callback_data.startswith("service:"):
        action = callback_data.split(":")[1]
        user_id = callback_data.split(":")[2]
        user_data = context.bot_data.get(int(user_id))

        if not user_data:
            await context.bot.send_message(chat_id=query.from_user.id, text="Ma'lumotlar topilmadi.")
            return

        name = user_data.get("name")
        print(name)
        phone = user_data.get("phone_number")
        print(phone)
        telegram_link = user_data.get("telegram_link")
        print(telegram_link)
        region_name = user_data.get("region_name")
        print(region_name)
        gender = user_data.get("gender")
        print(gender)
        bio = user_data.get("bio")
        print(bio)
        latitude = user_data.get("latitude")
        print(latitude)
        longitude = user_data.get("longitude")
        print(longitude)
        photos = user_data.get("photos", [])
        print(photos)

        # Ma'lumotlarni tekshirish
        required_fields = [name, phone, region_name, gender]
        if any(field is None or field == "" for field in required_fields):
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="❌ Ma'lumotlar to'liq emas. Iltimos, qaytadan to'ldiring.")

            return

        if action == "save":
            # Regionni olish yoki yaratish
            regions = db.get_all_regions()
            region_id = next((reg["region_id"] for reg in regions if reg["region_name"] == region_name), None)

            if not region_id:
                db.create_region(region_name)
                regions = db.get_all_regions()
                region_id = next(reg["region_id"] for reg in regions if reg["region_name"] == region_name)

            # Barberni yaratish
            db.create_barber(name, telegram_link, phone, gender, bio, region_id, latitude, longitude)

            # Barber IDni olish
            db.cursor.execute(
                "SELECT barber_id FROM barbers WHERE name = %s AND phone = %s", (name, phone)
            )
            barber = db.cursor.fetchone()

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
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            print(f"Tugmachalarni o'chirishda xatolik: {e}")

        # Foydalanuvchi ma'lumotlarini tozalash
        context.user_data.clear()
