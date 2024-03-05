from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from components import keyboards
from components.keyboards import ActionCallback
from components.states import AddCategory, DeleteOperation, Balance, EditCategory
from components import config

from data.scripts.DB_database import (check_db, create_table, get_info, get_categories, 
                                      create_table_with_categories, cat_add, delete_operation, 
                                      change_sum_currency, delete_category, add_data, edit_cat, check_data,
                                      start_get_last_operations, get_operation)
from data.scripts.DB_users import check_user


rt = Router()


@rt.message(F.text, Command('start'))
async def start(message: Message, id = None, edit = False):
    # Получение ID, если ID не был передан в функцию
    if not id:
        id = message.from_user.id

    does_table_exists = check_db(id)                   # Проверка, есть ли в БД таблица с юзером
    main_currency = check_data(id, 'main_currency')    # Получение информации о том, определена ли у юзера основная валюта
    does_user_exists = check_user(id)                  # Проверка, есть ли юзер в таблице со всеми юзерами бота

    if not does_user_exists and config.GET_NOTIFY_ID:    # Если юзера нет в таблице со всеми юзерами, то:
        from main import bot
        nickname = message.from_user.full_name                                                  # Определение ника юзера
        username = message.from_user.username                                                   # Определение юзернейма юзера
                                                                
        await bot.send_message(chat_id=config.GET_NOTIFY_ID,                                  # Отправка уведомления о новом юзере
                            text=f'Новый пользователь\n\n{id}\n{nickname}\n@{username}')
        
    # Если у юзера нет таблицы, то вызывается функция с её настройкой
    if not does_table_exists:
        await default_categories(message)

    # Если у юзера есть таблица, но не определена основная валюта, то вызывается функция с её выбором
    if does_table_exists and not main_currency:
        await choose_currency(message)

    # Если все условия соблюдены
    if does_table_exists and main_currency and does_user_exists:
        bal = float(get_info(id, 'balance'))                        # Получение баланса
        bal = '{:.2f}'.format(bal).rstrip('0').rstrip('.')   # Округление баланса
        cur = get_info(id, 'main_currency')                  # Получение основной валюты

        # Получение текста с последними операциями
        incomes = start_get_last_operations(id, '+', 3)
        spends = start_get_last_operations(id, '-', 3)

        # Если нет операций
        if not incomes:
            incomes = '<b>У вас пока что нет занесённых доходов</b>\n'
        if not spends:
            spends = '<b>У вас пока что нет занесённых трат</b>\n'


        text = f'''<b>Добро пожаловать в бота учёта финансов. Заносите свои доходы и траты за секунды, анализируйте результат и полностью управляйте своими средствами.</b>
        
💰Ваш баланс: <b>{bal} {cur}</b>

📈 Ваши последние доходы:

{incomes}
📉 Ваши последние траты: 

{spends}'''
        
        # Редактировать сообщение или отправить новое (передаётся в функцию)
        if edit:
            await message.edit_text(text=text,
                                reply_markup=await keyboards.kb_start()) 
        else:
            await message.answer(text=text,
                                reply_markup=await keyboards.kb_start())   
    

