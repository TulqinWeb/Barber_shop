import re
import json
import base64
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
import logging

from barbershop_db import DataBase
from config import ADMIN_ID

db = DataBase()

from get_all_regions import get_all_regions


async def start_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reply_text = "<b>Salom! Foydalanuvchilar sizga aloqaga chiqishi uchun telefon raqamingizni yuboring. Telefon raqamingizni yuborish uchun kontakt ulashish tugmasini bosing!.</b>"
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton(text="Kontakt ulashish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await context.bot.send_message(
        chat_id=user.id,
        text=reply_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    logging.info(f"{user.first_name} has started registering")
    return "PHONE_NUMBER"


async def phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Telefon raqami kiritilganini tekshiramiz
    if update.message.contact:  # Agar kontakt yuborilgan bo'lsa
        phone_number = update.message.contact.phone_number
        print(phone_number)
        context.user_data['phone_number'] = phone_number
        logging.info(f"Telefon raqami: +{phone_number}")
        await update.message.reply_text("<b>Ismingizni kiriting:</b>", parse_mode="HTML")
        return "NAME"  # Keyingi bosqichga o'tish
    else:
        logging.info(f"Telefon raqami yuborilmadi!")
        await update.message.reply_text("Iltimos, telefon raqamingizni yuboring.")
        print("Bo'sh")
        return "PHONE_NUMBER"  # Telefon raqam yuborilguncha bu yerda qoladi


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data["name"] = name
    logging.info(f"Ismi: {name}")
    await update.message.reply_text(
        text="<b>Foydalanuvchilar sizga aloqaga chiqishi uchun telegram profilingiz havolasini yuboring:</b>\n"
             "Masalan: https://t.me/abcdfusername yoki @aadadusername",
        parse_mode="HTML"
    )
    return "TELEGRAM_LINK"


async def verify_telegram_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()
    # Havola yoki username formatini tekshirish
    if re.match(r"^https://t\.me/\w{5,}$", link) or re.match(r"^@\w{5,}$", link):
        # Havolani umumiy formatga aylantirish (agar username ko‘rinishida bo‘lsa)
        if link.startswith('@'):
            link = f"https://t.me/{link[1:]}"
        context.user_data["telegram_link"] = link
        logging.info(f"Telegram link:{link}")
        await update.message.reply_text(
            text=f"Havolangiz qabul qilindi: {link}\nRahmat",
            parse_mode="HTML"
        )
        await update.message.reply_text(
            text="""O'zingiz haqingizda ma'lumotlar kiriting.Ushbu ma'lumotlar ko'proq foydalanuvchi sizga qiziqish bildirishi uchun muhim bo'lishi mumkin.""",
            parse_mode="HTML"
        )
        return "BIO"

    else:
        await update.message.reply_text(
            text="Noto'g'ri format. Iltimos, havolani yoki username'ni to‘g‘ri shaklda yuboring.",
            parse_mode="HTML"
        )
        return "TELEGRAM_LINK"


async def bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bio = update.message.text
    context.user_data["bio"] = bio
    keyboard = [
        [KeyboardButton(text="Erkaklar uchun 🧑")],
        [KeyboardButton(text="Ayollar uchun 👩")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    logging.info(f"BIO : {bio}")
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="Kimlar uchun o'z xizmatingizni taklif etasiz? Birini tanlang",
        parse_mode="HTML",
        reply_markup=reply_markup
    )
    return "GENDER"


async def gender_selection(update, context):
    gender = update.message.text

    if gender == "Erkaklar uchun 🧑":
        context.user_data['gender'] = "M"
        regions = db.get_all_regions()
        logging.info(f"Xzimat turi:{gender}")
        await get_all_regions(context=context, regions=regions,
                              chat_id=update.message.from_user.id)

    elif gender == "Ayollar uchun 👩":
        context.user_data['gender'] = "F"
        regions = db.get_all_regions()
        logging.info(f"Xzimat turi:{gender}")
        await get_all_regions(context=context, regions=regions,
                              chat_id=update.message.from_user.id)

    return "REGION_SELECTION"


async def region_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    # Callback_data dan region_id ni olish
    data = query.data  # Masalan: "region_1"
    region_id = int(data.split('_')[2])

    # Region nomini olish (databazadan qidirib topish yoki inline tugma yaratishda saqlash)
    region_name = next(region['region_name'] for region in db.get_all_regions() if region['region_id'] == region_id)

    # Ma'lumotlarni saqlash
    context.user_data["region_id"] = region_id
    context.user_data["region_name"] = region_name
    logging.info(f"Tuman: {region_name}")
    # Xabarni yangilash
    await query.edit_message_text(
        text=f" <b>{region_name}</b> tumani tanladi.",
        parse_mode="HTML"
    )

    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text="<b> O'zingizning ishlaringizdan namunalar (rasmlar) yuboring! </b> ",
                                   parse_mode="HTML"
                                   )
    return "PHOTO"


async def handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Foydalanuvchidan kelgan rasmlar
    photos = context.user_data.get('photos', [])

    if update.message.photo:
        # Yuborilgan har bir rasmni tekshirish
        new_photos = []  # Yangi rasmlar ro'yxati
        # Telegramda rasmlar o'lchami sifatida photo[-1] eng katta versiya bo'ladi
        photo_file_id = update.message.photo[-1].file_id  # Eng katta o'lchamni olish

        # Agar rasm oldin yuborilmagan bo'lsa, uni saqlaymiz
        if photo_file_id not in photos:
            new_photos.append(photo_file_id)  # Yangi rasmni qo'shish
        else:
            # Bu rasm allaqachon yuborilgan, shuning uchun foydalanuvchiga xabar yuboriladi
            await update.message.reply_text(
                "Bu rasm allaqachon yuborilgan. Yana rasmlar yuborishingiz mumkin yoki keyingi bosqichga o'tish uchun /next buyrug'ini kiriting."
            )

        # Yangi rasmlar ro'yxatini to'liq ro'yxatga qo'shish
        photos.extend(new_photos)  # Yangi rasmlarni saqlash

        # Yangilangan ro'yxatni context'ga saqlaymiz
        context.user_data['photos'] = photos

        # Faqat yangi rasmlar yuborilgandan keyin umumiy xabar yuboriladi
        if new_photos:  # Yangi rasmlar qo'shilgan bo'lsa
            await update.message.reply_text(
                f"Jami {len(photos)} ta rasm qabul qilindi.\n"
                "Yana rasmlar yuborishingiz mumkin yoki keyingi bosqichga o'tish uchun /next buyrug'ini kiriting."
            )

        else:
            pass

    return "PHOTO"  # Shu holatda qoladi, foydalanuvchi yana rasm yuborishi mumkin


async def next_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = context.user_data.get('photos', [])
    if photos:
        await update.message.reply_text(
            f"Jami {len(photos)} ta rasm qabul qilindi. Keyingi bosqichga o'tamiz."
        )
    else:
        await update.message.reply_text(
            "Siz hech qanday rasm yubormadingiz. Davom etish uchun kamida bitta rasm yuboring."
        )
        return "PHOTO"  # Rasmlar yuborilmagani uchun shu holatda qoladi

    # Joylashuv yuborish tugmasi
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton(text="Joylashuv yuborish", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="Iltimos, foydalanuvchilar ish joyingizni oson topib borishi uchun, o'z ish joyingiz lokatsiyasini yuboring. Lokatsiya yuborish uchun << Joylashuv yuborish >> tugmasini bosing!",
        reply_markup=reply_markup
    )
    return "LOCATION"  # Keyingi bosqich


# Joylashuvni olish va tasdiqlash uchun barcha ma'lumotlarni yuborish
async def handle_location(update, context):
    if update.message.location:
        latitude = update.message.location.latitude
        longitude = update.message.location.longitude

        context.user_data['latitude'] = latitude
        context.user_data['longitude'] = longitude

        # # Foydalanuvchining joylashuvini saqlash
        # context.user_data['location'] = {'latitude': latitude, 'longitude': longitude}

        # Foydalanuvchiga joylashuv qabul qilinganligini bildirish
        await update.message.reply_text("Joylashuvingiz qabul qilindi.")

        # Barcha ma'lumotlarni foydalanuvchiga yuborish
        await send_all_data_to_user(update, context)
        return "CONFIRMATION"
    else:
        # Joylashuv yuborilmagan bo'lsa
        await update.message.reply_text("Iltimos, telefoningizdan joylashuvingizni ulashing.")
        return "LOCATION"


# Ma'lumotlarni formatlab, tasdiqlash tugmasi bilan yuborish
async def send_all_data_to_user(update, context):
    # Foydalanuvchining barcha ma'lumotlarini olish
    user_data = context.user_data
    name = user_data.get("name", "Noma'lum")
    print(name)
    phone = user_data.get("phone_number", "Noma'lum")
    print(phone)
    telegram_link = user_data.get("telegram_link", "Noma'lum")
    print(telegram_link)
    region_name = user_data.get("region_name", "Noma'lum")
    print(region_name)
    gender = "Erkaklar uchun" if user_data.get("gender") == "M" else "Ayollar uchun"
    print(gender)
    bio = user_data.get("bio", "Noma'lum")
    print(bio)
    latitude = user_data.get("latitude")
    print(latitude)
    longitude = user_data.get("longitude")
    print(longitude)
    photos = user_data.get("photos", [])
    print('-----------------------------------------------------------------------------------------------------------')

    # Ma'lumotlarni formatlash
    message = (
        f"📝 <b>Xizmat Ko'rsatuvchi Ma'lumotlari:</b>\n"
        f"📛 <b>Ismi:</b> {name}\n"
        f"📞 <b>Telefon:</b> +{phone}\n"
        f"🔗 <b>Telegram Link:</b> {telegram_link}\n"
        f"📍 <b>Hudud:</b> {region_name}\n"
        f"👤 <b>Xizmat turi:</b> {gender}\n"
        f"📖 <b>Ma'lumot:</b> {bio}\n"

    )

    # Inline tugmalarni yaratish
    keyboard = [
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data="approve"),
            InlineKeyboardButton("❌ Rad etish", callback_data="reject")
        ]
    ]

    # Rasm yuborish (agar mavjud bo'lsa)
    for photo in photos:
        await update.message.reply_photo(photo=photo)

    # Xizmat ko'rsatuvchiga ma'lumotlarni yuborish
    await update.message.reply_text(
        text=message,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return "CONFIRMATION"


#  Xizmat ko'rsatuvchi ma'lumotlarini tasdiqlash va adminga yuborish
async def confirm_and_send_to_admin(update, context):
    query = update.callback_query

    # Foydalanuvchi ma'lumotlarini olish
    user_data = context.user_data
    name = user_data.get("name", "Noma'lum")
    print('name')
    phone = user_data.get("phone_number", "Noma'lum")
    print(phone)
    telegram_link = user_data.get("telegram_link", "Noma'lum")
    print(telegram_link)
    region_name = user_data.get("region_name", "Noma'lum")
    print(region_name)
    gender = "Erkaklar uchun" if user_data.get("gender") == "M" else "Ayollar uchun"
    print(gender)
    bio = user_data.get("bio", "Noma'lum")
    print(bio)
    latitude = user_data.get("latitude", "Noma'lum")
    print(latitude)
    longitude = user_data.get("longitude", "Noma'lum")
    print(longitude)
    photos = user_data.get("photos", [])

    # Adminga yuboriladigan xabar
    message = (
        f"📝 <b>Yangi Xizmat Ko'rsatuvchi Ma'lumotlari:</b>\n"
        f"📛 <b>Ismi:</b> {name}\n"
        f"📞 <b>Telefon:</b> +{phone}\n"
        f"🔗 <b>Telegram Link:</b> {telegram_link}\n"
        f"📍 <b>Hudud:</b> {region_name}\n"
        f"👤 <b>Xizmat turi:</b> {gender}\n"
        f"📖 <b>Ma'lumot:</b> {bio}\n"
        f"🌐 <b>Manzil:</b> Latitude: {latitude}, Longitude: {longitude}\n"
    )

    # Foydalanuvchi ma'lumotlarini JSON formatida kodlash
    data = {
        "name": name,
        "phone": phone,
        "telegram_link": telegram_link,
        "region_name": region_name,
        "gender": gender,
        "bio": bio,
        "latitude": latitude,
        "longitude": longitude,
        "photos": photos
    }

    # JSON formatida kodlash
    json_data = json.dumps(data)

    # Base64 formatiga o'zgartirish
    encoded_data = base64.b64encode(json_data.encode()).decode()

    # Callback data sifatida yuborish
    button = [
        [InlineKeyboardButton(text="✅ Bazaga saqlash", callback_data=f"service:save:{encoded_data}")],
        [InlineKeyboardButton(text="❌ O'chirib yuborish", callback_data=f"service:delete:{encoded_data}")]
    ]

    reply_markup = InlineKeyboardMarkup(button)

    # Admin ID ga yuborish
    if query.data == "approve":

        admin_chat_id = ADMIN_ID  # Agar bir nechta admin bo'lsa, bitta ID ni tanlang
        for photo in photos:
            await context.bot.send_photo(chat_id=admin_chat_id, photo=photo)

        await context.bot.send_message(
            chat_id=admin_chat_id, text=message, reply_markup=reply_markup, parse_mode="HTML"
        )

        # Foydalanuvchini xabardor qilish
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Ma'lumotlaringiz adminga yuborildi."
        )

        return ConversationHandler.END

    elif query.data == "reject":
        # Foydalanuvchiga rad etilganligi haqida xabar yuborish
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Ma'lumotlaringizni jo'natishni rad ettingiz va ma'lumotlaringiz o'chirildi."
        )
        context.user_data.clear()
        return ConversationHandler.END
