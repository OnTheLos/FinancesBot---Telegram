import os

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from data.scripts.DB_users import get_active_users, set_inactive_user, get_users_txt
from data.scripts.DB_banned import set_ban, set_unban
from data.scripts.DB_database import delete_table

from components.keyboards import ActionCallback
from components.states import Distribution
from components.filters import AdminFilter, update_banned


rt = Router()
rt.message.filter(AdminFilter())
rt.callback_query.filter(AdminFilter())


@rt.message(Command('admin'))
async def admin(message: Message):
    buttons = [
    [
        InlineKeyboardButton(text='Получить активных', callback_data=ActionCallback(action='gettxt_active').pack()),
        InlineKeyboardButton(text='Получить неактивных', callback_data=ActionCallback(action='gettxt_inactive').pack())
    ],
    [
        InlineKeyboardButton(text='Сделать рассылку', callback_data=ActionCallback(action='distribute').pack())
    ],
    [
        InlineKeyboardButton(text='В главное меню', callback_data=ActionCallback(action='back_to_menu').pack())
    ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)  
    await message.answer(text='Выберите действие:',
                         reply_markup=kb)
    

@rt.callback_query(ActionCallback.filter(F.action == 'distribute'))
async def distribute(call: CallbackQuery, state: FSMContext):
    buttons = [
    [
        InlineKeyboardButton(text='Назад', callback_data=ActionCallback(action='back_to_admin_st').pack())
    ],
    [
        InlineKeyboardButton(text='В главное меню', callback_data=ActionCallback(action='back_to_menu_st').pack())
    ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons) 

    await call.message.edit_text(text='Введите текст рассылки',
                                 reply_markup=kb)
    await state.set_state(Distribution.message)


@rt.message(Distribution.message)
async def distribute_(message: Message, state: FSMContext):
    text = message.html_text
    rm = message.reply_markup
    await state.update_data(dist_text=text, dist_rm=rm)

    buttons = [
        InlineKeyboardButton(text='Подтвердить', callback_data='confirm_distribute'),
        InlineKeyboardButton(text='Отменить', callback_data=ActionCallback(action='back_to_admin_st').pack())
    ]

    if message.photo:
        photo_id = message.photo[-1].file_id
        await state.update_data(dist_phid=photo_id)
    else:
        await state.update_data(dist_phid=None)

    if rm:
        existing_buttons = rm.inline_keyboard
        new_buttons = existing_buttons + [buttons]
    else:
        new_buttons = [buttons]

    if message.photo:
        await message.answer_photo(photo=photo_id, caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[*new_buttons]))
    else:
        await message.answer(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[*new_buttons]))

    await state.update_data(dist_text=text, dist_rm=rm)


@rt.callback_query(F.data == 'confirm_distribute')
async def confirm_distribute(call: CallbackQuery, state: FSMContext):
    from main import bot

    users = get_active_users()
    data = await state.get_data()   # {dist_text, dist_rm, (dist_phid)}
    act = 0
    inact = 0
    for i in users:
        try:
            if not data['dist_phid']:
                await bot.send_message(chat_id=i,
                                    text=data['dist_text'],
                                    reply_markup=data['dist_rm'])
            else:
                await bot.send_photo(chat_id=i,
                                    photo=data['dist_phid'],
                                    caption=data['dist_text'],
                                    reply_markup=data['dist_rm'])
            act += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            set_inactive_user(i)
            inact += 1

    await call.message.answer(text=f'Рассылка завершена.\n\nПолучили рассылку: {act}\nНе получили рассылку: {inact}')
    await call.answer()
    await admin(call.message)


@rt.callback_query(lambda c: 'gettxt' in c.data)
async def gettxt(call: CallbackQuery):
    data = call.data.split('_')[1]
    a = get_users_txt(data)
    if a:
        file = FSInputFile(f'{data}_users.txt')
        try: 
            await call.message.answer_document(file)
        except TelegramBadRequest:
            await call.message.answer(text='Файл пуст')
        os.remove(f'{data}_users.txt')
        await call.answer()
        await admin(call.message)


async def db_backup():
    from main import bot
    file = FSInputFile(f'data/database/database.db')
    await bot.send_document(chat_id=524520741,
                            document=file)


@rt.message(Command('ban'))
async def ban(message: Message, command: CommandObject):
    id = command.args

    a = set_ban(id)
    b = update_banned()

    if a and b:
        await message.answer(text=f'Пользователь {id} забанен')
        await admin(message)


@rt.message(Command('unban'))
async def unban(message: Message, command: CommandObject):
    id  = command.args

    a = set_unban(id)
    b = update_banned()

    if a and b:
        await message.answer(text=f'Пользователь {id} разбанен')
        await admin(message)


@rt.message(Command('deltab'))
async def deltab(message: Message, command: CommandObject):
    id = command.args

    a = delete_table(id)

    if a:
        await message.answer(text='Таблица удалена')
        await admin(message)


@rt.callback_query(ActionCallback.filter(F.action == 'back_to_admin_st'))
async def back_to_admin_st(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await admin(call.message)
    await call.answer()