import sqlite3
from datetime import datetime
from telegram.constants import ParseMode
import re
from pytz import timezone
from telegram import Update, BotCommand, BotCommandScopeAllChatAdministrators, BotCommandScopeAllGroupChats, BotCommandScopeDefault
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler
import asyncio
from BBotButtons import add_inline_keyboard, reply_markup, instruction_inline_keyboard, support_inline_keyboard

async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id, message_id, delay=0):
    await asyncio.sleep(delay)  # Ждём указанное количество секунд
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

async def start(update: Update, context: CallbackContext):
    # Отправляем приветственное сообщение с меню
    await update.message.reply_text(
        "Привет! Я бот для поздравлений с днем рождения в группе. Выберите действие из меню ниже.",
        reply_markup=reply_markup
    )
    asyncio.create_task(delete_message_after_delay(context, update.message.chat_id, update.message.message_id))

async def add_to_group_command(update: Update, context: CallbackContext):
    # Отправляем сообщение с URL-кнопкой
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы добавить меня в группу.",
        reply_markup=add_inline_keyboard
    )
    asyncio.create_task(delete_message_after_delay(context, update.message.chat_id, update.message.message_id))

async def instructions_command(update: Update, context: CallbackContext):
    # Пока без реализации
    await update.message.reply_text("Нажмите на кнопку ниже, чтобы перейти к инструкции.",
    reply_markup=instruction_inline_keyboard)
    asyncio.create_task(delete_message_after_delay(context, update.message.chat_id, update.message.message_id))
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Отправляем сообщение с кнопкой для бота поддержки
    await update.message.reply_text(
        "Если у вас возникли вопросы или проблемы, обратитесь в службу поддержки.",
        reply_markup=support_inline_keyboard
    )
    asyncio.create_task(delete_message_after_delay(context, update.message.chat_id, update.message.message_id))

async def set_commands(application):
    # Команды для личных чатов с ботом
    personal_commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("add", "Добавить бота в группу"),
        BotCommand("instructions", "Получить инструкцию"),
        BotCommand("support", "Обратиться в поддержку"),
    ]

    # Команды для всех групповых чатов (для обычных участников)
    group_commands = [
        BotCommand("setbirthday", "Установить свой день рождения"),
        BotCommand("listbirthdays", "Показать список дней рождения"),
        BotCommand("showcongratulationtime", "Показать время поздравления"),
    ]

    # Команды для администраторов групповых чатов
    admin_commands = [
        BotCommand("setbirthday", "Установить свой день рождения"),
        BotCommand("listbirthdays", "Показать список дней рождения"),
        BotCommand("removebirthday", "Удалить день рождения"),
        BotCommand("showcongratulationtime", "Показать время поздравления"),
        BotCommand("setcongratulationtime", "Установить время поздравлений"),
    ]

    # Устанавливаем команды для личных чатов
    await application.bot.set_my_commands(
        commands=personal_commands,
        scope=BotCommandScopeDefault()  # Глобальная область видимости (личные чаты)
    )

    # Устанавливаем команды для всех групповых чатов (для обычных участников)
    await application.bot.set_my_commands(
        commands=group_commands,
        scope=BotCommandScopeAllGroupChats()  # Все групповые чаты
    )

    # Устанавливаем команды для администраторов групповых чатов
    await application.bot.set_my_commands(
        commands=admin_commands,
        scope=BotCommandScopeAllChatAdministrators()  # Только администраторы
    )

async def handle_menu_buttons(update: Update, context: CallbackContext):
    # Обрабатываем нажатия на кнопки меню
    text = update.message.text

    if text == "Добавить в группу":
        # Отправляем сообщение с URL-кнопкой
        await update.message.reply_text(
            "Нажмите кнопку ниже, чтобы добавить меня в группу:",
            reply_markup=add_inline_keyboard
        )
        asyncio.create_task(
            delete_message_after_delay(context, update.message.chat_id, update.message.message_id))
    elif text == "Инструкция":
        await update.message.reply_text("Нажмите на кнопку ниже, чтобы перейти к инструкции.",
                                        reply_markup=instruction_inline_keyboard)
        asyncio.create_task(
            delete_message_after_delay(context, update.message.chat_id, update.message.message_id))
    elif text == "Поддержка":
        # Отправляем сообщение с кнопкой для бота поддержки
        await update.message.reply_text(
            "Если у вас возникли вопросы или проблемы, обратитесь в службу поддержки:",
            reply_markup=support_inline_keyboard
        )
        asyncio.create_task(
            delete_message_after_delay(context, update.message.chat_id, update.message.message_id))

