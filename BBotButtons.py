from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from BBot import BOT_USERNAME, SUPPORT_USERNAME, INSTRUCTION_URL

# Команды и меню

# Создаём клавиатуру с кнопками
reply_keyboard = [
    ["Добавить в группу", "Инструкция"],
    ["Поддержка"]
]
reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

# Создаём URL-кнопку для добавления бота в группу
add_to_group_button = InlineKeyboardButton(
    text="Добавить бота в группу",
    url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
)

# Создаём URL-кнопку для перехода в бот поддержки
support_button = InlineKeyboardButton(
    text="Обратиться в поддержку",
    url=f"https://t.me/{SUPPORT_USERNAME}"
)

# Создаём URL-кнопку для перехода к инструкции
instruction_button = InlineKeyboardButton(
    text="Перейти к инструкции",
    url=f"{INSTRUCTION_URL}"
)

add_inline_keyboard = InlineKeyboardMarkup([[add_to_group_button]])
support_inline_keyboard = InlineKeyboardMarkup([[support_button]])
instruction_inline_keyboard = InlineKeyboardMarkup([[instruction_button]])