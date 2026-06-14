import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# LOGGING
logging.basicConfig(level=logging.INFO)

# SOZLAMALAR (Shu yerga o'z ma'lumotlaringizni yozing)
API_TOKEN = '8829040058:AAHBzigI7ASmqdHJ9DRhzL5KxrmzmpkoEKo'  # @BotFather bergan token
ADMIN_ID = 651936747  # Sizning aniq Telegram ID raqamingiz

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 1. /START BUYRUG'I
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 **My Vocabularies To'lov Tizimiga xush kelibsiz!**\n\n"
        "Kitobni faollashtirish uchun quyidagi kartaga to'lovni amalga oshiring:\n"
        "💳 **Karta raqami:** `8600 1234 5678 9012`\n"
        "👤 **Mulkdor:** Eshmatov Toshmat\n"
        "💵 **Narxi:** 25,000 so'm\n\n"
        "📥 **To'lovdan so'ng:** Chekni (skrinshotni) shu yerga rasm ko'rinishida yuboring "
        "va rasm izohiga (caption) Mini App ichidagi shaxsiy ID raqamingizni yozib qoldiring!"
    )
    await message.reply(welcome_text, parse_mode="Markdown")

# 2. HAR QANDAY RASM YOKI FAYL KO'RINISHIDAGI RASMNI USHLASH
@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.DOCUMENT])
async def handle_screenshot(message: types.Message):
    user = message.from_user
    caption_text = message.caption if message.caption else "ID raqam yozilmadi"
    
    # Adminga yuboriladigan matn
    admin_alert = (
        "🔔 **Yangi to'lov cheki keldi!**\n\n"
        f"👤 **Kimdan:** {user.full_name} (@{user.username})\n"
        f"🆔 **Xaridor Telegram ID:** `{user.id}`\n"
        f"📝 **Xaridor yozgan ID/Izoh:** `{caption_text}`\n\n"
        "⚠️ Pul tushganini tekshiring va ushbu ID raqamni GitHub kodingizga qo'shing."
    )

    inline_kb = InlineKeyboardMarkup()
    btn_copy = InlineKeyboardButton(text="📋 ID'dan nusxa olish", callback_data=f"copy_{user.id}")
    inline_kb.add(btn_copy)

    try:
        # Agar oddiy rasm bo'lsa
        if message.photo:
            file_id = message.photo[-1].file_id
            await bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=admin_alert, reply_markup=inline_kb, parse_mode="Markdown")
        # Agar fayl ko'rinishidagi rasm bo'lsa
        elif message.document and message.document.mime_type.startswith('image/'):
            file_id = message.document.file_id
            await bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=admin_alert, reply_markup=inline_kb, parse_mode="Markdown")
        else:
            await message.reply("❌ Iltimos, faqat rasm formatidagi chekni yuboring!")
            return

        # Foydalanuvchiga muvaffaqiyatli javob
        await message.reply("✅ **Chekingiz qabul qilindi!**\nAdministrator tez orada uni tekshirib, kitobingizni ochib beradi.")
        
    except Exception as e:
        # Agar adminga yuborishda xato bo'lsa, foydalanuvchiga bildiradi
        logging.error(f"Xatolik yuz berdi: {e}")
        await message.reply(f"❌ Xabar adminga yetkazilmadi. Xatolik: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