# Подключение к базе данных
def init_db():
    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()
    # Создаем таблицу дней рождения
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS birthdays (
            chat_id INTEGER,
            user_id INTEGER,
            username TEXT, 
            birthday TEXT,
            UNIQUE(chat_id, user_id)
        )
    """)
    # Создаем таблицу настроек чатов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_settings (
            chat_id INTEGER PRIMARY KEY,
            congratulation_time TEXT DEFAULT '14:00'
        )
    """)
    conn.commit()
    conn.close()

SET_BIRTHDAY, REMOVE_BIRTHDAY, SET_CONGRATULATION_TIME = range(3)
# Добавление дня рождения
async def set_birthday_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем данные пользователя и чата
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    # Подключаемся к базе данных
    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()

    try:
        # Проверяем, существует ли запись для данного пользователя в текущем чате
        cursor.execute("""
            SELECT birthday FROM birthdays
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        result = cursor.fetchone()

        if result:
            # Если запись существует, отправляем сообщение и завершаем диалог
            birthday = result[0]
            await update.message.reply_text(
                f"У вас уже установлен день рождения: {birthday}. "
                "Если хотите удалить или изменить его, обратитесь к администратору."
            )
            return ConversationHandler.END

    finally:
        conn.close()

    # Если записи нет, предлагаем ввести дату
    await update.message.reply_text(
        "Введите ваш день рождения в формате ДД.ММ.ГГГГ:"
    )
    return SET_BIRTHDAY

async def set_birthday_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        birthday = update.message.text.strip()

        # Регулярное выражение для проверки формата даты (только ДД.ММ.ГГГГ)
        if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", birthday):
            await update.message.reply_text(
                "Дата должна быть в формате ДД.ММ.ГГГГ. Попробуйте установить снова."
            )
            return ConversationHandler.END

        # Разделяем дату на компоненты
        day, month, year = map(int, birthday.split("."))

        # Проверяем корректность даты и не является ли она будущей
        try:
            birth_date = datetime(year, month, day)
            now = datetime.now()
            if birth_date > now:
                await update.message.reply_text(
                    "Вы не можете установить дату рождения в будущем. Пожалуйста, введите корректную дату."
                )
                return ConversationHandler.END
        except ValueError:
            await update.message.reply_text(
                "Некорректная дата. Убедитесь, что день, месяц и год существуют, и попробуйте установить снова."
            )
            return ConversationHandler.END

        # Сохраняем дату в базу данных
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id
        username = update.message.from_user.username

        conn = sqlite3.connect("birthdays.db")
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO birthdays (chat_id, user_id, username, birthday)
                VALUES (?, ?, ?, ?)
            """, (chat_id, user_id, username, birthday))
            conn.commit()
            await update.message.reply_text(
                f"Ваш день рождения установлен на {birthday}"
            )
        except sqlite3.IntegrityError:
            await update.message.reply_text("Ваш день рождения уже установлен.")
        finally:
            conn.close()

    except Exception as e:
        print(f"Ошибка: {str(e)}")

    return ConversationHandler.END

async def remove_birthday_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(update.message.chat_id, update.message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Введите @username, упоминание пользователя или его ID для удаления:"
    )
    return REMOVE_BIRTHDAY


