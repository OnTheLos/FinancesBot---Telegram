from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from components.keyboards import ActionCallback
from components.filters import BannedFilter


rt = Router()
rt.message.filter(BannedFilter())
rt.callback_query.filter(BannedFilter())


@rt.message(F.text)
async def ban_msg(message: Message):
    await message.answer(text='Вы заблокированы в боте')


@rt.callback_query(F.data)
async def ban_call(call: CallbackQuery):
    await call.message.answer(text='Вы заблокированы в боте')
    await call.answer()


@rt.callback_query(ActionCallback.filter(F.action))
async def ban_call(call: CallbackQuery):
    await call.message.answer(text='Вы заблокированы в боте')
    await call.answer()