from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def get_keyboard_sex() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="Я парень")], [KeyboardButton(text="Я девушка")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_age(age: int) -> ReplyKeyboardMarkup | ReplyKeyboardRemove:
    kb = []
    if age != -1:
        kb.append([KeyboardButton(text=str(age))])
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return get_remove_keyboard()


def get_keyboard_descr(registered: bool) -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="Пропустить")]]
    if registered:
        kb.append([KeyboardButton(text="Оставить текущее")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_images(registered: bool, stage: bool) -> ReplyKeyboardMarkup | ReplyKeyboardRemove:
    kb = []
    if registered and not stage:
        kb.append([KeyboardButton(text="Оставить текущее")])
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    if stage:
        kb.append([KeyboardButton(text="Пропустить")])
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return get_remove_keyboard()


def get_keyboard_name(name1: str, name2: str) -> ReplyKeyboardMarkup:
    kb = []
    if len(name1) != 0:
        kb.append([KeyboardButton(text=name1)])
    if len(name2) != 0 and name1 != name2:
        kb.append([KeyboardButton(text=name2)])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_main() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_profile() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="❤️"), KeyboardButton(text="💌"), KeyboardButton(text="👎"), KeyboardButton(text="💤")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_like() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="1"), KeyboardButton(text="2")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_profile_like() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="❤️"), KeyboardButton(text="👎")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_inactive() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="Я вернулся")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_party() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="Создать"), KeyboardButton(text="Вступить")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_keyboard_party_back() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="Назад")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
