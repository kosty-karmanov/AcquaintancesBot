from aiogram.client.default import DefaultBotProperties
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import Message, FSInputFile, User
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher
import asyncio

from Database import DataBase
from Profile import Profile
import Keyboards

dp = Dispatcher()
db = DataBase()
bot: Bot = None
registration = {}


async def save_photos(message: Message) -> str:
    photo = sorted(message.photo, key=lambda x: x.height, reverse=True)[0]
    file = await bot.get_file(photo.file_id)
    await bot.download_file(file_path=file.file_path, destination=rf"./photos/{file.file_id}.png")
    return f"{file.file_id}"


async def load_photos(media_group, data: str):
    for photo in data.split(";"):
        media_group.add_photo(media=FSInputFile(rf"./photos/{photo}.png"))
    return media_group


async def get_username(user_id: int) -> str:
    members = await bot.get_chat_member(user_id=user_id, chat_id=user_id)
    name = db.get_form(user_id)[1]
    return hlink(name, f'https://t.me/{members.user.username}')


async def send_profile(prof: Profile, reciew: int = None, is_like: bool = False) -> None:
    if is_like:
        text = f"Кому-то понравилась твоя анкета:\n\n{prof.get_text()}"
        msg = db.get_like_message(prof.user_id, reciew)
        if len(msg) != 0:
            text += f"\n\nСообщение для тебя💌: {msg}"
    else:
        text = prof.get_text()
    media_group = MediaGroupBuilder(caption=text)
    await load_photos(media_group, prof.photos)
    if reciew is not None:
        await bot.send_media_group(chat_id=reciew, media=media_group.build())
        return
    await bot.send_media_group(chat_id=prof.user_id, media=media_group.build())


async def send_registration_msg(from_user: User) -> None:
    await bot.send_message(chat_id=from_user.id, text="Как тебя зовут?",
                           reply_markup=Keyboards.get_keyboard_name(from_user.first_name, (
                               db.get_form(from_user.id)[1] if db.has_form(from_user.id) else "")))


async def send_main_msg(id: int) -> None:
    db.set_state(id, 1)
    await bot.send_message(chat_id=id, text="1. Смотреть анкеты.\n2. Заполнить анкету заново.\n3. Отключить анкету.",
                           reply_markup=Keyboards.get_keyboard_main())


async def send_like_msg(id: int) -> None:
    state = db.get_state(id)
    if state == "looking":
        db.set_state(id, 5)
        await bot.send_message(chat_id=id,
                               text="Кто-то тобой заинтересовался! Заканчивай с анкетой выше и посмотрим кто там")
    elif state == "main":
        likes = db.get_likes(id)
        db.set_state(id, 3)
        await bot.send_message(chat_id=id,
                               text=f"Ты понравился {len(likes)} чел., показать?\n\n1. Показать.\n2. Не хочу больше никого смотреть.",
                               reply_markup=Keyboards.get_keyboard_like())


async def send_besties_profile_msg(id: int) -> None:
    bestie_id = db.get_likes(id)
    if len(bestie_id) == 0:
        await send_main_msg(id)
        return
    db.set_target(id, bestie_id[0])
    db.mark_like(bestie_id[0], id)
    await bot.send_message(chat_id=id, text="✨🔍",
                           reply_markup=Keyboards.get_keyboard_profile_like())
    while db.is_mutually(id, bestie_id[0]):
        await send_profile(db.get_profile(bestie_id[0]), id)
        await bot.send_message(chat_id=id,
                               text=f"Есть взаимная симпатия! Начинай общаться 👉 {await get_username(bestie_id[0])}",
                               disable_web_page_preview=True)
        bestie_id = db.get_likes(id)
        if len(bestie_id) == 0:
            break
        db.set_target(id, bestie_id[0])
        db.mark_like(bestie_id[0], id)
    if len(bestie_id) == 0:
        await send_main_msg(id)
        return
    await send_profile(db.get_profile(bestie_id[0]), id, True)


async def find_bestie(id: int) -> None:
    bestie_id = db.get_bestie(id)
    if bestie_id == 0:
        await bot.send_message(chat_id=id, text="Извини, сейчас никого не могу найти :(")
        await send_main_msg(id)
        return
    await send_profile(db.get_profile(bestie_id), id)
    db.set_state(id, 4)
    db.set_target(id, bestie_id)