async def remove_birthday_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_identifier = None
    chat_id = update.message.chat_id
    text = update.message.text
    entities = update.message.entities

    # Попытка извлечь ID из текста, если это просто число
    try:
        target_identifier = int(text)
    except ValueError:
        # Если не число, проверяем наличие упоминания или юзернейма
        for entity in entities:
            if entity.type == "text_mention":  # Это упоминание без username
                target_identifier = entity.user.id
                break
            elif entity.type == "mention":  # Это username
                target_username = text[entity.offset:entity.offset + entity.length].lstrip("@")
                try:
                    # Ищем пользователя в базе данных по username
                    conn = sqlite3.connect("birthdays.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                            SELECT user_id FROM birthdays
                            WHERE chat_id = ? AND username = ?
                        """, (chat_id, target_username,))
                    result = cursor.fetchone()
                    conn.close()
                    if result:
                        target_identifier = result[0]
                    else:
                        await update.message.reply_text(f"Пользователь @{target_username} не найден в базе данных этого чата.")
                        return ConversationHandler.END
                except Exception as e:
                    print(f"Ошибка при поиске по username: {str(e)}")
                    return ConversationHandler.END
        # Если после всего target_identifier все еще None, возможно, введен некорректный формат
        if target_identifier is None:
            await update.message.reply_text(
                "Неверный формат идентификатора. Используйте @username, упоминание или ID пользователя."
            )
            return ConversationHandler.END

    # Теперь у нас есть target_identifier (user_id), удаляем запись
    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()
    cursor.execute("""
            DELETE FROM birthdays
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, target_identifier))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()

    if rows_affected > 0:
        try:
            target_user = await context.bot.get_chat_member(chat_id, target_identifier)
            mention = f"<a href='tg://user?id={target_identifier}'>{target_user.user.full_name}</a>"
            await update.message.reply_text(f"День рождения пользователя {mention} удален.", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"День рождения пользователя с ID {target_identifier} удален.")
    else:
        await update.message.reply_text(f"Пользователь с ID {target_identifier} не найден в списке дней рождения.")

    return ConversationHandler.END

async def set_congratulation_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(update.message.chat_id, update.message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")

        return ConversationHandler.END

    await update.message.reply_text(
        "Введите новое время поздравлений в формате ЧЧ:ММ (МСК):"
    )
    return SET_CONGRATULATION_TIME


async def set_congratulation_time_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_time = update.message.text.strip()
        # Проверка формата времени
        if not re.match(r"^\d{2}:\d{2}$", new_time):
            await update.message.reply_text(
                "Неверный формат времени. Используйте формат ЧЧ:ММ."
            )
            return ConversationHandler.END

        hour, minute = map(int, new_time.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            await update.message.reply_text(
                "Неверное время. Убедитесь, что часы и минуты находятся в допустимых пределах."
            )
            return ConversationHandler.END

        chat_id = update.message.chat_id
        conn = sqlite3.connect("birthdays.db")
        cursor = conn.cursor()
        # Обновляем или создаем запись с временем поздравлений
        cursor.execute("""
            INSERT OR REPLACE INTO chat_settings (chat_id, congratulation_time)
            VALUES (?, ?)
        """, (chat_id, new_time))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"Время поздравлений успешно установлено на {new_time} МСК."
        )
    except Exception as e:
        print(f"Ошибка: {str(e)}")

    return ConversationHandler.END

# Обработчик события "Новый участник присоединился к чату"
async def new_member_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_id = context.bot.id  # ID самого бота
    for member in update.message.new_chat_members:
        # Игнорируем, если новый участник — это сам бот
        if member.id == bot_id:
            continue

        full_name = member.full_name
        mention = f"<a href='tg://user?id={member.id}'>{full_name}</a>"

        welcome_message = (
            f"Добро пожаловать, {mention}! 🎉\n"
            "Рады видеть вас в нашем чате!"
            "Вот список доступных команд:"
            "- /setbirthday — установить свой день рождения."
            "- /listbirthdays — показать список дней рождения в этом чате."
            "- /showcongratulationtime — показать время отправки поздравлений."
            "Для администраторов:"
            "- /removebirthday — удалить день рождения."
            "- /setcongratulationtime — установить время отправки поздравлений."
        )
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.HTML)

