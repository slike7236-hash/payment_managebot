import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# LOGGING
logging.basicConfig(level=logging.INFO)

# SOZLAMALAR
API_TOKEN = '8829040058:AAHBzigI7ASmqdHJ9DRhzL5KxrmzmpkoEKo'  # @BotFather bergan token
ADMIN_ID = 651936747  # Sizning aniq Telegram ID raqamingiz

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 1. /START BUYRUG'I
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    welcome_text = (
        "<b>👋 My Vocabularies To'lov Tizimiga xush kelibsiz!</b>\n\n"
        "Kitobni faollashtirish uchun quyidagi kartaga to'lovni amalga oshiring:\n"
        "💳 <b>Karta raqami:</b> <code>8600 1234 5678 9012</code>\n"
        "👤 <b>Mulkdor:</b> Eshmatov Toshmat\n"
        "💵 <b>Narxi:</b> 25,000 so'm\n\n"
        "📥 <b>To'lovdan so'ng:</b> Chekni (skrinshotni) shu yerga rasm ko'rinishida yuboring "
        "va rasm izohiga (caption) Mini App ichidagi shaxsiy ID raqamingizni yozib qoldiring!"
    )
    await message.reply(welcome_text, parse_mode="HTML")

# 2. RASMLARNI XATOLIKSIZ QABUL QILISH
@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.DOCUMENT])
async def handle_screenshot(message: types.Message):
    user = message.from_user
    caption_text = message.caption if message.caption else "ID raqam yozilmadi"
    
    # Ismdagi xavfli belgilarni zararsizlantirish
    full_name = user.full_name.replace('<', '&lt;').replace('>', '&gt;')
    username = user.username if user.username else "yo'q"
    
    # Adminga yuboriladigan matn (HTML formatida)
    admin_alert = (
        "🔔 <b>Yangi to'lov cheki keldi!</b>\n\n"
        f"👤 <b>Kimdan:</b> {full_name} (@{username})\n"
        f"🆔 <b>Xaridor Telegram ID:</b> <code>{user.id}</code>\n"
        f"📝 <b>Xaridor yozgan ID/Izoh:</b> <code>{caption_text}</code>\n\n"
        "⚠️ Pul tushganini tekshiring va ushbu ID raqamni Mini App kodingizga qo'shing."
    )

    inline_kb = InlineKeyboardMarkup()
    btn_copy = InlineKeyboardButton(text="📋 ID'dan nusxa olish", callback_data=f"copy_{user.id}")
    inline_kb.add(btn_copy)

    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            await bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=admin_alert, reply_markup=inline_kb, parse_mode="HTML")
        elif message.document and message.document.mime_type.startswith('image/'):
            file_id = message.document.file_id
            await bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=admin_alert, reply_markup=inline_kb, parse_mode="HTML")
        else:
            await message.reply("❌ Iltimos, faqat rasm formatidagi chekni yuboring!")
            return

        await message.reply("✅ <b>Chekingiz qabul qilindi!</b>\nAdministrator tez orada uni tekshirib, kitobingizni ochib beradi.")
        
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        await message.reply(f"❌ Xabar adminga yetkazilmadi. Xatolik: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
