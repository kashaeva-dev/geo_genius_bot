import logging
import random

import emoji
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
    get_initial_definitions_keyboard,
    get_used_definitions_keyboard,
    get_used_in_definitions_keyboard, get_answer_choice_definitions_keyboard,
)
from definitions.models import Client, Definition

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


class Learning(StatesGroup):
    learning_definitions = State()
    waiting_for_definition = State()


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
        await message.answer('🤖 ГЛАВНОЕ МЕНЮ:'
                             ',m &#128230; A&#x2208; &#127956;&#x21D4;(A&#x2208;&#x1F4C8;)&#x22C0;(A&#x2208;&#x1F9F7;)&#x22C0;(A&#x2208;&#x1FA83;)&#x22C0;(A&#x21D4;{x1&#x2208;&#x1F4CF;,x2&#x2208;&#x1F4CF;,x3&#x2208;&#x1F4CF;})',
                             reply_markup=user_main_keyboard,
                             parse_mode='HTML',
                             )


@router.callback_query(F.data == 'user_register')
async def user_register_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer('Пожалуйста, введи свое имя',
                                        parse_mode='HTML',
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
    await client.asave()
    await message.answer(f"Спасибо за регистрацию, {client.firstname} {client.lastname}!",
                         reply_markup=user_main_keyboard,
                         parse_mode='HTML',
                         )
    await state.clear()


@router.callback_query(F.data == 'look_definitions')
async def look_definitions_handler(callback_query: CallbackQuery):
    await callback_query.message.answer(
        'Список исходных определений:',
        reply_markup=await get_initial_definitions_keyboard(),
        parse_mode='HTML',
        )

@router.callback_query(F.data.startswith('definition_'))
async def definition_handler(callback_query: CallbackQuery):
    definition_id = callback_query.data.split('_')[-1]
    definition = await sync_to_async(Definition.objects.get)(pk=definition_id)
    await callback_query.message.answer(
        emoji.emojize(f'<b>{definition.name.upper()}</b>\n\n{definition.description}\n\n'
        f'определение использует :right_arrow_curving_down:'),
        reply_markup=await get_used_definitions_keyboard(definition_id),
        parse_mode='HTML',
        )
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text=emoji.emojize(f'определение используется :right_arrow_curving_down:'),
        reply_markup=await get_used_in_definitions_keyboard(definition_id),
        parse_mode='HTML',
    )

@router.callback_query(F.data == 'learn_definitions')
async def learn_definitions_handler(callback_query: CallbackQuery, state: FSMContext):
    definitions_to_learn = await Definition.objects.afirst()
    definition = definitions_to_learn
    await state.update_data(definition=definition)
    await callback_query.message.answer(
        'Выбери определение, которое означает:\n\n'
        f'{definition.description}',
        reply_markup=await get_answer_choice_definitions_keyboard(definition.id),
        parse_mode='HTML',
    )
