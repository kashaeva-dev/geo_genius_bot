import logging
import emoji
import random

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async

from definitions.models import Definition, DefinitionUsage


logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d - %(levelname)-8s - %(asctime)s - %(funcName)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)


user_register_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Зарегистрироваться', callback_data='user_register'),
    ],
])

to_main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='На главную', callback_data='to_main_menu'),
    ],
])

user_main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=emoji.emojize(':eyes: Просмотреть определения'), callback_data='look_definitions'),
    ],
    [
        InlineKeyboardButton(text=emoji.emojize(':brain: Учить определения'), callback_data='learn_definitions'),
    ],
    [
        InlineKeyboardButton(text=emoji.emojize(':1st_place_medal: Посмотреть рейтинг'), callback_data='look_statistics'),
    ],
    [
        InlineKeyboardButton(text=emoji.emojize(':gear: Настройки'), callback_data='settings'),
    ],
])

user_settings_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=emoji.emojize(':pencil: Изменить имя'), callback_data='change_name')
    ],
    [
        InlineKeyboardButton(text=emoji.emojize(':pencil: Вкл./Выкл. мат. определение'), callback_data='change_description_math_usage')
    ],
]
)

user_hint_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=emoji.emojize(':bomb: Мат. определение'), callback_data='look_definition_math'),
        InlineKeyboardButton(text=emoji.emojize(':key: Подсказка'), callback_data='look_definition_hint'),
    ],
]

)

user_description_math_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=emoji.emojize(':pencil: Включить'), callback_data='change_name')
    ],
    [
        InlineKeyboardButton(text=emoji.emojize(':pencil: Выключить'), callback_data='change_description_math_usage')
    ],
]
)

async def get_initial_definitions_keyboard():
    definitions = await sync_to_async(Definition.objects.filter)(is_initial=True)
    builder = InlineKeyboardBuilder()
    async for definition in definitions:
        builder.button(text=f'{definition.emoji_picture} {definition.name}',
                                      callback_data=f'definition_{definition.id}',
                       )
        builder.adjust(2)
    return InlineKeyboardMarkup(inline_keyboard=builder.export())


async def get_used_definitions_keyboard(definition_id):
    definition = await sync_to_async(Definition.objects.get)(pk=definition_id)
    builder = InlineKeyboardBuilder()
    async for used_definition in definition.used_definitions.all():
        builder.button(text=f'{used_definition.emoji_picture} {used_definition.name}',
                       callback_data=f'definition_{used_definition.id}',
                       )
        builder.adjust(2)
    return InlineKeyboardMarkup(inline_keyboard=builder.export())


async def get_used_in_definitions_keyboard(definition_id):
    definition = await sync_to_async(Definition.objects.get)(pk=definition_id)
    builder = InlineKeyboardBuilder()
    used_in_definitions = await sync_to_async(DefinitionUsage.objects.select_related('definition').filter)(used_definition=definition)
    async for used_in_definition in used_in_definitions:
        builder.button(text=f'{used_in_definition.definition.emoji_picture} {used_in_definition.definition.name}',
                       callback_data=f'definition_{used_in_definition.definition.id}',
                       )
        builder.adjust(2)
    return InlineKeyboardMarkup(inline_keyboard=builder.export())


async def get_answer_choice_definitions_keyboard(definition_id):
    definition = await sync_to_async(Definition.objects.get)(pk=definition_id)
    builder = InlineKeyboardBuilder()
    used_in_definitions = await sync_to_async(DefinitionUsage.objects.select_related('definition').filter)(used_definition=definition)
    buttons = []
    async for answer_choice in used_in_definitions:
        buttons.append((f'{answer_choice.definition.emoji_picture} {answer_choice.definition.name}',
                       f'answer_choice_{answer_choice.definition.id}',)
                       )
    async for answer_choice in definition.used_definitions.all():
        buttons.append((f'{answer_choice.emoji_picture} {answer_choice.name}',
                       f'answer_choice_{answer_choice.id}',)
                       )
    async for answer_choice in definition.similar_definitions.all():
        buttons.append((f'{answer_choice.emoji_picture} {answer_choice.name}',
                       f'answer_choice_{answer_choice.id}',)
                       )
    buttons.append((f'{definition.emoji_picture} {definition.name}', f'answer_choice_{definition.id}'))
    random.shuffle(buttons)
    logger.info(f'buttons: {buttons}')
    for button in set(buttons):
        builder.button(text=button[0],
                       callback_data=button[1],
                       )
    builder.adjust(2)

    return InlineKeyboardMarkup(inline_keyboard=builder.export())


learn_next_definition_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Дальше', callback_data='learn_definitions'),
    ],
])