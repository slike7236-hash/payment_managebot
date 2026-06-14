import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# LOGGING SOZLAMALARI (Bot holatini kuzatish uchun)
logging.basicConfig(level=logging.INFO)

# TELEGRAM SOZLAMALARI
API_TOKEN = 'BU_YERGA_BOT_TOKENINGIZNI_YOZING'  # @BotFather bergan token
ADMIN_ID = 651936747  # Sizning shaxsiy Telegram ID raqamingiz (Cheklar shu yerga boradi)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 1. FOYDALANUVCHIGA /START BUYRUG'I JAVOBI
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

# 2. FOYDALANUVCHIDAN RASMLI CHEKNI QABUL QILISH VA ADMINGA YUBORISH
@dp.message_handler(content_types=['photo'])
async def handle_screenshot(message: types.Message):
    user = message.from_user
    caption_text = message.caption if message.caption else "ID raqam yozilmadi"
    
    # Sizga (Adminga) boradigan bildirishnoma matni
    admin_alert = (
        "🔔 **Yangi to'lov cheki keldi!**\n\n"
        "👤 **Kimdan:** {user.full_name} (@{user.username})\n"
        "🆔 **Xaridor Telegram ID:** `{user.id}`\n"
        "📝 **Xaridor yozgan ID/Izoh:** `{caption_text}`\n\n"
        "⚠️ Pul tushganini tekshiring va ushbu ID raqamni GitHub'dagi Mini App kodingizga qo'shing."
    ).format(user=user, caption_text=caption_text)

    # Adminga kelgan xabar tagida ID nusxalash tugmasi
    inline_kb = InlineKeyboardMarkup()
    btn_copy = InlineKeyboardButton(text="📋 ID'dan nusxa olish", callback_data=f"copy_{user.id}")
    inline_kb.add(btn_copy)

    # Chek rasmini sizga yo'naltirish
    await bot.send_photo(
        chat_id=ADMIN_ID, 
        photo=message.photo[-1].file_id, 
        caption=admin_alert, 
        reply_markup=inline_kb,
        parse_mode="Markdown"
    )
    
    # Xaridorga tasdiq xabari
    await message.reply("✅ **Chekingiz qabul qilindi!**\nAdministrator tez orada uni tekshirib, kitobingizni ochib beradi.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