async def send_party_selection_msg(id: int) -> None:
    db.set_state(id, 7)
    await bot.send_message(chat_id=id,
                           text="Вы не состоите в пати!\nВступите или создайте его чтобы начать знакомиться",
                           reply_markup=Keyboards.get_keyboard_party())


async def send_party_creation_msg(id: int) -> None:
    db.set_state(id, 9)
    await bot.send_message(chat_id=id, text="Опишите вашу группу. Что вас объединяет?",
                           reply_markup=Keyboards.get_keyboard_party_back())


async def send_party_joining_msg(id: int) -> None:
    db.set_state(id, 8)
    await bot.send_message(chat_id=id, text="Отправьте в чат код группы или перейдите по ссылке-приглашению",
                           reply_markup=Keyboards.get_keyboard_party_back())


async def registration_step(prof: Profile, msg: Message) -> None:
    if prof.stage == 0:
        data = msg.text
        try:
            prof.validate_name(data)
        except RuntimeError as e:
            await bot.send_message(chat_id=prof.user_id, text=str(e))
            return
        prof.stage += 1
        cur_age = -1
        print(db.has_form(prof.user_id))
        if db.has_form(prof.user_id):
            cur_age = db.get_form(prof.user_id)[2]
        await bot.send_message(chat_id=prof.user_id, text="Сколько тебе лет?",
                               reply_markup=Keyboards.get_keyboard_age(cur_age))
    elif prof.stage == 1:
        data = msg.text
        try:
            prof.validate_age(data)
        except RuntimeError as e:
            await bot.send_message(chat_id=prof.user_id, text=str(e))
            return
        prof.stage += 1
        await bot.send_message(chat_id=prof.user_id, text="Теперь определимся с полом",
                               reply_markup=Keyboards.get_keyboard_sex())
    elif prof.stage == 2:
        data = msg.text
        try:
            prof.validate_sex(data)
        except RuntimeError as e:
            await bot.send_message(chat_id=prof.user_id, text=str(e))
            return
        prof.stage += 1
        await bot.send_message(chat_id=prof.user_id,
                               text="Расскажи о себе и кого хочешь найти, чем предлагаешь заняться",
                               reply_markup=Keyboards.get_keyboard_descr(db.has_form(prof.user_id)))
    elif prof.stage == 3:
        data = msg.text
        if data == "Пропустить":
            data = ""
        if data == "Оставить текущее":
            data = db.get_form(prof.user_id)[4]
        try:
            prof.validate_descr(data)
        except RuntimeError as e:
            await bot.send_message(chat_id=prof.user_id, text=str(e))
            return
        prof.stage += 1
        await bot.send_message(chat_id=prof.user_id,
                               text="Теперь пришли свои фото (до 3), их будут видеть другие пользователи",
                               reply_markup=Keyboards.get_keyboard_images(db.has_form(prof.user_id), False))
    else:
        if msg.photo is not None:
            photos = await save_photos(msg)
            if prof.stage != 4:
                prof.photos += f";{photos}"
            else:
                prof.photos = photos
            prof.stage += 1
        elif msg.text is not None:
            if msg.text == "Оставить текущее":
                prof.photos = db.get_form(msg.from_user.id)[3]
                prof.stage = 7
            elif msg.text == "Пропустить":
                prof.stage = 7
            else:
                await bot.send_message(chat_id=prof.user_id, text="Такого варианта нет :(")
                return
        else:
            await bot.send_message(chat_id=prof.user_id, text="Такого варианта нет :(")
            return
        if prof.stage == 7:
            db.set_profile(prof)
            registration.pop(prof.user_id)
            await send_profile(prof)
            await send_main_msg(prof.user_id)
        else:
            await bot.send_message(chat_id=prof.user_id,
                                   text=f"❤️ Можешь отправить еще {7 - prof.stage} фото",
                                   reply_markup=Keyboards.get_keyboard_images(db.has_form(prof.user_id), True))


