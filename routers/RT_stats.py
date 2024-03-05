import warnings
import os
import matplotlib.pyplot as plt

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from data.scripts.DB_database import get_info, get_history
from data.scripts.DB_currencies import cur_rate

from components.keyboards import ActionCallback
from routers.RT_start import start


rt = Router()

warnings.filterwarnings("ignore", category=UserWarning)


@rt.callback_query(ActionCallback.filter(F.action == 'see_stats'))
async def see_stats(call: CallbackQuery):
    buttons = [
        [
            InlineKeyboardButton(text='📈 Доход', callback_data='income_see_type_stats'),
            InlineKeyboardButton(text='📉 Траты', callback_data='spends_see_type_stats')
        ],
        [
            InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='see_history').pack())
        ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(text='Выберите вид операций для отображения статистики:', 
                                 reply_markup=kb)
    await call.answer()


@rt.callback_query(lambda c: '_see_type_stats' in c.data)
async def see_stats_per(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')[0]
    await state.update_data(stats_type=data)
    await see_stats_per1(call.message)


async def see_stats_per1(message: Message):
    buttons = [
        [
            InlineKeyboardButton(text='Эта Неделя', callback_data='week_see_period_stats'),
            InlineKeyboardButton(text='Этот Месяц', callback_data='month_see_period_stats'),
            InlineKeyboardButton(text='Этот Год', callback_data='year_see_period_stats')
        ],
        [
            InlineKeyboardButton(text='Всё время', callback_data='alltime_see_period_stats')
        ],
        [
            InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='see_history').pack())
        ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.edit_text(text='Выберите за какой период отобразить стаистику:', 
                                 reply_markup=kb)


@rt.callback_query(lambda c: '_see_period_stats' in c.data)
async def see_stats_period(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')[0]
    id = call.from_user.id
    await state.update_data(stats_period=data, stats_id=id)
    await see_stats(call, state)


def get_stats(id, type, period):
    a = get_history(id, 'all', type, period, 'all')
    if not a:
        return False, False
    
    dic = {
        'alltime': 'всё время',
        'week': 'эту неделю',
        'month': 'этот месяц',
        'year': 'этот год',
        'income': 'доходов',
        'spends': 'трат'
    }
    category_totals = {}  # Словарь для хранения сумм трат по категориям
    total_expenses = 0  # Переменная для общей суммы трат
    currency = get_info(id, 'main_currency')

    for entry in a:
        category = entry[5]
        expense = entry[3]
        cur = entry[4]

        if cur != currency:
            expense *= cur_rate[f'{cur}_to_{currency}']
        
        if category not in category_totals:
            category_totals[category] = 0
        
        category_totals[category] += expense
        total_expenses += expense

    category_totals_per = {}

    for category, total in category_totals.items():
        per = (total / total_expenses) * 100
        category_totals_per[category] = per 

    stats = ''

    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

    for category, total in sorted_categories:
        per = category_totals_per[category]
        stats += f'<b><i>"{category}"</i></b> | {total:.2f} {currency} | <b>{per:.2f}%</b>\n'

    text = f'Ваша статистика <b>{dic[type]}</b> за <b>{dic[period]}</b>:\n\n' + stats + f'\nОбщая сумма трат: <b>{total_expenses:.2f} {currency}</b>'
    return text, category_totals

async def see_stats(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    id = data['stats_id']
    type = data['stats_type']
    period = data['stats_period']

    text, category_totals = get_stats(id, type, period)
    if not text:
        await call.message.edit_text(text='📊 У вас нет операций за выбранный период')
        await call.answer()
        await start(call.message, id=id)   

    else:
        from main import bot
        # Создание диаграммы
        labels = list(category_totals.keys())
        sizes = list(category_totals.values())
        colors = plt.cm.tab10(range(len(labels)))

        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        file = f'temp/dg{id}.jpg'
        plt.savefig(file, bbox_inches='tight')
        plt.close()

        # Создание сообщения с картинкой
        image = FSInputFile(file)

        # Кнопки
        buttons = [
            [
                InlineKeyboardButton(text='◄◄ В главное меню', callback_data=ActionCallback(action='back_to_menu_stats').pack())
            ]
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await call.answer(text='Пожалуйста, ожидайте')
        await call.message.answer_photo(image, caption=text, reply_markup=kb)

        os.remove(file)


@rt.callback_query(ActionCallback.filter(F.action == 'back_to_menu_stats'))
async def back_to_menu(call: CallbackQuery):
    id = call.from_user.id
    await start(call.message, id=id)
    await call.answer()
