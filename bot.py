import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv('8809640044:AAEzc6ROjT9C7zZuXBalz51GQOnFLeBnbiI')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start с голубой кнопкой"""
    keyboard = [['🚀 Начать']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        'Привет! 👋\nЯ телеграм-бот. Выбери действие:',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
    Доступные команды:
    /start - Начать работу с ботом
    /help - Показать эту справку
    /about - Информация о боте
    /echo - Эхо (введи текст после команды)
    """
    await update.message.reply_text(help_text)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /about"""
    await update.message.reply_text('Это простой телеграм-бот на Python 🤖')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /echo - повторяет текст"""
    if context.args:
        text = ' '.join(context.args)
        await update.message.reply_text(f'Ты сказал: {text}')
    else:
        await update.message.reply_text('Используй: /echo [текст]')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений"""
    user_message = update.message.text
    
    if user_message == '🚀 Начать':
        await update.message.reply_text('✅ Готово! Используй команды или напиши сообщение.')
    else:
        await update.message.reply_text(f'Ты написал: {user_message}')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    print(f'Ошибка: {context.error}')

def main():
    """Запуск бота"""
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('about', about))
    app.add_handler(CommandHandler('echo', echo))
    
    # Обработчик обычных сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    app.add_error_handler(error_handler)
    
    # Запускаем бота
    print('🤖 Бот запущен...')
    app.run_polling()

if __name__ == '__main__':
    main()
