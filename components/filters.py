from typing import Union, Dict, Any

from aiogram.filters import BaseFilter

from data.scripts.DB_banned import get_banned
from components import config


admin = config.ADMIN_IDS
banned = get_banned()

def update_banned():
    global banned
    banned = get_banned()
    return True


class AdminFilter(BaseFilter):
    async def __call__(self, message) -> Union[bool, Dict[str, Any]]:

        if message.from_user.id in admin:
            return True


class BannedFilter(BaseFilter):
    async def __call__(self, message) -> Union[bool, Dict[str, Any]]:

        if message.from_user.id in banned:
            return True