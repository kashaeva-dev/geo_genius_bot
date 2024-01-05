import logging
import random
import re

import emoji
from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from environs import Env
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

from definitions.management.commands.bot.emoji import replace_with_emoji, async_re_sub
from definitions.management.commands.bot.user_keyboards import (
    user_register_keyboard,
    user_main_keyboard,
    get_initial_definitions_keyboard,
    get_used_definitions_keyboard,
    get_used_in_definitions_keyboard, get_answer_choice_definitions_keyboard, learn_next_definition_keyboard,
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
        await message.answer('🤖 ГЛАВНОЕ МЕНЮ:',
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
    description_math = await async_re_sub(r'\$(\d+)\$', replace_with_emoji, definition.description_math)
    await callback_query.message.answer(
        f'<b>{definition.name.upper()}</b>\n\n{definition.description}\n\n'
        f'{description_math}\n\nопределение использует ⤵',
        reply_markup=await get_used_definitions_keyboard(definition_id),
        parse_mode='HTML',
        )
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text=emoji.emojize(f'определение используется ⤵'),
        reply_markup=await get_used_in_definitions_keyboard(definition_id),
        parse_mode='HTML',
    )

@router.callback_query(F.data == 'learn_definitions')
async def learn_definitions_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get('counter', False):
        await state.update_data(counter=0)
    data = await state.get_data()
    if data['counter'] < 3:
        definitions_to_learn = await sync_to_async(Definition.objects.all)()
        definitions_to_learn_ids = []
        async for definition in definitions_to_learn:
            definitions_to_learn_ids.append(definition.id)
        definition_id = random.choice(definitions_to_learn_ids)
        definition = await Definition.objects.aget(pk=definition_id)
        await state.update_data(definition=definition)
        await callback_query.message.edit_text(
            'Выбери определение, которое означает:\n\n'
            f'{definition.description}',
            reply_markup=await get_answer_choice_definitions_keyboard(definition.id),
            parse_mode='HTML',
        )
    else:
        definition_id = random.choice(data['show_definition_ids'])
        definition = await Definition.objects.aget(pk=definition_id)
        await state.update_data(definition=definition)
        await state.set_state(Learning.waiting_for_definition)
        await callback_query.message.edit_text(
            'А теперь, пожалуйста, напишите определение, которое означает:\n\n'
            f'{definition.name.upper()}',
            parse_mode='HTML',
        )



@router.callback_query(F.data.startswith('answer_choice_'))
async def answer_choice_handler(callback_query: CallbackQuery, state: FSMContext):
    definition_id = callback_query.data.split('_')[-1]
    data = await state.get_data()
    counter = data['counter']
    show_definition_ids = data.get('show_definition_ids', False)
    if not show_definition_ids:
        show_definition_ids = []
    show_definition_ids.append(definition_id)
    await state.update_data(counter=counter + 1)
    await state.update_data(show_definition_ids=show_definition_ids)
    definition = await Definition.objects.aget(pk=definition_id)
    if definition.id == data['definition'].id:
        await callback_query.message.edit_text(
            'Правильно!',
            reply_markup=learn_next_definition_keyboard,
            parse_mode='HTML',
        )
    else:
        await callback_query.message.edit_text(
            f'Неправильно. Правильный ответ: <b>{data["definition"].name}</b>',
            reply_markup=learn_next_definition_keyboard,
            parse_mode='HTML',
        )


@router.message(Learning.waiting_for_definition)
async def definition_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    definition = data['definition']
    await state.update_data(counter=0)
    await state.update_data(show_definition_ids=[])
    user_answer = message.text.lower().split()
    user_answer = [word.strip(',.()') for word in user_answer]
    right_answer = definition.description.lower().split()
    right_answer = [word.strip(',.()<b>/') for word in right_answer]
    right_word_count = 0

    for word in user_answer:
        if word in right_answer:
            right_word_count += 1
    mark = right_word_count / len(right_answer)

    if mark == 1:
        mark_text = '🏆 Отлично! Точно в цель!'
    elif mark >= 0.8:
        mark_text = '👍 Почти получилось! Надо чуть-чуть подкорректировать!'
    elif mark >= 0.5:
        mark_text = '🥉 Неплохо! Пожалуйста, обрати внимание на формулировку!'
    else:
        mark_text = '☹  Попробуй еще раз! Все получится!'
    if mark == 1:
        await message.answer(
            mark_text,
            reply_markup=learn_next_definition_keyboard,
            parse_mode='HTML',
        )
    else:
        await message.answer(
            f'{mark_text}\n\nПравильный ответ: <b>{definition.description}</b>',
            reply_markup=learn_next_definition_keyboard,
            parse_mode='HTML',
        )
    await state.clear()
