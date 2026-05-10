from aiogram.fsm.state import StatesGroup, State


class CheckTest(StatesGroup):
    answers = State()
    answers2 = State()


class ReNameUser(StatesGroup):
    wait_new_name = State()