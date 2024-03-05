from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from data.scripts.DB_database import get_categories, get_info
from data.scripts.DB_database import  get_history
from data.scripts.DB_currencies import cur_rate

from components import keyboards
from components.keyboards import ActionCallback


rt = Router()


# Хэндлер просмотра истории операций
@rt.callback_query(ActionCallback.filter(F.action == 'see_history'))
async def see_histor(call: CallbackQuery, state: FSMContext):

    # Проверка стейта (для фильтров)
    data = await state.get_data()
    if not data:                                                                                    # Если стейты не найдены...
        await state.update_data(category='all', operation='all', period='alltime', page=1)          # то заносятся фильтры по умолчанию

    elif len(data) != 4:                               # Если стейтов в машине состояний менее 4-х...       
        await state.clear()                            # то машина состояний очищается...
        await see_histor(call, state)                  # и функция запускается заново        

    # Определение переменных
    filters = await state.get_data()            # Словарь со всеми фильтрами из машины состояний

    id = call.from_user.id                      # Получение ID юзера
    category = filters['category']              # Получение фильтра категорий
    operation = filters['operation']            # Получение фильтра типа операций
    period = filters['period']                  # Получение фильтра периода операций
    page = filters['page']                      # Получение страницы

    # Получение истории операций
    result = get_history(id, category, operation, period, page)

    # Определение текста для кнопки
    if category == 'all' and operation == 'all' and period == 'alltime':    # "Если фильтров нет"
        filt = 'Нет'
    else: filt = 'Свои'                                                     # "Если есть хотя бы 1 фильтр"

    buttons = [
            [
                InlineKeyboardButton(text=f'📥 Фильтры: {filt}', callback_data=ActionCallback(action='filters').pack())
            ],
            [       
                InlineKeyboardButton(text='📊 Посмотреть статистику', callback_data=ActionCallback(action='see_stats').pack())
            ],
            [
                InlineKeyboardButton(text='◀', callback_data=ActionCallback(action='prev_history_page').pack()),
                InlineKeyboardButton(text=f'{str(page)}', callback_data=ActionCallback(action='history_num_page').pack()),
                InlineKeyboardButton(text='▶', callback_data=ActionCallback(action='next_history_page').pack())
            ],
            [
                InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_menu').pack())
            ]
        ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Если функция ничего не вернула и страница не равна 1, то это значит, что юзер дошёл до последней страницы
    if not result and page != 1:
        await call.answer(text='Вы на последней странице.')
        await state.update_data(page=page-1)
    
    # Если функция ничего не вернула, фильтры стоят по умолчанию и страница равна 1, то это значит, что у юзера нет никаких операций
    elif not result and category == 'all' and operation == 'all' and period == 'alltime' and page == 1:
        await call.answer(text='Сначала вам нужно добавить доход или трату.')

    # Если функция ничего не вернула, страница равна 1 и выбран хотя бы один фильтр, то это значит, что по этим фильтрам нет операций
    elif not result and (category != 'all' or operation != 'all' or period != 'alltime') and page == 1:
        try:        
            await call.message.edit_text(text=f'<b>Нет никаких операций по текущим фильтрам.</b>', 
                                        reply_markup=kb)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
        
        await call.answer()

    else:        
        main_cur = get_info(id, 'main_currency')                    # Получение основной валюты юзера

        msg = ''                                                    # Переменная, в которую будет добавляться текст с операциями
        for index, i in enumerate(result):
                 
            if i[2] == '+':                                         # Определение смайлика  
                msg += '🟢'
            else: msg += '🔴'

            # Если основная валюта отличается от валюты данной операции, то в скобки вносится сумма операции в основной валюте
            if i[4] != main_cur:
                main_summa = '{:.2f}'.format(i[3] * cur_rate[f'{i[4]}_to_{main_cur}']).rstrip('0').rstrip('.')
                cur = f'{i[4]}({main_summa} {main_cur})'
            else: 
                cur = i[4]

            date = str(i[1])[8:10] + '.' + str(i[1])[5:7] + '.' + str(i[1])[2:4]                    # Форматирование даты
            summa ='{:.2f}'.format(i[3]).rstrip('0').rstrip('.')                                    # Округление суммы операции
            msg += f'<b> {i[2]}{summa} {cur}▫️<i>"{i[5]}"</i></b>▫️{date} [<code>{i[0]}</code>]\n'    # Сборка строки с данными об операции

            # Добавление комментария к строке, если он есть
            if i[7] is not None:
                msg += f"<i>{i[7]}</i>\n"

            # Добавление разграничительной полосы под строку(но только, если строка не последняя)
            if index < len(result) - 1: 
                msg += '<b>————————————————————————————</b>\n'
        
        try:        
            await call.message.edit_text(text=f'<b>Ваши операции:</b>\n\n{msg}',        # Отправка сообщения 
                                        reply_markup=kb)
        
        # Игнорирование ошибки, которая возникает если отредактировать без изменений сообщение
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):                           
                pass
            
        await call.answer()


