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
API_TOKEN = '8829040058:AAHBzigI7ASmqdHJ9DRhzL5KxrmzmpkoEKo'  # Tokeningiz
ADMIN_ID = 651936747  # Sizning Telegram ID raqamingiz

# FSM Storage
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# OBUNACHILAR RO'YXATI
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
    users_list.add(message.from_user.id)
    
    welcome_text = (
        "💳 <b>🇺🇿 My Vocabularies — To'lov tizimiga xush kelibsiz!</b>\n"
        "Kitobga to'lov qilish uchun pastdagi <b>🛍 Buy a Book</b> tugmasini bosing.\n\n"
        "💳 <b>🇬🇧 Welcome to My Vocabularies — Payment Bot!</b>\n"
        "Click the <b>🛍 Buy a Book</b> button below to pay for the book.\n\n"
        "👇 👇 👇"
    )
    await message.reply(welcome_text, reply_markup=main_menu, parse_mode="HTML")

# 2. ADMIN UCHUN STATISTIKA BUYRUG'I
@dp.message_handler(commands=['stat'], state="*")
async def cmd_stat(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply(f"📊 <b>Bot statistikasi:</b>\n\n👥 Jami obunachilar soni: <b>{len(users_list)}</b> ta", parse_mode="HTML")
    else:
        await message.reply("❌ Bu buyruq faqat admin uchun!")

# 3. UNIVERSAL REKLAMA FUNKSIYASI
@dp.message_handler(content_types=[types.ContentType.TEXT, types.ContentType.PHOTO, types.ContentType.VIDEO], state="*")
async def handle_all_messages(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    users_list.add(user_id)

    is_reklama = False
    reklama_text = ""
    media_type = "text"
    file_id = None

    if message.photo and message.caption and message.caption.startswith('/reklama'):
        is_reklama = True
        media_type = "photo"
        file_id = message.photo[-1].file_id
        reklama_text = message.caption.replace('/reklama', '').strip()

    elif message.video and message.caption and message.caption.startswith('/reklama'):
        is_reklama = True
        media_type = "video"
        file_id = message.video.file_id
        reklama_text = message.caption.replace('/reklama', '').strip()

    elif message.text and message.text.startswith('/reklama'):
        is_reklama = True
        media_type = "text"
        reklama_text = message.text.replace('/reklama', '').strip()

    if is_reklama:
        if user_id != ADMIN_ID:
            await message.reply("❌ Bu buyruq faqat admin uchun!")
            return

        if not reklama_text and media_type == "text":
            await message.reply("⚠️ <b>Xato:</b> Reklama matnini yozmadingiz!", parse_mode="HTML")
            return

        send_count = 0
        failed_count = 0

        for obunachi_id in users_list:
            try:
                if media_type == "photo":
                    await bot.send_photo(chat_id=obunachi_id, photo=file_id, caption=reklama_text if reklama_text else None, parse_mode="HTML")
                elif media_type == "video":
                    await bot.send_video(chat_id=obunachi_id, video=file_id, caption=reklama_text if reklama_text else None, parse_mode="HTML")
                else:
                    await bot.send_message(chat_id=obunachi_id, text=reklama_text, parse_mode="HTML")
                send_count += 1
            except Exception:
                failed_count += 1

        await message.reply(
            f"📢 <b>Reklama tarqatish yakunlandi:</b>\n\n"
            f"✅ Yetkazildi: <b>{send_count}</b> ta obunachiga\n"
            f"❌ Yetkazilmadi (bloklaganlar): <b>{failed_count}</b> ta",
            parse_mode="HTML"
        )
        return

    # --- SOTIB OLISH JARRAYONI ---
    if message.text == "📚 Kitob sotib olish":
        await OrderProcess.waiting_for_book_name.set()
        await message.reply("📝 <b>Iltimos, sotib olmoqchi bo'lgan kitobingiz nomini yozing:</b>", reply_markup=cancel_menu, parse_mode="HTML")
        return

    if message.text == "❌ Jarayonni bekor qilish":
        await state.finish()
        await message.reply("🔄 Sotib olish jarayoni bekor qilindi. Bosh menyuga qaytdingiz.", reply_markup=main_menu, parse_mode="HTML")
        return

    current_state = await state.get_state()
    if current_state == OrderProcess.waiting_for_book_name.state:
        if message.text:
            await state.update_data(chosen_book=message.text)
            await OrderProcess.next()
            payment_text = (
                f"🛒 <b>Siz tanlagan kitob:</b> {message.text}\n\n"
                "💳 To'lovni amalga oshirish uchun quyidagi karta raqamiga pul o'tkazing:\n"
                "• <b>Karta raqami:</b> <code>8600 1234 5678 9012</code>\n"
                "• <b>Mulkdor:</b> Eshmatov Toshmat\n"
                "• <b>Narxi:</b> 25,000 so'm\n\n"
                "📥 <b>To'lovdan so'ng:</b> To'lov chekini (skrinshotini) shu yerga rasm ko'rinishida yuboring!"
            )
            await message.reply(payment_text, reply_markup=cancel_menu, parse_mode="HTML")
        return

    if current_state == OrderProcess.waiting_for_screenshot.state:
        if message.photo or (message.document and message.document.mime_type.startswith('image/')):
            user_data = await state.get_data()
            book_name = user_data.get("chosen_book", "Noma'lum kitob")
            full_name = message.from_user.full_name.replace('<', '&lt;').replace('>', '&gt;')
            username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"
            user_caption = message.caption if message.caption else "Izoh qoldirilmadi"
            
            admin_alert = (
                "🔔 <b>Yangi buyurtma va to'lov cheki keldi!</b>\n\n"
                f"👤 <b>Xaridor:</b> {full_name} ({username})\n"
                f"🆔 <b>Telegram ID:</b> <code>{message.from_user.id}</code>\n"
                f"📚 <b>Sotib olmoqchi:</b> <u>{book_name}</u>\n"
                f"📝 <b>Izoh:</b> {user_caption}\n\n"
                "⚠️ Pulni tekshiring va qaror qabul qiling:"
            )

            inline_kb = InlineKeyboardMarkup(row_width=2)
            btn_approve = InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"app_{message.from_user.id}")
            btn_reject = InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rej_{message.from_user.id}")
            inline_kb.add(btn_approve, btn_reject)

            if message.photo:
                file_id = message.photo[-1].file_id
                await bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=admin_alert, reply_markup=inline_kb, parse_mode="HTML")
            else:
                file_id = message.document.file_id
                await bot.send_document(chat_id=ADMIN_ID, document=file_id, caption=admin_alert, reply_markup=inline_kb, parse_mode="HTML")

            await message.reply("⏳ <b>To'lovingiz qabul qilindi va tekshirilmoqda!</b>\nAdministrator tez orada to'lovni tekshiradi.", reply_markup=main_menu, parse_mode="HTML")
            await state.finish()
        else:
            await message.reply("❌ Iltimos, faqat rasm formatidagi chekni yuboring!")
        return

