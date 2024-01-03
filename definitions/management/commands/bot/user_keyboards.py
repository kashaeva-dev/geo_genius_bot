import logging
import emoji

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

