from datetime import datetime
import pytz
from html import escape

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from keyboards import back_btn_reply, test_start_btn, currentResults, refresh_current_results, ownerMenu
from states import CreateTest
from filters import IsAdmins
from data.loader import db
from utils.secondary_funk import make_results_list, format_answers

rt = Router()
rt.message.filter(IsAdmins())
rt.callback_query.filter(IsAdmins())


# TEST yaratish
@rt.message(F.text == "➕ Test yaratish")
async def create_test(message:Message, state:FSMContext):
    await message.answer("<b>Test nomini kiriting:</b>\n\n<b>Namuna:</b> <i>Matematika</i>", reply_markup=back_btn_reply)
    await state.set_state(CreateTest.title)


@rt.message(F.text == "↩️ Orqaga", StateFilter(CreateTest.title, CreateTest.answers))
async def add_test_back_(message:Message, state:FSMContext):
    user_id = message.from_user.id
    await message.answer("<b>Test yaratish bekor qilindi.</b>", reply_markup=ownerMenu(user_id))
    await state.clear()


@rt.message(F.text, CreateTest.title)
async def get_new_test_name(message:Message, state:FSMContext):
    await message.answer(f"<b>{message.text}</b> testi uchun javoblarni yuboring:\n\n<b>Namuna:</b>\n<i>abcd...\nyoki\n1a2b3c4d...</i>", reply_markup=back_btn_reply)
    await state.set_data({"test_title": message.text})
    await state.set_state(CreateTest.answers)


@rt.message(F.text, CreateTest.answers)
async def get_new_test_answer(message:Message, state:FSMContext):
    data = await state.get_data()
    test_title = data.get("test_title", "Nomsiz test")

    tashkent_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(tashkent_tz)
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")

    user = await db.get_user(message.from_user.id)
    test_code = await db.add_test(test_title, message.text.lower(), user[2], created_at)

    sana = now.strftime("%d.%m.%Y")
    vaqt = now.strftime("%H:%M")

    user_id = message.from_user.id
    await message.answer("<b>Test yaratildi ✅</b>", reply_markup=ownerMenu(user_id))
    await message.answer(f"<b>✍️ Test:</b> {test_title}\n"
                         f"<b>👨‍🏫 Muallif:</b> {user[1]}\n"
                         f"<b>🔢 Test kodi:</b> <code>{test_code}</code>\n"
                         f"<b>❓ Savollar:</b> {len(message.text)} ta\n"
                         "<b>⏳ Holati:</b> boshlanmagan\n\n"
                         f"<i>📆 {sana} ⏰ {vaqt}</i>",
                         reply_markup=test_start_btn(test_code))
    await state.clear()
    

@rt.callback_query(F.data.startswith("start_test_"))
# @rt.callback_query(F.data.startswith("start_refresh_test_"))
async def start_test(call:CallbackQuery):
    if call.data.startswith("start_refresh_test_"):
        test_code = call.data.split('_')[3]
        await db.del_results(int(test_code))
    else:
        test_code = call.data.split('_')[2]
    

    await db.test_update_status(test_code, "active")
    test = await db.get_test(int(test_code))
    test_title = test[1]
    tests = test[2]
    await call.message.delete()
    await call.message.answer(f"<b>🔔 {test_title}</b> testi boshlandi.\n\n"
                              f"<b>🔢 Test kodi:</b> <code>{test_code}</code>\n"
                              f"<b>❓ Savollar:</b> {len(tests)} ta\n"
                              "<b>⏳ Holati:</b> boshlangan\n\n",
                              reply_markup=currentResults(test_code))


