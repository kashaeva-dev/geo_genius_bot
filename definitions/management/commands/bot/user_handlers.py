import logging
import random
import re
from datetime import date

import emoji
from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.db.models import Sum, FloatField
from django.db.models.functions import Coalesce
from environs import Env
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

from definitions.management.commands.bot.emoji import replace_with_emoji, async_re_sub
from definitions.management.commands.bot.pymorphy_func import get_accs_forms
from definitions.management.commands.bot.user_keyboards import (
    user_register_keyboard,
    user_main_keyboard,
    get_initial_definitions_keyboard,
    get_used_definitions_keyboard,
    get_used_in_definitions_keyboard, get_answer_choice_definitions_keyboard, learn_next_definition_keyboard,
    to_main_menu_keyboard, user_settings_keyboard, user_hint_keyboard, user_description_math_keyboard,
)
from definitions.models import Client, Definition, DefinitionLearningProcess, LearnedDefinition, Error

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


class ErrorReporting(StatesGroup):
    waiting_for_report = State()


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

@router.callback_query(F.data == 'change_name')
@router.callback_query(F.data == 'user_register')
async def user_register_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client = data.get('client', await Client.objects.aget(chat_id=callback_query.from_user.id))
    await state.update_data(client=client)
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
    await message.answer(f"Добро пожаловать, {client.firstname} {client.lastname}!",
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
async def definition_handler(callback_query: CallbackQuery, state: FSMContext):
    definition_id = callback_query.data.split('_')[-1]
    definition = await sync_to_async(Definition.objects.get)(pk=definition_id)
    data = await state.get_data()
    description_math = await async_re_sub(r'\$(\d+)\$', replace_with_emoji, definition.description_math) + '\n'
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
    if not data.get('client', False):
        client = await Client.objects.aget(chat_id=callback_query.from_user.id)
        await state.update_data(client=client)
    data = await state.get_data()
    await state.update_data(penalty=1)
    if data['counter'] < 3:
        definitions_to_learn = await sync_to_async(Definition.objects.exclude)(learning__is_learned=True)
        definitions_to_learn_ids = []
        async for definition in definitions_to_learn:
            definitions_to_learn_ids.append(definition.id)
        definition_id = random.choice(definitions_to_learn_ids)
        definition = await Definition.objects.aget(pk=definition_id)
        client = data['client']
        if client.description_math_is_on:
            description_math = await async_re_sub(r'\$(\d+)\$', replace_with_emoji, definition.description_math)
        else:
            description_math = ''
        await state.update_data(definition=definition)
        logger.info(f'definition category: {definition.get_category_display()}')
        category = definition.get_category_display()
        category, kotorii = get_accs_forms(category, 'который')
        await callback_query.message.edit_text(
            f'Выбери <b>{category}</b>, {kotorii} соответствует:\n\n'
            f'{definition.description}\n\n'
            f'{description_math}',
            reply_markup=await get_answer_choice_definitions_keyboard(definition.id),
            parse_mode='HTML',
        )
    else:
        definition_id = random.choice(data['show_definition_ids'])
        definition = await Definition.objects.aget(pk=definition_id)
        logger.info(f'definition category: {definition.get_category_display()}')
        category = definition.get_category_display()
        category, kotorii = get_accs_forms(category, 'который')
        await state.update_data(definition=definition)
        await state.set_state(Learning.waiting_for_definition)
        await callback_query.message.edit_text(
            f'А теперь, пожалуйста, напишите {category}, '
            f' {kotorii} соответствует:\n\n'
            f'{definition.name.upper()}',
            reply_markup=user_hint_keyboard,
            parse_mode='HTML',
        )



@router.callback_query(F.data.startswith('answer_choice_'))
async def answer_choice_handler(callback_query: CallbackQuery, state: FSMContext):
    definition_id = callback_query.data.split('_')[-1]
    data = await state.get_data()
    counter = data.get('counter', 0)
    show_definition_ids = data.get('show_definition_ids', False)
    if not show_definition_ids:
        show_definition_ids = []
    show_definition_ids.append(definition_id)
    await state.update_data(counter=counter + 1)
    await state.update_data(show_definition_ids=show_definition_ids)
    definition = await Definition.objects.aget(pk=definition_id)
    if definition.id == data['definition'].id:
        client = data['client']
        await DefinitionLearningProcess.objects.acreate(
            client=client,
            definition=definition,
            action='selection',
            score=1,
        )
        await callback_query.message.edit_text(
            'Правильно!',
            reply_markup=learn_next_definition_keyboard,
            parse_mode='HTML',
        )
    else:
        client = data['client']
        await DefinitionLearningProcess.objects.acreate(
            client=client,
            definition=definition,
            action='selection',
            score=0,
        )
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
    right_answer = [word.strip(',.-()<b>/') for word in right_answer]
    right_word_count = 0
    client = data['client']
    penalty = data['penalty']
    if user_answer[0] == 'это':
        user_answer = user_answer[1:]
    for word in user_answer:
        if word in right_answer:
            right_word_count += 1
    mark = right_word_count / len(right_answer)

    if mark == 1:
        await DefinitionLearningProcess.objects.acreate(
            client=client,
            definition=definition,
            action='typing',
            grade = 'excellent',
            score=30 / penalty,
        )
        actions = await sync_to_async(DefinitionLearningProcess.objects.filter)(client=client, definition=definition)
        total_score = 0
        async for action in actions:
            total_score += action.score
        if total_score >= 100:
            await sync_to_async(LearnedDefinition.objects.get_or_create)(
                client=client,
                definition=definition,
                defaults={'is_learned': True}
            )
            mark_text = '🏆 Отлично! Точно в цель!\n\n 🎉 Поздравляю! Определение отмечено как выученное!'
        else:
            mark_text = '🏆 Отлично! Точно в цель!'
    elif mark >= 0.8:
        await DefinitionLearningProcess.objects.acreate(
            client=client,
            definition=definition,
            action='typing',
            grade='good',
            score=10 / penalty,
        )
        mark_text = '👍 Почти получилось! Надо чуть-чуть подкорректировать!'
    elif mark >= 0.5:
        await DefinitionLearningProcess.objects.acreate(
            client=client,
            definition=definition,
            action='typing',
            grade='satisfactory',
            score=5 / penalty,
        )
        mark_text = '🥉 Неплохо! Пожалуйста, обрати внимание на формулировку!'
    else:
        await DefinitionLearningProcess.objects.acreate(
            client=client,
            definition=definition,
            action='typing',
            grade='bad',
            score=0,
        )
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


@router.callback_query(F.data == 'look_statistics')
async def look_statistics_handler(callback_query: CallbackQuery):
    today = date.today()
    client = await Client.objects.aget(chat_id=callback_query.from_user.id)
    learned_definitions = await sync_to_async(LearnedDefinition.objects.filter(client=client).distinct().count)()
    all_definitions = await sync_to_async(Definition.objects.all().count)()
    learned_today_definitions = await sync_to_async(LearnedDefinition.objects.filter(
        client=client,
        created_at__date=date.today()
    ).distinct().count)()
    correct_selections = await sync_to_async(DefinitionLearningProcess.objects.filter(
        client=client,
        action='selection',
        score__gt=0,
        date__date=today,
    ).count)()
    excellent_typings = await sync_to_async(DefinitionLearningProcess.objects.filter(
        client=client,
        action='typing',
        grade='excellent',
        date__date=today,
    ).count)()
    good_typings = await sync_to_async(DefinitionLearningProcess.objects.filter(
        client=client,
        action='typing',
        grade='good',
        date__date=today,
    ).count)()
    bad_typings = await sync_to_async(DefinitionLearningProcess.objects.filter(
        client=client,
        action='typing',
        grade='bad',
        date__date=today,
    ).count)()
    client_with_today_score = await sync_to_async(DefinitionLearningProcess.objects.filter(
        client=client,
        date__date=today,
    ).aggregate)(total_score=Sum('score'))
    today_total_score = client_with_today_score['total_score']
    scores = await sync_to_async(DefinitionLearningProcess.objects.select_related('client').filter(
        date__date=today,
    ).values(
        'client'
    ).annotate(
        total_score=Coalesce(Sum('score'), 0, output_field=FloatField())
    ).order_by)('total_score')

    scores_text = 'РЕЙТИНГ 3 ЛУЧШИХ УЧАСТНИКОВ:\n'
    counter = 0
    async for score in scores[:3]:
        logger.info(f'score: {score["client"]}')
        client = await Client.objects.aget(id=score["client"])
        scores_text += f'🥇 {client.firstname} {client.lastname} - {score["total_score"]}\n'
    scores_text += '\n'
    today_total_score_text = ''
    if today_total_score:
        today_total_score_text = f'Твой рейтинг сегодня: <b>{today_total_score}</b>'
    await callback_query.message.answer(
        'СТАТИСТИКА:\n\n'
        f'Всего выучено определений и/или аксиом: <b>{learned_definitions}</b> из {all_definitions}\n\n'
        'ЗА СЕГОДНЯ:\n'
        f'Выучено определений: <b>{learned_today_definitions}</b>\n'
        f'Выбрано правильных ответов: <b>{correct_selections}</b>\n'
        f'Написано определений: 🏆 <b>{excellent_typings}</b> 👍 <b>{good_typings}</b> 🥉 <b>{bad_typings}</b>\n\n'
        f'{scores_text}'
        f'{today_total_score_text}',
        reply_markup=to_main_menu_keyboard,
        parse_mode='HTML',
    )


@router.callback_query(F.data == 'to_main_menu')
async def to_main_menu_handler(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        '🤖 ГЛАВНОЕ МЕНЮ:',
        reply_markup=user_main_keyboard,
        parse_mode='HTML',
    )


@router.callback_query(F.data == 'settings')
async def settings_handler(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        '⚙ НАСТРОЙКИ:',
        reply_markup=user_settings_keyboard,
        parse_mode='HTML',
    )


@router.callback_query(F.data == 'look_definition_math')
async def look_definition_math_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    definition = data['definition']
    description_math = await async_re_sub(r'\$(\d+)\$', replace_with_emoji, definition.description_math)
    await callback_query.message.answer(
        text=f'Надеюсь, что тебе это поможет 😉\n\n'
        f'{description_math}',
        parse_mode='HTML',
    )

@router.callback_query(F.data == 'change_description_math_usage')
async def description_math_menu_handler(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        text='Здесь можно включить или выключить отображение математических определений в процессе изучения',
        reply_markup=user_description_math_keyboard,
        parse_mode='HTML',
    )

@router.callback_query(F.data.startswith('description_math_'))
async def description_math_handler(callback_query: CallbackQuery):
    condition = callback_query.data.split('_')[-1]
    client = await Client.objects.aget(chat_id=callback_query.from_user.id)
    if condition == 'on':
        client.description_math_is_on = True
        await client.asave()
        await callback_query.message.edit_text(
            text='Математические определения включены',
            reply_markup=user_main_keyboard,
            parse_mode='HTML',
        )
    else:
        client.description_math_is_on = False
        await client.asave()
        await callback_query.message.edit_text(
            text='Математические определения выключены',
            reply_markup=user_main_keyboard,
            parse_mode='HTML',
        )

@router.callback_query(F.data == 'look_definition_beginning')
async def look_definition_beginning_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    definition = data['definition']
    await callback_query.message.answer(
        text=f'Начало определения: <b>{definition.description.split()[0]}</b>',
        parse_mode='HTML',
    )


@router.callback_query(F.data == 'error_report')
async def report_command_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get('definition', False):
        definition = data['definition']
        await callback_query.message.answer(
            text='Пожалуйста, опишите проблему '
            f'c определением: {definition.name.upper()}',
            reply_markup=to_main_menu_keyboard,
            parse_mode='HTML',
        )
    else:
        await callback_query.message.answer(
            text='Пожалуйста, опишите проблему',
            reply_markup=to_main_menu_keyboard,
            parse_mode='HTML',
        )
    await state.set_state(ErrorReporting.waiting_for_report)

@router.message(ErrorReporting.waiting_for_report)
async def report_handler(message: Message, state: FSMContext):
    error = message.text
    data = await state.get_data()
    client = await Client.objects.aget(chat_id=message.from_user.id)
    if data.get('definition', False):
        definition = data['definition']
        await Error.objects.acreate(client=client, definition=definition, error=error)
        await message.answer(
            text='Спасибо за Вашу помощь. Мы обязательно разберемся с этим!',
            parse_mode='HTML',
        )
    else:
        Error.objects.create(client=client, error=error)
        await message.answer(
            text='Спасибо за Вашу помощь. Мы обязательно разберемся с этим!',
            parse_mode='HTML',
        )

    await state.clear()


@router.callback_query(F.data == 'look_definition_words')
async def look_definition_words_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    definition = data['definition']
    used_definitions = await sync_to_async(definition.used_definitions.all)()
    text = 'Данное определение основано на определениях:\n'
    async for used_definition in used_definitions:
        text += f'{used_definition.name}\n'
    await callback_query.message.answer(
        text=text,
        parse_mode='HTML',
    )

@router.callback_query(F.data == 'look_definition_hint')
async def look_definition_hint_handler(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    definition = data['definition']
    penalty = 5
    await state.update_data(penalty=penalty)
    hint_length = len(definition.description.split()) // 3
    hint = definition.description.split()[:hint_length]
    hint = ' '.join(hint)
    await callback_query.message.answer(
        text=f'Подсказка: <b>{hint}</b>',
        parse_mode='HTML',
    )