# 4. ADMIN QAROR QABUL QILGANDA (ENG ULTRA-TEZKOR VARIANT)
@dp.callback_query_handler(lambda call: call.data.startswith(('app_', 'rej_')), state="*")
async def admin_decision(call: types.CallbackQuery):
    # ENG MUHIMI: Telegram'ga sarlavhani uzatib, so'rovni darhol tasdiqlaymiz (Sekinlashuvni butunlay yo'qotadi)
    try:
        await call.answer()
    except Exception:
        pass

    data_parts = call.data.split('_')
    action = data_parts[0]
    buyer_id = int(data_parts[1])
    
    book_name = "Tanlangan kitob"
    if call.message.caption and "Sotib olmoqchi:" in call.message.caption:
        try:
            book_name = call.message.caption.split("Sotib olmoqchi:")[1].split("\n")[0].strip()
        except Exception:
            pass

    if action == 'app':
        # Admin xabarini tezkor yangilash va tugmalarni o'chirish
        try:
            await call.message.edit_caption(caption=call.message.caption + f"\n\n🟢 <b>TASDIQLANDI. Kitob ochildi!</b>", reply_markup=None, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Ekranni yangilashda xato: {e}")

        # Orqa fonda foydalanuvchiga yuborish
        try:
            success_message = (
                f"🎉 <b>Ajoyib xabar!</b>\n\n"
                f"✅ Sizning <b>{book_name}</b> uchun qilgan to'lovingiz muvaffaqiyatli tasdiqlandi!\n"
                f"🚀 Biz siz uchun ushbu kitobni ochib qo'ydik. Mini App'ga kirib foydalanishingiz mumkin!"
            )
            await bot.send_message(chat_id=buyer_id, text=success_message, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Xaridorga yuborishda xato: {e}")
            
    elif action == 'rej':
        # Admin xabarini tezkor yangilash va tugmalarni o'chirish
        try:
            await call.message.edit_caption(caption=call.message.caption + f"\n\n🔴 <b>RAD ETILDI. Xaridorga xabar berildi.</b>", reply_markup=None, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Ekranni yangilashda xato: {e}")

        # Orqa fonda foydalanuvchiga yuborish
        try:
            reject_message = (
                f"⚠️ <b>To'lov tasdiqlanmadi!</b>\n\n"
                f"Kechirasiz, siz yuborgan chek orqali <b>{book_name}</b> uchun to'lov topilmadi.\n"
                f"Iltimos, pul ko'chirmasini qaytadan tekshirib ko'ring yoki adminga murojaat qiling."
            )
            await bot.send_message(chat_id=buyer_id, text=reject_message, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Xaridorga yuborishda xato: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
