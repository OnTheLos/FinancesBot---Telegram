import asyncio
import logging

from aiogram import Bot, Dispatcher
from datetime import datetime
from components import config
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from routers import RT_start, RT_operations, RT_history, RT_stats, RT_info_settings, RT_admin, RT_banned
from routers.RT_admin import db_backup
from data.scripts.DB_currencies import update_currency


# Логирование в консоли
if config.LOGGING == True:
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


bot = Bot(token=config.BOT_TOKEN, 
          parse_mode="HTML")
dp = Dispatcher()

async def main():

    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

    # Обновление курсов валют
    scheduler.add_job(update_currency, trigger='cron', 
                      hour=10, minute=0,
                      start_date=datetime.now())
    
    # Бэкапы БД
    if config.BACKUP_TIMES:
        scheduled_times = config.BACKUP_TIMES

        for time in scheduled_times:
            hour, minute = map(int, time.split(':'))
            scheduler.add_job(db_backup, trigger='cron', hour=hour, minute=minute, start_date=datetime.now())

    dp.include_routers(RT_banned.rt,
                       RT_admin.rt,
                      RT_start.rt, 
                      RT_operations.rt,
                      RT_history.rt,
                      RT_stats.rt,
                      RT_info_settings.rt)
    
    # Запуск запланированных действий и бота
    scheduler.start()
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())