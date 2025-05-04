from telegram.ext import Application, CommandHandler, ChatMemberHandler, MessageHandler, filters, ContextTypes, CallbackContext, ConversationHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
from dotenv import load_dotenv
from BBotFuncs import *

# load_dotenv('.env.development')
load_dotenv('.env')

# токен API от BotFather
INSTRUCTION_URL = os.getenv('INSTRUCTION_URL')
TOKEN = os.getenv('TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')
SUPPORT_USERNAME = os.getenv('SUPPORT_USERNAME')

# Основная функция для запуска бота
def main():
    # Инициализация базы данных
    init_db()

    # Создаем приложение для бота
    application = Application.builder().token(TOKEN).build()

    # Добавляем ConversationHandler для /setbirthday
    set_birthday_handler = ConversationHandler(
        entry_points=[CommandHandler("setbirthday", set_birthday_start)],
        states={
            SET_BIRTHDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_birthday_save)],
        },
        fallbacks=[]
    )

    # Добавляем ConversationHandler для /removebirthday
    remove_birthday_handler = ConversationHandler(
        entry_points=[CommandHandler("removebirthday", remove_birthday_start)],
        states={
            REMOVE_BIRTHDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_birthday_save)],
        },
        fallbacks=[]
    )

    # Добавляем ConversationHandler для /setcongratulationtime
    set_congratulation_time_handler = ConversationHandler(
        entry_points=[CommandHandler("setcongratulationtime", set_congratulation_time_start)],
        states={
            SET_CONGRATULATION_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_congratulation_time_save)],
        },
        fallbacks=[]
    )

    # Добавляем обработчики команд
    application.add_handler(set_birthday_handler)
    application.add_handler(remove_birthday_handler)
    application.add_handler(set_congratulation_time_handler)
    application.add_handler(CommandHandler("listbirthdays", list_birthdays))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_to_group_command))
    application.add_handler(CommandHandler("instructions", instructions_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("showcongratulationtime", show_congratulation_time))

    # Обработчики событий
    application.add_handler(ChatMemberHandler(handle_my_chat_member_update, chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, handle_left_chat_member))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_joined))

    # Настройка планировщика задач
    loop = asyncio.get_event_loop()  # Получаем текущий цикл событий
    scheduler = AsyncIOScheduler(event_loop=loop, timezone='Europe/Moscow')
    scheduler.add_job(check_birthdays, "cron", minute="*", args=[application])
    scheduler.start()

    # Добавляем обработчик для кнопок меню
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))

    # Устанавливаем команды меню
    application.job_queue.run_once(set_commands, when=0)

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()