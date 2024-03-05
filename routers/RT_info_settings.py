from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from data.scripts.DB_currencies import get_date

from components.keyboards import ActionCallback


rt = Router()


# Хэндлер информации о боте
@rt.callback_query(ActionCallback.filter(F.action == 'info'))
async def info(call: CallbackQuery):
    cur_rate_date = get_date()                                                                  # Получение даты последнего обновления курса валют
    date = cur_rate_date[8:10] + '.' + cur_rate_date[5:7] + '.' + cur_rate_date[2:4]            # Форматирование даты

    text = f'''<b>Бот учёта финансов. Заносите свои доходы и траты за секунды, анализируйте результат и полностью управляйте своими средствами.</b>
    
Последнее обновление курсов валют: {date}'''

    buttons = [
    [
        InlineKeyboardButton(text='◄ Назад', callback_data=ActionCallback(action='back_to_menu').pack())
    ]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons) 

    await call.message.edit_text(text=text,
                                 reply_markup=kb)
    await call.answer()