# Обработчик события "Изменение статуса бота"
async def handle_my_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_id = context.bot.id
    chat = update.effective_chat
    new_status = update.my_chat_member.new_chat_member.status

    # Обработка добавления бота (как и раньше)
    if update.my_chat_member.new_chat_member.user.id == bot_id and new_status in ["member", "administrator"]:
        conn = sqlite3.connect("birthdays.db")
        cursor = conn.cursor()
        try:
            cursor.execute("""
                        INSERT OR IGNORE INTO chat_settings (chat_id, congratulation_time)
                        VALUES (?, '10:00')
                    """, (chat.id,))
            conn.commit()
        finally:
            conn.close()

        await context.bot.send_message(
            chat_id=chat.id,
            text="""
                Здравствуйте! Я бот для поздравлений с Днем рождения!
                Вот список доступных команд:
            - /setbirthday — установить свой день рождения.
            - /listbirthdays — показать список дней рождения в этом чате.
            - /showcongratulationtime — показать время отправки поздравлений.
                Для администраторов:
            - /removebirthday — удалить день рождения.
            - /setcongratulationtime — установить время отправки поздравлений.
            """,
            parse_mode=ParseMode.HTML
        )

# Вывод списка дней рождения
async def list_birthdays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, birthday FROM birthdays WHERE chat_id = ?", (chat_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Список дней рождения пуст.")
        return

    message = "Список дней рождения:\n"
    for user_id, birthday in rows:
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            mention = f"<a href='tg://user?id={user_id}'>{chat_member.user.full_name}</a>"
            message += f"{mention}: {birthday}\n"
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)


async def show_congratulation_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()

    cursor.execute("SELECT congratulation_time FROM chat_settings WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()

    if result:
        time = result[0]
        await update.message.reply_text(f"Текущее время поздравлений: {time} МСК")
    else:
        await update.message.reply_text(
            "Время поздравлений не установлено. Используется значение по умолчанию: 10:00 МСК")

    conn.close()


async def check_birthdays(context: ContextTypes.DEFAULT_TYPE):
    print("Проверка дней рождения запущена.")
    moscow_tz = timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz).strftime("%H:%M")  # Текущее время
    today = datetime.now(moscow_tz).strftime("%d.%m")  # Текущая дата
    current_year = datetime.now(moscow_tz).year  # Текущий год

    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()

    # Получаем все чаты с их временами поздравлений
    cursor.execute("SELECT chat_id, congratulation_time FROM chat_settings")
    chat_times = dict(cursor.fetchall())

    for chat_id, time in chat_times.items():
        if time == current_time:
            # Проверяем дни рождения для этого чата
            cursor.execute("""
                SELECT user_id, birthday FROM birthdays
                WHERE chat_id = ? AND birthday LIKE ?
            """, (chat_id, f"{today}.%"))
            rows = cursor.fetchall()

            for user_id, birthday in rows:
                try:
                    day, month, birth_year = map(int, birthday.split("."))
                    age = current_year - birth_year
                    if datetime.now(moscow_tz) < datetime(current_year, month, day, tzinfo=moscow_tz):
                        age -= 1

                    chat_member = await context.bot.get_chat_member(chat_id, user_id)
                    mention = f"<a href='tg://user?id={user_id}'>{chat_member.user.full_name}</a>"

                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🎉 Сегодня день рождения у {mention}! Поздравляем с {age} годами! 🎉",
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    print(f"Ошибка при отправке поздравления: {e}")

    conn.close()

async def handle_left_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что событие связано с исключением или выходом участника
    if not update.message or not update.message.left_chat_member:
        return

    # Удаляем запись пользователя из базы данных для этого чата
    chat_id = update.message.chat_id
    user = update.message.left_chat_member  # Пользователь, который покинул чат
    user_id = user.id

    conn = sqlite3.connect("birthdays.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM birthdays
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        conn.commit()

        # Отправляем простое текстовое сообщение в ответ
        if cursor.rowcount > 0:
            sent_message = await update.message.reply_text(
                "Пользователь покинул чат. Запись о его дне рождения удалена."
            )
        else:
            print(f"Ошибка: Пользователь с ID {user_id} не найден в базе данных для чата {chat_id}.")
    except Exception as e:
        print(f"Ошибка: {str(e)}")
    finally:
        conn.close()
