import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# LOGGING
logging.basicConfig(level=logging.INFO)

# SOZLAMALAR
API_TOKEN = '8829040058:AAHBzigI7ASmqdHJ9DRhzL5KxrmzmpkoEKo'  # Tokeningiz kiritildi
ADMIN_ID = 651936747  # Sizning Telegram ID raqamingiz

# FSM Storage (Dialog holatlarini eslab qolish uchun)
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# DIALOG BOSQICHLARI (STATES)
class OrderProcess(StatesGroup):
    waiting_for_book_name = State()  # Kitob nomini kutish holati
    waiting_for_screenshot = State()  # Chekni kutish holati

# REPLYY KEYBOARD (Pastdagi menyu tugmasi)
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("📚 Kitob sotib olish"))

# 1. /START BOSILGANDA
@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()  # Har qanday eski dialoglarni tozalash
    welcome_text = (
        "<b>👋 My Vocabularies Botiga xush kelibsiz!</b>\n\n"
        "✨ Bu bot orqali siz o'z so'z boyligingizni oshirish uchun mo'ljallangan "
        "eng sara interaktiv kitoblarni sotib olishingiz va Mini App orqali ulardan foydalanishingiz mumkin.\n\n"
        "👇 Kitob xarid qilishni boshlash uchun pastdagi <b>📚 Kitob sotib olish</b> tugmasini bosing."
    )
    await message.reply(welcome_text, reply_markup=main_menu, parse_mode="HTML")

# 2. "KITOB SOTIB OLISH" TUGMASI BOSILGANDA
@dp.message_handler(lambda message: message.text == "📚 Kitob sotib olish", state="*")
async def start_order(message: types.Message):
    await OrderProcess.waiting_for_book_name.set()  # Birinchi bosqichni yoqamiz
    await message.reply(
        "📝 <b>Iltimos, sotib olmoqchi bo'lgan kitobingiz nomini yozing:</b>\n"
        "<i>(Masalan: English Vocabulary, Toefl Words va h.k.)</i>",
        reply_markup=types.ReplyKeyboardRemove(), # Menyu tugmasini vaqtincha yopamiz
        parse_mode="HTML"
    )

# 3. KITOB NOMINI QABUL QILISH VA KARTANI KO'RSATISH
@dp.message_handler(state=OrderProcess.waiting_for_book_name, content_types=types.ContentType.TEXT)
async def process_book_name(message: types.Message, state: FSMContext):
    book_name = message.text
    await state.update_data(chosen_book=book_name)  # Kitob nomini xotiraga saqlaymiz
    
    await OrderProcess.next()  # Keyingi bosqichga (chek kutishga) o'tamiz
    
    payment_text = (
        f"🛒 <b>Siz tanlagan kitob:</b> {book_name}\n\n"
        "💳 To'lovni amalga oshirish uchun quyidagi karta raqamiga pul o'tkazing:\n"
        "• <b>Karta raqami:</b> <code>8600 1234 5678 9012</code>\n"
        "• <b>Mulkdor:</b> Eshmatov Toshmat\n"
        "• <b>Narxi:</b> 25,000 so'm\n\n"
        "📥 <b>To'lovdan so'ng:</b> To'lov chekini (skrinshotini) shu yerga rasm ko'rinishida yuboring!"
    )
    await message.reply(payment_text, parse_mode="HTML")

# 4. CHEKNI QABUL QILISH, ADMINGA YUBORISH VA DIALOGNI YAKUNLASH
@dp.message_handler(state=OrderProcess.waiting_for_screenshot, content_types=[types.ContentType.PHOTO, types.ContentType.DOCUMENT])
async def process_screenshot(message: types.Message, state: FSMContext):
    user = message.from_user
    
    # Xotiradan kitob nomini olamiz
    user_data = await state.get_data()
    book_name = user_data.get("chosen_book", "Noma'lum kitob")
    
    # Ismdagi maxsus belgilarni tozalash
    full_name = user.full_name.replace('<', '&lt;').replace('>', '&gt;')
    username = f"@{user.username}" if user.username else "yo'q"
    
    # Adminga boradigan bildirishnoma
    admin_alert = (
        "🔔 <b>Yangi buyurtma va to'lov cheki keldi!</b>\n\n"
        f"👤 <b>Xaridor:</b> {full_name} ({username})\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"📚 <b>Sotib olmoqchi:</b> <u>{book_name}</u>\n\n"
        "⚠️ Pul tushganini tekshiring. Agar hammasi joyida bo'lsa, pastdagi <b>Tasdiqlash</b> tugmasini bosing."
    )

    # Admin uchun tugma (Xaridor ID raqami callback ichiga yashiriladi)
    inline_kb = InlineKeyboardMarkup()
    btn_approve = InlineKeyboardButton(text="✅ To'lovni tasdiqlash va Kitobni ochish", callback_data=f"approve_{user.id}_{book_name}")
    inline_kb.add(btn_approve)

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

        # Xaridorga tasdiq va holatni yakunlash
        await message.reply(
            "⏳ <b>To'lovingiz qabul qilindi va tekshirilmoqda!</b>\n"
            "Administrator tez orada to'lovni tasdiqlaydi va kitobingiz tizimda avtomatik ochiladi. Iltimos, biroz kuting.", 
            reply_markup=main_menu,
            parse_mode="HTML"
        )
        await state.finish() # Dialog yakunlandi, foydalanuvchi boshqa kitob olishi mumkin endi
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.reply(f"❌ Xatolik yuz berdi, adminga yetkazilmadi: {e}")

# 5. ADMIN "TASDIQLASH" TUGMASINI BOSGANDA XARIDORGA JAVOB YUBORISH
@dp.callback_query_handler(lambda call: call.data.startswith('approve_'), state="*")
async def approve_payment(call: types.CallbackQuery):
    # Callback'dan foydalanuvchi ID va kitob nomini ajratib olamiz
    data_parts = call.data.split('_')
    buyer_id = int(data_parts[1])
    book_name = data_parts[2]
    
    try:
        # Xaridorga xushxabar yuborish
        success_message = (
            f"🎉 <b>Ajoyib xabar!</b>\n\n"
            f"✅ Sizning <b>{book_name}</b> kitobi uchun qilgan to'lovingiz muvaffaqiyatli tasdiqlandi!\n"
            f"🚀 Biz siz uchun ushbu kitobni butunlay ochib qo'ydik. Mini App'ga kirib, o'qishni boshlashingiz mumkin. Omad!"
        )
        await bot.send_message(chat_id=buyer_id, text=success_message, parse_mode="HTML")
        
        # Admin oynasidagi matnni yangilash (ish bajarilganini bildirish uchun)
        await call.message.edit_caption(
            caption=call.message.caption + f"\n\n🟢 <b>BU BUYURTMA SIZ TOMONIDAN TASDIQLANDI! KITOB OCHILDI.</b>",
            parse_mode="HTML"
        )
        await call.answer("Xaridorga kitob ochilgani haqida xabar yuborildi!", show_alert=True)
        
    except Exception as e:
        await call.answer(f"Xabar yuborishda xatolik: {e}", show_alert=True)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
