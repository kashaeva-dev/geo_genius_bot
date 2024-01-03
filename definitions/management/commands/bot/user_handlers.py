import logging

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from environs import Env
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

from definitions.management.commands.bot.user_keyboards import (
    user_register_keyboard,
    user_main_keyboard,
)
from definitions.models import Client

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d - %(levelname)-8s - %(asctime)s - %(funcName)s - %(name)s - %(message)s',
)

logger = logging.getLogger(__name__)

env: Env = Env()
env.read_env()

bot: Bot = Bot(token=env('TG_TOKEN'))

router = Router()


class Registration(StatesGroup):
    waiting_for_firstname = State()
    waiting_for_lastname = State()


@router.message(Command(commands=['start']))
async def start_command_handler(message: Message, state: FSMContext):
    client, created = await sync_to_async(Client.objects.get_or_create)(
        chat_id=message.from_user.id,
    )
    await state.update_data(client=client)
    logger.info(f'Client {client} created: {created}')
    if created or not client.firstname or not client.lastname:
        await message.answer('🤖 Добро пожаловать в чат-бот <b>Geo Genius</b>!\n\n'
                             'Я создан, чтобы помочь запомнить определения геометрических понятий.\n\n'
                             '🎫 Чтобы начать работу с ботом необходимо зарегистрироваться.\n\n'
                             '✅ Продолжая, вы даете свое согласие на обработку персональных данных.',
                             reply_markup=user_register_keyboard,
                             parse_mode='HTML',
                             )
    else:
        await message.answer('🤖 ГЛАВНОЕ МЕНЮ:',
                             reply_markup=user_main_keyboard,
                             )


@router.callback_query(F.data == 'user_register')
async def user_register_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer('Пожалуйста, введи свое имя',
                                         )
    await state.set_state(Registration.waiting_for_firstname)


@router.message(Registration.waiting_for_firstname)
async def enter_name(message: Message, state: FSMContext):
    await state.update_data(firstname=message.text)
    await message.answer("Какая у тебя фамилия?")
    await state.set_state(Registration.waiting_for_lastname)

@router.message(Registration.waiting_for_lastname)
async def enter_lastname(message: Message, state: FSMContext):
    await state.update_data(lastname=message.text)
    data = await state.get_data()
    client = await sync_to_async(Client.objects.get)(
        id=data['client'].id,
    )
    client.firstname = data['firstname']
    client.lastname = data['lastname']
    await message.answer(f"Спасибо за регистрацию, {client.firstname} {client.lastname}!",
                         reply_markup=user_main_keyboard,
                         parse_mode='HTML',
                         )
    await state.clear()
