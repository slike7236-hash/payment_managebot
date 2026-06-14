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
API_TOKEN = '8829040058:AAHBzigI7ASmqdHJ9DRhzL5KxrmzmpkoEKo'  # Tokeningiz kiritilgan
ADMIN_ID = 651936747  # Sizning Telegram ID raqamingiz

# FSM Storage
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# OBUNACHILAR RO'YXATI (Reklama va Statistika uchun)
users_list = set()

# DIALOG BOSQICHLARI (STATES)
class OrderProcess(StatesGroup):
    waiting_for_book_name = State()
    waiting_for_screenshot = State()

# KEYBOARDS (Menyular)
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("📚 Kitob sotib olish"))

cancel_menu = ReplyKeyboardMarkup(resize_keyboard=True)
cancel_menu.add(KeyboardButton("❌ Jarayonni bekor qilish"))

# 1. /START BOSILGANDA
@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    users_list.add(message.from_user.id)  # Foydalanuvchini ro'yxatga qo'shish
    
    welcome_text = (
        "<b>👋 My Vocabularies Botiga xush kelibsiz!</b>\n\n"
        "✨ Bu bot orqali siz o'z so'z boyligingizni oshirish uchun mo'ljallangan "
        "eng sara interaktiv kitoblarni sotib olishingiz mumkin.\n\n"
        "👇 Kitob xarid qilishni boshlash uchun pastdagi <b>📚 Kitob sotib olish</b> tugmasini bosing."
    )
    await message.reply(welcome_text, reply_markup=main_menu, parse_mode="HTML")

