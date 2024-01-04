import logging
import emoji

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async

from definitions.models import Definition

user_register_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Зарегистрироваться', callback_data='user_register'),
    ],
])

user_main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=emoji.emojize(':eyes: Просмотреть'), callback_data='look_definitions'),
    ],
    [
        InlineKeyboardButton(text=emoji.emojize(':brain: Учить'), callback_data='learn_definitions'),
    ],
])

async def get_initial_definition_keyboard():
    definitions = await sync_to_async(Definition.objects.filter)(is_initial=True)
    keyboard = InlineKeyboardMarkup()
    async for definition in definitions:
        keyboard.add(
            InlineKeyboardButton(text=f'{emoji.emojize(definition.emoji)} + {definition.name}',
                                      callback_data=f'definition_{definition.id}'),
        )
    return keyboard