# Хэндлер выбора фильтров
@rt.callback_query(ActionCallback.filter(F.action == 'filters'))
async def filters(call: CallbackQuery, state: FSMContext):
    # Получение данных из машины состояний
    data = await state.get_data()

    category = data['category']
    operation = data['operation']
    period = data['period']

    # Текст для кнопок
    mapping = {
        'week': 'Неделя',
        'month': 'Месяц',
        'year': 'Год',
        'alltime': 'Вcё время',
        'all': 'Все',
        'income': 'Доход',
        'spends': 'Трата'
    } 
    if category == 'all':
        category = 'Все'

    buttons = [
        [
            InlineKeyboardButton(text=f'📆 Период: {mapping.get(period)}', callback_data=ActionCallback(action='history_time').pack()),
            InlineKeyboardButton(text=f'🗃 Тип операции: {mapping.get(operation)}', callback_data=ActionCallback(action='history_operation_type').pack())
        ],
        [
           InlineKeyboardButton(text=f'📁 Категория: {category}', callback_data=ActionCallback(action='history_category').pack())
        ],
        [
            InlineKeyboardButton(text='Восстановить значения по умолчанию', callback_data=ActionCallback(action='history_reset').pack())
        ],
        [
            InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='see_history').pack())
        ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await call.message.edit_text(text='Выберите фильтры:',
                                 reply_markup=kb)


# Хэндлер кнопки 'Восстановить значения по умолчанию'
@rt.callback_query(ActionCallback.filter(F.action == 'history_reset'))
async def his_res(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await see_histor(call, state)  


# Хэндлер выбора фильтра типа операций
@rt.callback_query(ActionCallback.filter(F.action == 'history_operation_type'))
async def history_type(call: CallbackQuery):
    buttons = [
        [
            InlineKeyboardButton(text='📈 Доход', callback_data='income_history_type_in'),
            InlineKeyboardButton(text='📉 Трата', callback_data='spends_history_type_in')
        ],
        [
            InlineKeyboardButton(text='Все', callback_data='all_history_type_in')
        ],
        [
            InlineKeyboardButton(text='◄ Назад', callback_data='back_to_history_filters')
        ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(text='Выберите тип операций:', 
                                 reply_markup=kb)
    await call.answer()
    

# Внесение данных о фильтре типа операций в машину состояний
@rt.callback_query(lambda c: 'history_type_in' in c.data)
async def answer(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')[0]
    await state.update_data(operation=data, page=1)
    await filters(call, state)


# Хэндлер выбора фильтра категории
@rt.callback_query(ActionCallback.filter(F.action == 'history_category'))
async def history_category(call: CallbackQuery):
    buttons = [
            [
                InlineKeyboardButton(text='📈 Доход',callback_data='in_hist_cat'),
                InlineKeyboardButton(text='📉 Трата',callback_data='sp_hist_cat')
            ],
            [
                InlineKeyboardButton(text='Все категории',callback_data='all_hist_cat')
            ],
            [
                InlineKeyboardButton(text='◄ Назад',callback_data='back_to_history_filters')
            ]
        ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(text='Выберите тип категории:', reply_markup=kb)
    await call.answer()


# Внесение данных о фильтре в машину состояний
@rt.callback_query(lambda c: '_hist_cat' in c.data)
async def answer(call: CallbackQuery, state: FSMContext):
    calldata = call.data.split(':')[1]
    data = calldata.split('_')[0]

    if data == 'all':
        await state.update_data(category=data, page=1)
        await filters(call, state)

    else:
        id = call.from_user.id
        a = get_categories(id, data)

        # Создание клавиатуры со всеми категориями (аналогичная в RT_start)
        bd = InlineKeyboardBuilder()
        [bd.add(InlineKeyboardButton(
            text=f'"{i}"', 
            callback_data=f'history_cat_{i}'))
            for i in a]
        if len(a) >= 10:
            bd.adjust(2)
        else:
            bd.adjust(1)
        bd.row(InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='history_category').pack()))
        
        await call.message.edit_text(text='Выберите категорию:', reply_markup=bd.as_markup())
        await call.answer()


@rt.callback_query(lambda c: 'history_cat_' in c.data)
async def answer(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')[2]
    await state.update_data(category=data, page=1)
    await filters(call, state)


@rt.callback_query(lambda c: 'history_page' in c.data)
async def answer(call: CallbackQuery, state: FSMContext):
    calldata = call.data.split(':')[1]
    data = calldata.split('_')[0]

    st = await state.get_data()

    num = st['page']

    if data == 'prev' and num > 1:
        await state.update_data(page=num - 1)
        await see_histor(call, state)
    
    elif data == 'next':
        await state.update_data(page=num + 1)
        await see_histor(call, state)
    
    else:
        await call.answer(text='Вы на начальной странице.')


@rt.callback_query(ActionCallback.filter(F.action == 'history_time'))
async def history_category(call: CallbackQuery):
    await call.message.edit_text(text='Выберите за какой период отображать историю:', reply_markup=await keyboards.kb_history_time())
    await call.answer()


@rt.callback_query(lambda c: 'history_choose_time_' in c.data)
async def answer(call: CallbackQuery, state: FSMContext):
    calldata = call.data.split(':')[1]
    data = calldata.split('_')[3]

    await state.update_data(period=data, page=1)
    await filters(call, state)


@rt.callback_query(ActionCallback.filter(F.action == 'back_to_history_filters'))
async def back_to_history_filters(call: CallbackQuery, state: FSMContext):
    await filters(call, state)
    await call.answer()


@rt.callback_query(ActionCallback.filter(F.action == 'history_num_page'))
async def history_num_page(call: CallbackQuery):
    await call.answer()