# 2. ADMIN UCHUN STATISTIKA BUYRUG'I
@dp.message_handler(commands=['stat'], state="*")
async def cmd_stat(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply(f"📊 <b>Bot statistikasi:</b>\n\n👥 Jami obunachilar soni: <b>{len(users_list)}</b> ta", parse_mode="HTML")
    else:
        await message.reply("❌ Bu buyruq faqat admin uchun!")

# 3. ADMIN UCHUN REKLAMA JONATISH BUYRUG'I
@dp.message_handler(commands=['reklama'], state="*")
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Bu buyruq faqat admin uchun!")
        return

    reklama_text = message.get_args()
    if not reklama_text:
        await message.reply("⚠️ <b>Xato:</b> Reklama matnini yozmadingiz!\n\n<i>Namuna:</i> <code>/reklama Ertaga hamma kitoblarga 50% chegirma!</code>", parse_mode="HTML")
        return

    send_count = 0
    failed_count = 0

    for user_id in users_list:
        try:
            await bot.send_message(chat_id=user_id, text=reklama_text, parse_mode="HTML")
            send_count += 1
        except Exception:
            failed_count += 1

    await message.reply(
        f"📢 <b>Reklama tarqatish yakunlandi:</b>\n\n"
        f"✅ Yetkazildi: <b>{send_count}</b> ta obunachiga\n"
        f"❌ Yetkazilmadi (bloklaganlar): <b>{failed_count}</b> ta",
        parse_mode="HTML"
    )

# 4. JARRAYONNI BEKOR QILISH (CANCEL TUGMASI)
@dp.message_handler(lambda message: message.text == "❌ Jarayonni bekor qilish", state="*")
async def cancel_order(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("🔄 Sotib olish jarayoni bekor qilindi. Bosh menyuga qaytdingiz.", reply_markup=main_menu, parse_mode="HTML")

# 5. "KITOB SOTIB OLISH" TUGMASI BOSILGANDA
@dp.message_handler(lambda message: message.text == "📚 Kitob sotib olish", state="*")
async def start_order(message: types.Message):
    users_list.add(message.from_user.id)
    await OrderProcess.waiting_for_book_name.set()
    await message.reply(
        "📝 <b>Iltimos, sotib olmoqchi bo'lgan kitobingiz nomini yozing:</b>",
        reply_markup=cancel_menu,
        parse_mode="HTML"
    )

# 6. KITOB NOMINI QABUL QILISH VA KARTANI KO'RSATISH
@dp.message_handler(state=OrderProcess.waiting_for_book_name, content_types=types.ContentType.TEXT)
async def process_book_name(message: types.Message, state: FSMContext):
    book_name = message.text
    await state.update_data(chosen_book=book_name)
    
    await OrderProcess.next()
    
    payment_text = (
        f"🛒 <b>Siz tanlagan kitob:</b> {book_name}\n\n"
        "💳 To'lovni amalga oshirish uchun quyidagi karta raqamiga pul o'tkazing:\n"
        "• <b>Karta raqami:</b> <code>8600 1234 5678 9012</code>\n"
        "• <b>Mulkdor:</b> Eshmatov Toshmat\n"
        "• <b>Narxi:</b> 25,000 so'm\n\n"
        "📥 <b>To'lovdan so'ng:</b> To'lov chekini (skrinshotini) shu yerga rasm ko'rinishida yuboring!"
    )
    await message.reply(payment_text, reply_markup=cancel_menu, parse_mode="HTML")

# 7. CHEKNI QABUL QILISH VA ADMINGA YUBORISH
@dp.message_handler(state=OrderProcess.waiting_for_screenshot, content_types=[types.ContentType.PHOTO, types.ContentType.DOCUMENT])
async def process_screenshot(message: types.Message, state: FSMContext):
    user = message.from_user
    users_list.add(user.id)
    
    user_data = await state.get_data()
    book_name = user_data.get("chosen_book", "Noma'lum kitob")
    
    full_name = user.full_name.replace('<', '&lt;').replace('>', '&gt;')
    username = f"@{user.username}" if user.username else "yo'q"
    user_caption = message.caption if message.caption else "Izoh qoldirilmadi"
    
    admin_alert = (
        "🔔 <b>Yangi buyurtma va to'lov cheki keldi!</b>\n\n"
        f"👤 <b>Xaridor:</b> {full_name} ({username})\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"📚 <b>Sotib olmoqchi:</b> <u>{book_name}</u>\n"
        f"📝 <b>Izoh:</b> {user_caption}\n\n"
        "⚠️ Pulni tekshiring va qaror qabul qiling:"
    )

    inline_kb = InlineKeyboardMarkup(row_width=2)
    btn_approve = InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"app_{user.id}_{book_name}")
    btn_reject = InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rej_{user.id}_{book_name}")
    inline_kb.add(btn_approve, btn_reject)

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

        await message.reply(
            "⏳ <b>To'lovingiz qabul qilindi va tekshirilmoqda!</b>\n"
            "Administrator tez orada to'lovni tekshiradi. Iltimos, biroz kuting.", 
            reply_markup=main_menu,
            parse_mode="HTML"
        )
        await state.finish()
        
    except Exception as e:
        await message.reply(f"❌ Xatolik yuz berdi: {e}")

# 8. ADMIN QAROR QABUL QILGANDA (TUGMALAR)
@dp.callback_query_handler(lambda call: call.data.startswith(('app_', 'rej_')), state="*")
async def admin_decision(call: types.CallbackQuery):
    data_parts = call.data.split('_')
    action = data_parts[0]
    buyer_id = int(data_parts[1])
    book_name = data_parts[2]
    
    if action == 'app':
        try:
            success_message = (
                f"🎉 <b>Ajoyib xabar!</b>\n\n"
                f"✅ Sizning <b>{book_name}</b> kitobi uchun qilgan to'lovingiz muvaffaqiyatli tasdiqlandi!\n"
                f"🚀 Biz siz uchun ushbu kitobni ochib qo'ydik. Mini App'ga kirib foydalanishingiz mumkin!"
            )
            await bot.send_message(chat_id=buyer_id, text=success_message, parse_mode="HTML")
            await call.message.edit_caption(caption=call.message.caption + f"\n\n🟢 <b>TASDIQLANDI. Kitob ochildi!</b>", parse_mode="HTML")
            await call.answer("To'lov tasdiqlandi!", show_alert=True)
        except Exception as e:
            await call.answer(f"Xato: {e}", show_alert=True)
            
    elif action == 'rej':
        try:
            reject_message = (
                f"⚠️ <b>To'lov tasdiqlanmadi!</b>\n\n"
                f"Kechirasiz, siz yuborgan chek orqali <b>{book_name}</b> kitobi uchun to'lov topilmadi yoki xato chek yuborildi.\n"
                f"Iltimos, pul ko'chirmasini qaytadan tekshirib ko'ring yoki adminga murojaat qiling."
            )
            await bot.send_message(chat_id=buyer_id, text=reject_message, parse_mode="HTML")
            await call.message.edit_caption(caption=call.message.caption + f"\n\n🔴 <b>RAD ETILDI. Xaridorga xabar berildi.</b>", parse_mode="HTML")
            await call.answer("To'lov rad etildi!", show_alert=True)
        except Exception as e:
            await call.answer(f"Xato: {e}", show_alert=True)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
