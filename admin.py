from barbershop_db import DataBase
from config import ADMIN_ID
import base64
import json

db = DataBase()


async def handle_admin_decision(update, context):
    query = update.callback_query
    await query.answer()
    callback_data = query.data

    # Callback data'dan Base64 kodlangan ma'lumotni olish
    encoded_data = query.data.split(":")[2]
    decoded_data = base64.b64decode(encoded_data).decode()

    # JSON formatida dekodlash
    user_data = json.loads(decoded_data)

    # Foydalanuvchi ma'lumotlari
    name = user_data["name"]
    phone = user_data["phone"]
    telegram_link = user_data["telegram_link"]
    region_name = user_data["region_name"]
    gender = user_data["gender"]
    bio = user_data["bio"]
    latitude = user_data["latitude"]
    longitude = user_data["longitude"]
    photos = user_data["photos"]



    # Admin huquqini tekshirish
    if str(update.effective_user.id) not in ADMIN_ID:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Sizda bu amalni bajarish huquqi yo'q."
        )
        return

    # Bazaga saqlash yoki o'chirish
    if callback_data.startswith("service:"):
        parts = callback_data.split(":")
        action = parts[1]


        print(name)

        print(phone)

        print(telegram_link)

        print(region_name)

        print(gender)

        print(bio)

        print(latitude)

        print(longitude)

        print(photos)

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