@dp.message(CommandStart())
async def command_start(message: Message, command: CommandObject) -> None:
    first = False
    if not db.is_exists(message.from_user.id):
        first = True
        db.add_user(message.from_user.id)
    if command.args is not None:
        party = command.args
        if db.is_party_exists(party):
            db.set_party(message.from_user.id, party)
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f"Вы успешно вступили в пати!\nОписание:\n{db.get_party_desc(party)}")
        else:
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f"Такого пати не существует!")
    if first:
        await send_registration_msg(message.from_user)
        registration[message.from_user.id] = Profile([message.from_user.id])
    else:
        await send_main_msg(message.from_user.id)


@dp.message(Command("myprofile"))
async def command_myprofile(message: Message) -> None:
    if not db.has_form(message.from_user.id):
        await send_registration_msg(message.from_user)
        registration[message.from_user.id] = Profile([message.from_user.id])
        return
    if message.from_user.id in registration:
        registration.pop(message.from_user.id)
    await send_profile(db.get_profile(message.from_user.id))
    await send_main_msg(message.from_user.id)


@dp.message(Command("party_info"))
async def command_party_info(message: Message) -> None:
    if message.from_user.id in registration:
        await bot.send_message(chat_id=message.from_user.id, text="Вы проходите регистрацию, не отвлекайтесь!")
        return
    if db.has_party(message.from_user.id):
        party = db.get_party(message.from_user.id)
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"Описание: {db.get_party_desc(party)}\nУчастников: {db.get_party_members(party)} шт.\nКод: `{party}`\nСсылка: https://t.me/Ffgggfbot?start={party}", parse_mode="MARKDOWN")
    else:
        await send_party_selection_msg(message.from_user.id)


@dp.message(Command("party_leave"))
async def command_party_leave(message: Message) -> None:
    if message.from_user.id in registration:
        await bot.send_message(chat_id=message.from_user.id, text="Вы проходите регистрацию, не отвлекайтесь!")
        return
    db.set_party(message.from_user.id, "")
    await send_party_selection_msg(message.from_user.id)