@rt.callback_query(F.data.startswith("current_results_"))
async def current_results_info(call:CallbackQuery):
    test_code = call.data.split('_')[2]
    results  = await db.get_results_with_ids(int(test_code))

    matn = escape(make_results_list(results))

    await call.message.delete()
    await call.message.answer("<b>📈 Joriy Natijalar</b>\n\n"
                              f"<b>🔢 Test kodi:</b> <code>{test_code}</code>\n"
                              f"<b>👥 Qatnashuvchilar:</b> {len(results)} ta\n"
                              "<b>⏳ Holati:</b> boshlangan\n\n"
                              "<b>Natijalar:</b>\n"
                              "---------------------\n"
                              f"{matn}",
                              reply_markup=refresh_current_results(test_code))


@rt.callback_query(F.data.startswith("refresh_"))
async def current_info(call:CallbackQuery):
    test_code = call.data.split('_')[1]
    results  = await db.get_results_with_ids(int(test_code))

    matn = escape(make_results_list(results))
    
    await call.message.delete()
    await call.message.answer("<b>📈 Joriy Natijalar</b>\n\n"
                            f"<b>🔢 Test kodi:</b> <code>{test_code}</code>\n"
                            f"<b>👥 Qatnashuvchilar:</b> {len(results)} ta\n"
                            "<b>⏳ Holati:</b> boshlangan\n\n"
                            "<b>Natijalar:</b>\n"
                            "---------------------\n"
                            f"{matn}",
                            reply_markup=refresh_current_results(test_code))


@rt.callback_query(F.data.startswith("stop_test_"))
async def finished_test_ans(call: CallbackQuery):
    test_code = int(call.data.split('_')[2])
    await db.test_update_status(test_code, "closed")

    test = await db.get_test(test_code)
    results = await db.get_results_with_ids(test_code)
    
    if not test:
        await call.answer("Xatolik: Test topilmadi!")
        return

    test_title = test[1]
    correct_ans_formatted = format_answers(test[2])
    participants_count = len(results)

    # userlarga test yakunlanganligi haqida habar berish
    for index, row in enumerate(results):
        user_tg_id, full_name, user_res, percent = row

        place = index + 1
        congrats = ""
        if place == 1:
            congrats = "🥇 <b>Tabriklaymiz! Siz 1-o'rinni egalladingiz!</b> 🎉\n\n"
        elif place == 2:
            congrats = "🥈 <b>Ajoyib! Siz 2-o'rinni egalladingiz!</b> 🎊\n\n"
        elif place == 3:
            congrats = "🥉 <b>Yaxshi natija! Siz 3-o'rinni egalladingiz!</b> ✨\n\n"
        else:
            congrats = f"📊 Sizning o'rningiz: <b>{place}-o'rin</b>\n\n"

        personal_msg = (
            f"🏁 <b>{escape(test_title)}</b> testi yakunlandi.\n\n"
            f"{congrats}"
            f"📊 <b>Natijangiz:</b> {user_res} ({int(percent)}%)\n\n"
            f"✅ <b>To'g'ri javoblar:</b>\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
            f"<code>{correct_ans_formatted}</code>"
        )
        
        try:
            if place ==1 :
                await call.bot.send_message(chat_id=user_tg_id, text='🏆')
            elif place <=3 :
                await call.bot.send_message(chat_id=user_tg_id, text='🎉')
            await call.bot.send_message(chat_id=user_tg_id, text=personal_msg)
        except Exception as e:
            print(f"Xabar yuborilmadi {user_tg_id}: {e}")

    # adminga xabar.
    total_percentage = 0
    if participants_count > 0:
        total_percentage = sum(row[3] for row in results) / participants_count
    
    matn = escape(make_results_list(results))
    if not matn:
        matn = "Ishtirokchilar mavjud emas."
    
    response_text = (
        f"🏁 <b>{test_title} testi yakunlandi.</b>\n\n"
        f"<b>🔢 Test kodi:</b> <code>{test_code}</code>\n"
        f"<b>👥 Qatnashganlar:</b> {participants_count} ta\n"
        f"<b>📊 Umumiy o'rtacha natija:</b> {total_percentage:.1f}%\n\n"
        f"<b>Natijalar:</b>\n"
        f"---------------------\n"
        f"{matn}"
    )
    
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(response_text)