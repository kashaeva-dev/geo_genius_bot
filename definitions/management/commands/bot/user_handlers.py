import logging

from aiogram import Bot, Router
from environs import Env
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d - %(levelname)-8s - %(asctime)s - %(funcName)s - %(name)s - %(message)s',
)

logger = logging.getLogger(__name__)

env: Env = Env()
env.read_env()

bot: Bot = Bot(token=env('TG_TOKEN'), parse_mode='HTML')

router = Router()

@router.message(Command(commands=['start']))
async def start_command_handler(message: Message):
    await bot.send_message(
        message.from_user.id,
        'Привет! Я помогу тебе выучить определения и теоремы.'
    )