# Функция для настройки категорий
async def default_categories(message: Message):
    buttons = [
        [
            InlineKeyboardButton(text='Да', callback_data='defcat_yes'),
            InlineKeyboardButton(text='Нет', callback_data='defcat_no')
        ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Категории
    incomes = '<b>Доходы:</b> "Зарплата"'
    spends = '<b>Траты:</b> "Продукты", "Кафе", "Транспорт", "Подписки", "Покупки", "Здоровье", "Подарки"'

    await message.answer(text=f'Давайте настроим бота. Хотите ли вы добавить следующие категории по умолчанию?\n\n{spends}\n{incomes}\n\nВ любое время их можно будет изменить или удалить.',
                         reply_markup=kb)
    

# Хэндлер с ответом юзера на предложение установить категории по умолчанию
@rt.callback_query(lambda c: 'defcat_' in c.data)
async def default_cat_set(call: CallbackQuery):
    data = call.data.split('_')[1]  # Получение ответа - "yes" или "no"
    id = call.from_user.id

    # Создание таблицы
    if data == 'yes':
        create_table_with_categories(id)
    else:
        create_table(id) 

    # Вызов главного меню
    await call.answer()
    await start(call.message, id=id, edit=True)


# Функция с выбором основной валюты для новых юзеров
async def choose_currency(message: Message):
    try:
        await message.edit_text(text='Выберите основную валюту для бота:', 
                                reply_markup=await keyboards.kb_start_currencies())
    except:
        await message.answer(text='Выберите основную валюту для бота:', 
                            reply_markup=await keyboards.kb_start_currencies())


# Хэндлер для выбора валюты через меню Управления 
@rt.callback_query(ActionCallback.filter(F.action == 'choose_currency'))
async def choose_currency1(call: CallbackQuery):
    await call.message.edit_text(text='Выберите основную валюту для бота.\n\n<b>Внимание! После смены валюты, все операции с предыдущей валюты сконвертируются в новую.</b>', 
                              reply_markup=await keyboards.kb_currencies())
    

@rt.callback_query(lambda c: '_my_currency' in c.data)
async def change_currency(call: CallbackQuery):
    # Получение выбранной валюты и айди юзера
    calldata = call.data.split(':')[1]
    data = calldata.split('_')[0]
    id = call.from_user.id

    result = change_sum_currency(id, data)   # Изменение валюты

    # Отправка сообщения и вызов гланого меню, если всё прошло успешно
    if result:
        await call.message.edit_text(text=f'💵 Вы изменили основную валюту.\n\nТеперь ваша основная валюта: {data}')
        await start(call.message, id=id)


# Хэндлер меню Управления
@rt.callback_query(ActionCallback.filter(F.action == 'manage'))
async def manage(call: CallbackQuery):
    text = '''<b>Управление</b>

📒 <b>Добавить категорию</b> — добавление новой категории доходов/трат.

📝 <b>Изменить категорию</b> — изменение названия любой категории.

💵 <b>Изменить валюту</b> — смена основной валюты бота.

✏️ <b>Изменить баланс</b> — редактирование текущего баланса.

📄 <b>Выгрузить данные</b> — получение таблицы в формате .xlsx со всеми операциями за всё время.

❌ <b>Удаление</b> — удаление любой операции или категории.'''

    await call.message.edit_text(text=text, reply_markup=await keyboards.kb_manage())
    await call.answer()


# Хэндлер добавления категории
@rt.callback_query(ActionCallback.filter(F.action == 'category_add'))
async def categoty_add_q(call: CallbackQuery, state: FSMContext):
    # Выбор типа категории
    await call.message.edit_text(text='Какой тип категории вы хотите добавить?', 
                                 reply_markup=await keyboards.kb_types_addc())
    await state.set_state(AddCategory.type)


# Внесение в машину состояний тип категории для добавления
@rt.callback_query(ActionCallback.filter(F.action == 'cat_income'))
async def cat_income(call: CallbackQuery, state: FSMContext):
    await state.update_data(type='in_')
    await category_add(call, state)

@rt.callback_query(ActionCallback.filter(F.action == 'cat_spend'))
async def cat_income(call: CallbackQuery, state: FSMContext):
    await state.update_data(type='sp_')
    await category_add(call, state)


# Функция с сообщением о просьбе ввести название категории
async def category_add(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text='Напишите название новой категории.\n\nНазвание не должно быть длиннее 25 символов и не должно содержать в себе символы "><=/"', 
                                 reply_markup=await keyboards.kb_back_to_manage_st(),
                                 parse_mode=None)
    await state.set_state(AddCategory.name)
    call.answer()


@rt.message(AddCategory.name, F.text)
async def categoty_add1(message: Message, state: FSMContext): 
    # Определение названия и типа категории, а также ID юзера
    name = message.text
    type = (await state.get_data())['type']
    id = message.from_user.id

    buttons = [
    [
        InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_manage_st').pack())
    ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)    

    # Проверка соблюдения условий для названия:
    if len(name) > 25 or any(symbol in name for symbol in ['<', '>', '=', '/']):
        # Если условия не соблюдены, то выводится сообщение:
        await message.answer(text='Название не должно быть длиннее 25 символов и не должно содержать в себе символы "><=/"\n\nВведите другое название.',
                             reply_markup=kb,
                             parse_mode=None)
    else:
        # Если условия соблюдены, то категория добавляется в таблицу
        result = cat_add(id, name, type)

        if result: 
            # Если всё прошло успешно, то выводится сообщение и открывается главное меню
            await message.answer(text=f'📒 Категория "{name}" добавлена')
            await start(message, id=id)
        else:
            # Если такая категория уже есть в таблице, то выводится сообщение:
            await message.answer(text='Категория с таким названием уже существует.\n\nВведите другое название.',
                                 reply_markup=kb)


# Хэндлер выбора удаления операции или категории
@rt.callback_query(ActionCallback.filter(F.action == 'delete'))
async def delete(call: CallbackQuery):

    buttons = [
        [
            InlineKeyboardButton(text='1️⃣ Операцию', callback_data=ActionCallback(action='delete_op').pack()),
            InlineKeyboardButton(text='📒 Категорию', callback_data=ActionCallback(action='delete_cat').pack())
        ],
        [
            InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_manage').pack())
        ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(text='Вы хотите удалить операцию или категорию?',
                                 reply_markup=kb)
    

# Хэндлер выбора типа категории для удаления
@rt.callback_query(ActionCallback.filter(F.action == 'delete_cat'))
async def delete_cat(call: CallbackQuery):
    buttons = [
        [
            InlineKeyboardButton(text='📈 Доход', callback_data='delete_cat_incomes'),
            InlineKeyboardButton(text='📉 Трата', callback_data='delete_cat_spends')
        ],
        [
            InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_delete').pack())
        ]
    ]   
    kb = InlineKeyboardMarkup(inline_keyboard=buttons) 

    await call.message.edit_text(text='Выберите тип категории для удаления:',
                                 reply_markup=kb)
    await call.answer()


@rt.callback_query(lambda c: 'delete_cat_' in c.data)
async def addoperation(call: CallbackQuery):
    data = call.data.split('_')[2]  # Получение типа категории для удлаения
    # Определение переменных для функции
    if data == 'incomes':
        type = '+'
    else: type = '-'
    id = call.from_user.id

    categories = get_categories(id, type)  # Получение всех категорий по указанным параметрам

    # Создание клавиатуры с категориями
    if categories:
        bd = InlineKeyboardBuilder()
        [bd.add(InlineKeyboardButton(           # Добавление кнопки
            text=f'"{i}"',                      # Текст кнопки
            callback_data=f'delcat_{id}_{i}'))  # Колбэк кнопки
            for i in categories]
        
        if len(categories) >= 10:       # Если количество категорий(кнопок) более или равно 10...
            bd.adjust(2)                # То в каждом ряду клавиатуры будет по 2 столбца кнопок
        else:                           # Если меньше 10...
            bd.adjust(1)                # То будет только 1 столбец

        bd.row(InlineKeyboardButton(text='◄ Назад', 
                                    callback_data=ActionCallback(action='back_to_delete').pack()))  # Добавление кнопки Назад
        
        await call.message.edit_text(text='Выберите категорию для удаления:', reply_markup=bd.as_markup())
        await call.answer()

    # Если у юзера нет категорий, то появляется овтет:
    else:
        await call.answer(text='Сначала вам нужно добавить категорию')


# Хэндлер подтверждения удаления категории
@rt.callback_query(lambda c: 'delcat_' in c.data)
async def delcatconfirm(call: CallbackQuery):
    data = call.data.split('_') 

    buttons = [
    [
        InlineKeyboardButton(text='Да, я хочу безвозвратно удалить категорию', callback_data=f'delcat1_{data[1]}_{data[2]}')
    ],
    [
        InlineKeyboardButton(text='- - -', callback_data=ActionCallback(action='none').pack())
    ],
    [
        InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_delete').pack())
    ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(text=f'Вы действительно хотите безвозвратно удалить категорию "{data[2]}"?\n\nПосле подтверждения, <b>удалится категория "{data[2]}" и все операции, относящиеся к ней. Восстановление невозможно!</b>', 
                             reply_markup=kb)


# Хэндлер удаления категории
@rt.callback_query(lambda c: 'delcat1_' in c.data)
async def addoperation(call: CallbackQuery):
    data = call.data.split('_')         # Получение данных из колбэка     # delcat1_{id}_{category}
    delete_category(data[1], data[2])   # Удаление категории

    # Отправка сообщения об успешном удалении и возврат в главное меню
    await call.message.edit_text(text=f'❌ Категория "{data[2]}" удалена')
    await call.answer()
    await start(call.message, id=data[1])


# Хэндлер запроса ID операции для удаления
@rt.callback_query(ActionCallback.filter(F.action == 'delete_op'))
async def delete_op(call: CallbackQuery, state: FSMContext):

    buttons = [
        [
            InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_delete').pack())
        ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(text='<b>Введите ID операции для удаления.</b>\n\n<i>Все ID указаны в Истории операций в квадратных скобках.</i>',
                                 reply_markup=kb)
    await state.set_state(DeleteOperation.opid)


# Хэндлер подтверждения удаления операции
@rt.message(DeleteOperation.opid, F.text)
async def get_id_del(message: Message, state: FSMContext):
    opid = message.text                             # ID операции
    id = message.from_user.id                       # ID юзера
    await state.update_data(opid=opid)              # Обновление стейта

    operation_text = get_operation(id, opid)        # Получение текста с данными об операции

    # Если операция найдена, то отправляется сообщение с подтверждением
    if operation_text:
        await message.answer(text=f'<b>Вы действительно хотите безвозвратно удалить следующую операцию?</b>\n\n{operation_text}\nПосле удаления её <b>невозможно будет восстановить.</b>', 
                             reply_markup=await keyboards.kb_delete_operation_confirm())

    # Если операция не найдена, то отправляется сообщение об этом
    else:
        buttons = [
        [
            InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_delete').pack())
        ]
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
        await message.answer(text='Вы ввели некорректный ID, попробуйте ещё раз.', 
                                reply_markup=kb)


# Хэндлер удаления операции
@rt.callback_query(ActionCallback.filter(F.action == 'del_op_conf'))
async def del_op_conf(call: CallbackQuery, state: FSMContext):
    opid = (await state.get_data())['opid']     # Получение ID операции
    id = call.from_user.id                      # Получение ID юзера

    result = delete_operation(id, opid)              # Удаление операции

    # Если удаление прошло успешно, то отправляется сообщение и вызывается главное меню
    if result:
        await call.answer(text='❌ Операция удалена')
        await start(call.message, id=id)


# Хэндлер запроса суммы для измененения баланса
@rt.callback_query(ActionCallback.filter(F.action == 'edit_balance'))
async def edit_balance(call: CallbackQuery, state: FSMContext):
    id = call.from_user.id                       # Получение ID юзера
    cur = get_info(id, 'main_currency')          # Получение основной валюты

    buttons = [
    [
         InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_menu_st').pack())
    ]
        ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(text=f'Введите новый баланс в {cur}',
                                 reply_markup=kb)
    await state.set_state(Balance.balance)


@rt.message(Balance.balance)
async def edit_balance_type(message: Message):
    balance = message.text                      # Получение нового баланса, введённого юзером
    id = message.from_user.id                   # Получение ID юзера
    balance = balance.replace(',', '.')         # Замена всех запятых(если они есть) в новом балансе на точки
    temp_balance = balance.replace('.', '')     # Внесение нового баланса без точек во временную переменную (для дальнейшей проверки на число)
    cur = get_info(id, 'main_currency')         # Получение основной валюты юзера

    if not temp_balance.isdigit() and not (balance.count('.')) <= 1:            # Проверка является ли введённый баланс числом
        await message.answer(text='Введите корректное число')
    else:
        result = add_data(id, 'balance', balance)                               # Добавление нового баланса

    if result:
        await message.answer(text=f'💰 Ваш новый баланс: {balance} {cur}')      # Если всё прошло успешно - вывод сообщения 
        await start(message, id=id)                                             # Вызов главного меню


# Хэндлер выбора типа категории для её редактирования
@rt.callback_query(ActionCallback.filter(F.action == 'category_edit'))
async def category_edit(call: CallbackQuery):
    buttons = [
        [
            InlineKeyboardButton(text='📈 Доход', callback_data='edit_cat_incomes'),
            InlineKeyboardButton(text='📉 Трата', callback_data='edit_cat_spends')
        ],
        [
            InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_manage').pack())
        ]
    ]   
    kb = InlineKeyboardMarkup(inline_keyboard=buttons) 

    await call.message.edit_text(text='Выберите тип категории для редактирования:',
                                 reply_markup=kb)
    await call.answer()  


@rt.callback_query(lambda c: 'edit_cat_' in c.data)
async def addoperation(call: CallbackQuery):
    data = call.data.split('_')[2]
    if data == 'incomes':
        op = '+'
    else: op = '-'
    id = call.from_user.id

    a = get_categories(id, op)

    if a:
        bd = InlineKeyboardBuilder()
        [bd.add(InlineKeyboardButton(
            text=f'"{i}"', 
            callback_data=f'editcat_{i}'))
            for i in a]
        if len(a) >= 10:
            bd.adjust(2)
        else:
            bd.adjust(1)
        bd.row(InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='categoty_edit').pack()))
        
        await call.message.edit_text(text='Выберите категорию для редактирования:', reply_markup=bd.as_markup())
        await call.answer()

    else:
        await call.answer(text='Сначала вам нужно добавить категорию')  


@rt.callback_query(lambda c: 'editcat_' in c.data)
async def categoty_edit(call: CallbackQuery, state: FSMContext):
    name = call.data.split('_')[1]
    await state.update_data(oldname=name)

    await call.message.edit_text(text='Напишите новое название для категории.\n\nНазвание не должно быть длиннее 25 символов и не должно содержать в себе символы "><=/"', 
                                 reply_markup=await keyboards.kb_back_to_manage_st(),
                                 parse_mode=None)
    await state.set_state(EditCategory.name1)
    call.answer()


@rt.message(EditCategory.name1, F.text)
async def categoty_edit1(message: Message, state: FSMContext): 
    newname = message.text                              # Получение нового названия категории
    oldname = (await state.get_data())['oldname']       # Получение старого названия категории
    id = message.from_user.id                           # Получение ID юзера

    buttons = [
    [
        InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_manage_st').pack())
    ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)    

    # Проверка соблюдения условий для названия
    if len(newname) > 25 or any(symbol in newname for symbol in ['<', '>', '=', '/']):
        await message.answer(text='Название не должно быть длиннее 25 символов и не должно содержать в себе символы "><=/"\n\nВведите другое название.',
                             reply_markup=kb,
                             parse_mode=None)
    else:
        result = edit_cat(id, newname, oldname)     # Редактирование названия категории

        if result:  
            await message.answer(text=f'📝 Название категории "{oldname}" изменено на "{newname}"')
            await start(message, id=id)
        else:
            await message.answer(text='Введите другое название.',
                                 reply_markup=kb)






# Кнопки назад

@rt.callback_query(ActionCallback.filter(F.action == 'back_to_manage'))
async def back_to_manage(call: CallbackQuery):
    await manage(call)
    await call.answer()


@rt.callback_query(ActionCallback.filter(F.action == 'back_to_menu'))
async def back_to_menu(call: CallbackQuery):
    id = call.from_user.id
    await start(call.message, id=id, edit=True)
    await call.answer()


@rt.callback_query(ActionCallback.filter(F.action == 'back_to_menu_st'))
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    id = call.from_user.id
    await start(call.message, id=id, edit=True)
    await call.answer()


@rt.callback_query(ActionCallback.filter(F.action == 'back_to_manage_st'))
async def back_to_manage_st(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await manage(call)
    await call.answer()


@rt.callback_query(ActionCallback.filter(F.action == 'back_to_delete'))
async def back_to_manage(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await delete(call)
    await call.answer()


@rt.callback_query(ActionCallback.filter(F.action == 'none'))
async def none(call: CallbackQuery):
    await call.answer()









