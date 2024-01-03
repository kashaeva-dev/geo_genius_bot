from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from django.core.management import BaseCommand

from environs import Env
import logging

from definitions.management.commands.bot import user_handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d - %(levelname)-8s - %(asctime)s - %(funcName)s - %(name)s - %(message)s'
    )

logger = logging.getLogger(__name__)

env: Env = Env()
env.read_env()

storage: MemoryStorage = MemoryStorage()
bot: Bot = Bot(token=env('TG_TOKEN'))
dp: Dispatcher = Dispatcher(storage=storage)

dp.include_router(user_handlers.router)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('Bot started')
        dp.run_polling(bot)
