import os

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from components.states import AddOperation
from components.keyboards import ActionCallback

from data.scripts.DB_database import get_categories, get_database_xlsx, operation_add

from .RT_start import start


rt = Router()


@rt.callback_query(lambda c: '_addoperation' in c.data)
async def addoperation(call: CallbackQuery):
    calldata = call.data.split(':')[1]
    data = calldata.split('_')
    if data[0] == 'in':
        op = '+'
    else: op = '-'

    id = call.from_user.id
    a = get_categories(id, op)

    if a:
        bd = InlineKeyboardBuilder()
        [bd.add(InlineKeyboardButton(
            text=f'"{i}"', 
            callback_data=f'adop_{op}_{id}_{i}'))
            for i in a]
        if len(a) >= 10:
            bd.adjust(2)
        else:
            bd.adjust(1)
        bd.row(InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_menu').pack()))
        
        await call.message.edit_text(text='Выберите категорию:', reply_markup=bd.as_markup())
        await call.answer()

    else:
        await call.answer(text='Сначала вам нужно добавить категорию')


@rt.callback_query(lambda c: 'adop' in c.data)
async def op_data(call: CallbackQuery, state: FSMContext):
    buttons = [
    [
        InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_menu_st').pack())
    ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    data = call.data.split('_')
    await state.update_data(op=data[1], id=data[2], cat=data[3], comm=None)
    await call.message.edit_text(text='Введите сумму.\n\nЕсли вы хотите внести сумму в валюте, отличной от основной, то после числа укажите нужную валюту через пробел.\nНапример: <i>200 usd</i>\n\nСписок доступных валют: <code>RUB</code>, <code>USD</code>, <code>EUR</code>, <code>UAH</code>, <code>BYN</code>, <code>KZT</code>',
                                 reply_markup=kb)
    await state.set_state(AddOperation.sum)


@rt.message(AddOperation.sum)
async def addcomm(message: Message, state: FSMContext):
    sum = message.text
    a = True
    try:
        if not ' ' in sum:
            raise ValueError
        
        b = sum.split(' ')
        if len(b) != 2 or not (b[1]).lower() in ['rub', 'uah', 'usd', 'eur', 'byn', 'kzt']:
            a = False
    except ValueError:
        sum = sum.replace(',', '.')
        temp = sum.replace('.', '')
        if not temp.isdigit():
            a = False

    if a:
        await state.update_data(sum=sum)
        await comment(message, state)
    else: 
        await message.answer(text='Неправильный формат ввода. Попробуйте ещё раз.')
        await state.set_state(AddOperation.sum)


async def comment(message: Message, state: FSMContext):
    bd = InlineKeyboardBuilder()
    bd.row(InlineKeyboardButton(text='📝 Ввести комментарий', callback_data=ActionCallback(action='input_comment').pack()))
    bd.row(InlineKeyboardButton(text='Пропустить ►', callback_data=ActionCallback(action='next_comment').pack()))

    bd1 = InlineKeyboardBuilder()
    bd1.row(InlineKeyboardButton(text='📝 Изменить комментарий', callback_data=ActionCallback(action='input_comment').pack()))
    bd1.row(InlineKeyboardButton(text='Далее ►', callback_data=ActionCallback(action='next_comment').pack()))

    a = (await state.get_data())['comm']
    if a:
        await message.answer(text=f'Ваш комментарий:\n\n<i>{a}</i>', reply_markup=bd1.as_markup())
    else: 
        await message.answer(text=f'Операция без комментария.\n\nВы можете ввести комментарий.', reply_markup=bd.as_markup())
    

@rt.callback_query(ActionCallback.filter(F.action == 'input_comment'))
async def input_comment(call: CallbackQuery, state: FSMContext):
    buttons = [
    [
        InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_menu_st').pack())
    ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(text='Введите ваш комментарий.\n\nКомментарий не должен быть длиннее 50 символов и не должен содержать в себе символы "><=/"',
                                 parse_mode=None,
                                 reply_markup=kb)
    await state.set_state(AddOperation.comm)
    await call.answer()


@rt.message(AddOperation.comm, F.text)
async def acomment(message: Message, state: FSMContext):
    buttons = [
    [
        InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_menu_st').pack())
    ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    comm = message.text

    if len(comm) > 50 or any(symbol in comm for symbol in ['<', '>', '=', '/']):
        await message.answer(text='Некорректный комментарий. Комментарий не должен быть длиннее 50 символов и не должен содержать в себе символы "><=/-+*"\n\nВведите другой комментарий.',
                             parse_mode=None,
                             reply_markup=kb)
        await state.set_state(AddOperation.comm)

    else:
        await state.update_data(comm=comm)
        await comment(message, state)


@rt.callback_query(ActionCallback.filter(F.action == 'next_comment'))
async def addop(call: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    id = data['id']
    a = operation_add(data['id'], data['cat'], data['op'], data['sum'], data['comm'])

    if data['op'] == '+':
        text = '📈 Доход добавлен'
    else:
        text = '📉 Трата добавлена'
    if a:
        await call.message.edit_text(text=text)
        await call.answer()
        await state.clear()
        await start(call.message, id=id)


@rt.callback_query(ActionCallback.filter(F.action == 'get_table'))
async def table(call: CallbackQuery):
    id = call.from_user.id
    get_database_xlsx(id)        
    
    file = f'temp/a{id}.xlsx'
    table = FSInputFile(file)
    await call.message.answer_document(table)
    await call.answer()
    os.remove(file)
    await start(call.message, id=id)
