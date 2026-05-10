import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from states import CheckTest, ReNameUser
from config.loader import db
from keyboards import update_name, user_menu, back_btn, back_btn_reply, user_menu

rt = Router()

# userlar
# Test tekshirish
@rt.message(F.text == "✅ Javobni tekshirish")
async def ask_test_code(message: Message, state: FSMContext):
    await message.answer(
        "<b>✅ Javobni tekshirish</b>\n\n"
        "Test javoblaringizni namunadagi kabi yuboring:\n\n"
        "<i>test_kodi*abcd...</i>\n\n"
        "<b>Namuna:</b> <i>7*abcdba</i>",
        reply_markup=back_btn_reply
    )
    await state.set_state(CheckTest.answers)

@rt.callback_query(F.data == "check_subs:tekshir")
async def ask_test_code_(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer(
        "<b>✅ Javobni tekshirish</b>\n\n"
        "Test javoblaringizni namunadagi kabi yuboring:\n\n"
        "<i>test_kodi*abcd...</i>\n\n"
        "<b>Namuna:</b> <i>125*abcdba</i>",
        reply_markup=back_btn_reply
    )
    await state.set_state(CheckTest.answers)

@rt.message(F.text == "↩️ Orqaga", StateFilter(CheckTest.answers, CheckTest.answers2))
async def back_to_user_menu(message: Message, state: FSMContext):
    await message.answer(
        "<b>Javobni tekshirish</b> bekor qilindi.", reply_markup=user_menu)
    await state.clear()


async def process_test_checking(message: Message, state: FSMContext, test, user_ans_raw: str):
    correct_ans = "".join(re.findall(r'[a-z]', test[2].lower()))
    user_ans = "".join(re.findall(r'[a-z]', user_ans_raw.lower()))

    total = len(correct_ans)
    correct = 0

    for i in range(total):
        if i < len(user_ans) and user_ans[i] == correct_ans[i]:
            correct += 1

    percentage = (correct / total) * 100 if total > 0 else 0

    already_done = await db.check_user_finished(message.from_user.id, test[0])
    if already_done:
        await db.update_result(message.from_user.id, test[0], f"{correct}/{total}", int(percentage))
    else:
        await db.add_result(message.from_user.id, test[0], f"{correct}/{total}", int(percentage))

    await message.answer(
        f"🏁 <b>Sizning natijangiz:</b>\n\n"
        f"📝 <b>Test:</b> {test[1]}\n"
        f"✅ <b>To'g'ri:</b> {correct} ta\n"
        f"❌ <b>Xato:</b> {total - correct} ta\n"
        f"📊 <b>Foiz:</b> {int(percentage)}%\n\n",
        reply_markup=user_menu
    )
    await state.clear()

@rt.message(F.text, CheckTest.answers)
async def get_answers_step1(message: Message, state: FSMContext):
    if message.text in ["📊 Natijalarim", "👤 Profile", "ℹ️ Bot haqida", "✅ Javobni tekshirish"]:
        await state.clear()
        await message.answer("Amal bekor qilindi.", reply_markup=user_menu)
        return

    msg = message.text.strip().lower()

    if msg.isdigit():
        test_code = int(msg)
        user_ans_raw = ''
    elif "*" in msg:
        try:
            test_code_str, user_ans_raw = msg.split("*", 1)
            test_code = int(test_code_str)
        except ValueError:
            await message.answer("❌ <b>Test kodini tekshirib qaytadan yuboring!</b>\n<i>Test kodi faqat raqamlardan iborat bo'lishi kerak!</i>")
            return
    else:
        await message.answer("❌ <b>Xato format!</b>\n<i>Iltimos namunadagi kabi yuboring</i>\n<b>Namuna:</b> <i>7*abcd</i>")
        return

    test = await db.get_test(test_code)
    if not test:
        await message.answer(f"❌ <b>Test topilmadi!</b>\n<i>Iltimos test kodini tekshirib qaytadan yuboring!</i>")
        return

    # Holatni tekshirish
    if test[3] == 'waiting':
        await message.answer("⚠️ <b>Kechirasiz, test hali boshlanmagan.</b>", reply_markup=user_menu)
        await state.clear()
        return
    if test[3] == 'closed':
        await message.answer("⚠️ <b>Kechirasiz, test yakunlangan.</b>", reply_markup=user_menu)
        await state.clear()
        return

    # Agar faqat kod bo'lsa, ikkinchi bosqichga o'tamiz
    if not user_ans_raw:
        await message.answer(f"✅ <b>Kod qabul qilindi:</b> {test_code}\nJavoblarni yuboring:", reply_markup=back_btn_reply)
        await state.set_data({"test_code":test_code})
        await state.set_state(CheckTest.answers2)
    else:
        await process_test_checking(message, state, test, user_ans_raw)


@rt.message(F.text, CheckTest.answers2)
async def get_answers(message: Message, state: FSMContext):
    if message.text in ["📊 Natijalarim", "👤 Profile", "ℹ️ Bot haqida", "✅ Javobni tekshirish"]:
        await state.clear()
        await message.answer("✅ Javobni tekshirish amali bekor qilindi.", reply_markup=user_menu)
        return

    user_ans_raw = message.text.strip().lower()
    data = await state.get_data()
    test_code = data.get("test_code", 10000)

    test = await db.get_test(test_code)
    if not test:
        await message.answer(f"❌ <b>Test topilmadi!</b>\n<i>Iltimos test kodini tekshirib qaytadan yuboring!</i>")
        return
    
    if test[3] == 'waiting':
        await message.answer("⚠️ <b>Kechirasiz, test hali boshlanmagan.</b>")
        return
    if test[3] == 'closed':
        await message.answer("⚠️ <b>Kechirasiz, test yakunlandi. Siz kech qoldingiz.</b>")
        return

    await process_test_checking(message, state, test, message.text)


@rt.message(F.text == "📊 Natijalarim")
async def send_results(message: Message):
    results = await db.get_user_results(message.from_user.id)
    if not results:
        await message.answer("📭 <b>Sizda hali natijalar yo'q.</b>")
        return

    text = "📊 <b>Sizning natijalaringiz:</b>\n\n"
    for i, res in enumerate(results, 1):
        text += f"{i}. {res[0]} | <b>{res[1]}</b> ({int(res[2])}%)\n"
    
    await message.answer(text)


@rt.message(F.text == "👤 Profile")
async def send_profile(message: Message):
    user = await db.get_user(message.from_user.id)
    res_count = await db.get_user_results_count(message.from_user.id)

    joined_date = "None"
    if user[3]:
        joined_date = user[3].split(' ')[0]
    
    text = (
        f"👤 <b>Sizning profilingiz</b>\n\n"
        f"<b>Ism:</b> {user[1]}\n"
        f"<b>Topshirilgan testlar:</b> {res_count} ta\n"
        f"<b>Botga a'zo bo'lingan:</b> {joined_date}\n"
    )
    await message.answer(text, reply_markup=update_name)


@rt.message(F.text == "ℹ️ Bot haqida")
async def about_bot(message: Message):
    await message.answer(
        "ℹ️ <b>Online Test Bot</b>\n\n"
        "Ushbu bot orqali testlar yaratish va ularni masofaviy "
        "tekshirish imkoniyati mavjud.\n\n"
    )


@rt.callback_query(F.data == "rename_user")
async def ask_new_name(call:CallbackQuery, state:FSMContext):
    await call.message.delete()
    await call.message.answer("<b>✍️ Ism o'zgartirish</b>\n\n"
                              "Yangi ismingizni kiriting", reply_markup=back_btn)
    await state.set_state(ReNameUser.wait_new_name)


@rt.callback_query(F.data == "back_", ReNameUser.wait_new_name)
async def update_user_name(call:CallbackQuery, state:FSMContext):
    await call.message.delete()
    await call.message.answer(f"<b>Ism o'zgartirilmadi.</b>")
    await state.clear()


@rt.message(F.text, ReNameUser.wait_new_name)
async def update_user_name(message:Message, state:FSMContext):
    tg_id = message.from_user.id
    name = message.text
    await db.update_fullname(tg_id, name)
    await message.answer(f"Ismingiz <b>{name}</b> - ga o'zgartirildi ✅")
    await state.clear()