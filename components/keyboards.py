from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData


class ActionCallback(CallbackData, prefix='main'):
    action: str


async def kb_start():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='📈 Добавить доход',
                    callback_data=ActionCallback(
                        action='in_addoperation'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='📉 Добавить трату',
                    callback_data=ActionCallback(
                        action='sp_addoperation'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='🔍 История/статистика',
                    callback_data=ActionCallback(
                        action='see_history'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='📝 Управление',
                    callback_data=ActionCallback(
                        action='manage'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='💬 Информация о боте',
                    callback_data=ActionCallback(
                        action='info'
                        ).pack()
                )
            ]
        ]
    )


async def kb_manage():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='📒 Добавить категорию',
                    callback_data=ActionCallback(
                        action='category_add'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='📝 Изменить категорию',
                    callback_data=ActionCallback(
                        action='category_edit'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='💵 Изменить валюту',
                    callback_data=ActionCallback(
                        action='choose_currency'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='✏️ Изменить баланс',
                    callback_data=ActionCallback(
                        action='edit_balance'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='📄 Выгрузить данные',
                    callback_data=ActionCallback(
                        action='get_table'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='❌ Удаление',
                    callback_data=ActionCallback(
                        action='delete'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='◄ Назад',
                    callback_data=ActionCallback(
                        action='back_to_menu'
                        ).pack()
                )
            ]
        ]
    )


async def kb_back_to_manage_st():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='◄ Назад',
                    callback_data=ActionCallback(
                        action='back_to_manage_st'
                        ).pack()
                )
            ]
        ]
    )


async def kb_types_addc():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='📈 Доход',
                    callback_data=ActionCallback(
                        action='cat_income'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='📉 Трата',
                    callback_data=ActionCallback(
                        action='cat_spend'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='◄ Назад',
                    callback_data=ActionCallback(
                        action='back_to_manage'
                        ).pack()
                )
            ]
        ]
    )


async def kb_history_time():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Эта Неделя',
                    callback_data=ActionCallback(
                        action='history_choose_time_week'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='Этот Месяц',
                    callback_data=ActionCallback(
                        action='history_choose_time_month'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='Этот Год',
                    callback_data=ActionCallback(
                        action='history_choose_time_year'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='Всё время',
                    callback_data=ActionCallback(
                        action='history_choose_time_alltime'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='◄ Назад',
                    callback_data=ActionCallback(
                        action='back_to_history_filters'
                        ).pack()
                )
            ]
        ]
    )


async def kb_delete_operation_confirm():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Да, я хочу удалить операцию',
                    callback_data=ActionCallback(
                        action='del_op_conf'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='- - -',
                    callback_data=ActionCallback(
                        action='none'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='◄ Назад',
                    callback_data=ActionCallback(
                        action='back_to_manage'
                        ).pack()
                )
            ]
        ]
    )

async def kb_start_currencies():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='RUB',
                    callback_data=ActionCallback(
                        action='RUB_my_currency'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='USD',
                    callback_data=ActionCallback(
                        action='USD_my_currency'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='EUR',
                    callback_data=ActionCallback(
                        action='EUR_my_currency'
                        ).pack()
                )
            ],
            [

                InlineKeyboardButton(
                    text='UAH',
                    callback_data=ActionCallback(
                        action='UAH_my_currency'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='BYN',
                    callback_data=ActionCallback(
                        action='BYN_my_currency'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='KZT',
                    callback_data=ActionCallback(
                        action='KZT_my_currency'
                        ).pack()
                )
            ] 
        ]
    )


async def kb_currencies():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='RUB',
                    callback_data=ActionCallback(
                        action='RUB_my_currency'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='USD',
                    callback_data=ActionCallback(
                        action='USD_my_currency'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='EUR',
                    callback_data=ActionCallback(
                        action='EUR_my_currency'
                        ).pack()
                )
            ],
            [

                InlineKeyboardButton(
                    text='UAH',
                    callback_data=ActionCallback(
                        action='UAH_my_currency'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='BYN',
                    callback_data=ActionCallback(
                        action='BYN_my_currency'
                        ).pack()
                ),
                InlineKeyboardButton(
                    text='KZT',
                    callback_data=ActionCallback(
                        action='KZT_my_currency'
                        ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text='◄ Назад',
                    callback_data=ActionCallback(
                        action='back_to_manage_st'
                        ).pack()
                )
            ] 
        ]
    )
