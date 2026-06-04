import os
import sys
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web

# Получаем токен
BOT_TOKEN = '8924718816:AAHssdcvvw3K-ivD4BW9b0O4ZJ2vcMGFpC4'
PORT = int(os.environ.get('PORT', 8443))
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://my-timetable-bot.onrender.com')

# Проверка токена
if not BOT_TOKEN or BOT_TOKEN == 'YOUR_TOKEN_HERE':
    print('❌ ОШИБКА: Токен не установлен!')
    sys.exit(1)

if ':' not in BOT_TOKEN:
    print('❌ ОШИБКА: Токен имеет неправильный формат!')
    sys.exit(1)

print(f'✅ Токен загружен успешно')

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
    print(f'⚠️ Ошибка: {context.error}')

async def main():
    """Главная функция"""
    try:
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
        
        # Инициализируем приложение
        await app.initialize()
        
        # Создаем веб приложение для webhook
        web_app = web.Application()
        
        # Обработчик webhook
        async def handle_telegram(request):
            """Получает обновления от Telegram"""
            try:
                data = await request.json()
                update = Update.de_json(data, app.bot)
                await app.process_update(update)
                return web.Response(text='OK')
            except Exception as e:
                print(f'Ошибка в webhook: {e}')
                return web.Response(text='ERROR', status=500)
        
        web_app.router.add_post('/telegram', handle_telegram)
        
        # Создаем и запускаем веб сервер
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        
        print(f'✅ Webhook сервер запущен на порту {PORT}')
        print(f'✅ Webhook URL: {WEBHOOK_URL}/telegram')
        
        # Устанавлив��ем webhook
        webhook_url = f'{WEBHOOK_URL}/telegram'
        await app.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
        print(f'✅ Webhook установлен: {webhook_url}')
        
        # Запускаем бота
        await app.start()
        print('🤖 Бот запущен и готов получать сообщения...')
        
        # Бесконечный цикл
        try:
            await asyncio.sleep(3600)
        except KeyboardInterrupt:
            pass
        finally:
            await runner.cleanup()
            await app.stop()
        
    except Exception as e:
        print(f'❌ Критическая ошибка: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