@dp.message()
async def echo(message: Message) -> None:
    if not db.is_exists(message.from_user.id):
        db.add_user(message.from_user.id)
    if message.from_user.id in registration:
        profile: Profile = registration[message.from_user.id]
        await registration_step(profile, message)
        return
    if not db.has_form(message.from_user.id):
        await send_registration_msg(message.from_user)
        registration[message.from_user.id] = Profile([message.from_user.id])
        return
    state = db.get_state(message.from_user.id)
    if not db.has_party(message.from_user.id) and "party" not in state:
        await send_party_selection_msg(message.from_user.id)
        return
    if message.text is None:
        return
    if state == "main":
        if message.text == "1":
            if len(db.get_likes(message.from_user.id)) != 0:
                db.set_state(message.from_user.id, 3)
                await send_besties_profile_msg(message.from_user.id)
                return
            await bot.send_message(chat_id=message.from_user.id, text="✨🔍",
                                   reply_markup=Keyboards.get_keyboard_profile())
            await find_bestie(message.from_user.id)
        elif message.text == "2":
            await send_registration_msg(message.from_user)
            registration[message.from_user.id] = Profile([message.from_user.id])
        elif message.text == "3":
            db.set_active(message.from_user.id, 0)
            db.set_state(message.from_user.id, 2)
            await bot.send_message(chat_id=message.from_user.id,
                                   text="Хорошо. Вы отключили свою анкету. Если захотите вернуться - напишите",
                                   reply_markup=Keyboards.get_keyboard_inactive())
        else:
            await bot.send_message(chat_id=message.from_user.id, text="Такого варианта нет",
                                   reply_markup=Keyboards.get_keyboard_main())
    elif state == "looking" or state == "lastprofile":
        if message.text == "❤️":
            db.like(message.from_user.id, db.get_target(message.from_user.id), "")
            await send_like_msg(db.get_target(message.from_user.id))
            if state == "looking":
                await find_bestie(message.from_user.id)
            else:
                db.set_state(message.from_user.id, 3)
                await send_besties_profile_msg(message.from_user.id)
        elif message.text == "💌":
            await bot.send_message(chat_id=message.from_user.id,
                                   text="Отправь в чат сообщение, которое хочешь передать")
            db.set_state(message.from_user.id, 6)
        elif message.text == "👎":
            db.ignore(message.from_user.id, db.get_target(message.from_user.id))
            if state == "looking":
                await find_bestie(message.from_user.id)
            else:
                db.set_state(message.from_user.id, 3)
                await send_besties_profile_msg(message.from_user.id)
        elif message.text == "💤":
            await bot.send_message(chat_id=message.from_user.id, text="Подождем пока кто-то увидит твою анкету")
            if state == "looking":
                await send_main_msg(message.from_user.id)
            else:
                db.set_state(message.from_user.id, 3)
                await send_besties_profile_msg(message.from_user.id)
        else:
            await bot.send_message(chat_id=message.from_user.id, text="Такого варианта нет",
                                   reply_markup=Keyboards.get_keyboard_profile())
    elif state == "inactive":
        if message.text == "Я вернулся":
            db.set_active(message.from_user.id, 1)
            await bot.send_message(chat_id=message.from_user.id, text="С возвращением!")
            await send_main_msg(message.from_user.id)
        else:
            await bot.send_message(chat_id=message.from_user.id, text="Такого варианта нет",
                                   reply_markup=Keyboards.get_keyboard_inactive())
    elif state == "like":
        if message.text == "1":
            await send_besties_profile_msg(message.from_user.id)
        elif message.text == "2":
            await bot.send_message(chat_id=message.from_user.id, text="Можете отключить вашу анкету в главном меню")
            await send_main_msg(message.from_user.id)
        elif message.text == "❤️" or message.text == "👎":
            if message.text == "👎":
                db.ignore(message.from_user.id, db.get_target(message.from_user.id))
            else:
                db.like(message.from_user.id, db.get_target(message.from_user.id), "")
                await send_like_msg(db.get_target(message.from_user.id))
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f"Отлично! Надеюсь хорошо проведете время ;) Начинай общаться 👉 {await get_username(db.get_target(message.from_user.id))}",
                                       disable_web_page_preview=True)
            await send_besties_profile_msg(message.from_user.id)
        else:
            await bot.send_message(chat_id=message.from_user.id, text="Такого варианта нет",
                                   reply_markup=Keyboards.get_keyboard_like())
    elif state == "message2bestie":
        if len(message.text) > 300:
            await bot.send_message(chat_id=message.from_user.id,
                                   text="Сообщение слишком длинное, максимум 300 символов. Введите сообщение заново.")
            return
        db.like(message.from_user.id, db.get_target(message.from_user.id), message.text)
        await send_like_msg(db.get_target(message.from_user.id))
        if db.is_mutually(message.from_user.id, db.get_target(message.from_user.id)):
            await send_besties_profile_msg(message.from_user.id)
        else:
            await find_bestie(message.from_user.id)
    elif state == "party_selection":
        if message.text == "Создать":
            await send_party_creation_msg(message.from_user.id)
        elif message.text == "Вступить":
            await send_party_joining_msg(message.from_user.id)
        else:
            await bot.send_message(chat_id=message.from_user.id, text="Такого варианта нет",
                                   reply_markup=Keyboards.get_keyboard_party())
    elif state == "party_joining":
        if db.is_party_exists(message.text):
            db.set_party(message.from_user.id, message.text)
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f"Вы успешно вступили в пати!\nОписание:\n{db.get_party_desc(message.text)}")
            await send_main_msg(message.from_user.id)
        elif message.text == "Назад":
            await send_party_selection_msg(message.from_user.id)
        else:
            await bot.send_message(chat_id=message.from_user.id,
                                   text="Такого пати не существует :(",
                                   reply_markup=Keyboards.get_keyboard_party_back())
    elif state == "party_creation":
        if message.text == "Назад":
            await send_party_selection_msg(message.from_user.id)
            return
        if len(message.text) > 300:
            await bot.send_message(chat_id=message.from_user.id,
                                   text="Слишком длинно! Максимум 300 символов")
        party = db.create_party(message.from_user.id, message.text)
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"Вы успешно создали пати\nВот ссылка на ваше пати: https://t.me/Ffgggfbot?start={party}")
        await send_main_msg(message.from_user.id)


async def main() -> None:
    global bot
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


asyncio.run(main())
