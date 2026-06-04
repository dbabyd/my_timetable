import os
import sys
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
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

# ==================== ГЛАВНОЕ МЕНЮ ====================
def get_main_menu():
    """Возвращает клавиатуру главного меню"""
    keyboard = [
        ['📊 Мой день', '📅 Расписание'],
        ['📝 Мои задачи', '📆 Полный календарь'],
        ['🔧 Управление', 'ℹ️ Помощь']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - показывает главное меню"""
    await update.message.reply_text(
        '👋 Привет! Я бот для управления расписанием и задачами.\n\n'
        'Выбери действие из меню ниже:',
        reply_markup=get_main_menu()
    )

# ==================== МОЙ ДЕНЬ ====================
async def my_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Мой день - показывает пары и задачи на сегодня"""
    await update.message.reply_text(
        '📊 <b>МОЙ ДЕНЬ</b>\n\n'
        '⏰ <b>Пары на сегодня:</b>\n'
        '• нет пар\n\n'
        '📝 <b>Задачи на сегодня:</b>\n'
        '• нет задач',
        parse_mode='HTML'
    )

# ==================== РАСПИСАНИЕ ====================
def get_schedule_menu():
    """Подменю расписания"""
    keyboard = [
        ['📅 Сегодня', '📅 Завтра'],
        ['📋 Неделя', '📆 Месяц'],
        ['🔙 Назад в меню']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📅 Расписание - подменю"""
    await update.message.reply_text(
        '📅 <b>РАСПИСАНИЕ</b>\n\n'
        'Выбери период:',
        reply_markup=get_schedule_menu(),
        parse_mode='HTML'
    )

async def schedule_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📅 Расписание на сегодня"""
    await update.message.reply_text(
        '📅 <b>РАСПИСАНИЕ НА СЕГОДНЯ</b>\n\n'
        '• нет пар',
        parse_mode='HTML'
    )

async def schedule_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📅 Расписание на завтра"""
    await update.message.reply_text(
        '📅 <b>РАСПИСАНИЕ НА ЗАВТРА</b>\n\n'
        '• нет пар',
        parse_mode='HTML'
    )

async def schedule_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Расписание на неделю"""
    await update.message.reply_text(
        '📋 <b>РАСПИСАНИЕ НА НЕДЕЛЮ</b>\n\n'
        '• нет пар',
        parse_mode='HTML'
    )

async def schedule_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📆 Расписание на месяц"""
    await update.message.reply_text(
        '📆 <b>РАСПИСАНИЕ НА МЕСЯЦ</b>\n\n'
        '• нет пар',
        parse_mode='HTML'
    )

# ==================== МОИ ЗАДАЧИ ====================
def get_tasks_menu():
    """Подменю задач"""
    keyboard = [
        ['📅 Задачи на дату', '📅 Задачи за период'],
        ['📂 Задачи по категории', '📋 Все задачи'],
        ['🔙 Назад в меню']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📝 Мои задачи - подменю"""
    await update.message.reply_text(
        '📝 <b>МОИ ЗАДАЧИ</b>\n\n'
        'Выбери опцию:',
        reply_markup=get_tasks_menu(),
        parse_mode='HTML'
    )

async def tasks_by_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📅 Задачи на дату"""
    await update.message.reply_text(
        '📅 <b>ЗАДАЧИ НА ДАТУ</b>\n\n'
        '• нет задач',
        parse_mode='HTML'
    )

async def tasks_by_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📅 Задачи за период"""
    await update.message.reply_text(
        '📅 <b>ЗАДАЧИ ЗА ПЕРИОД</b>\n\n'
        '• нет задач',
        parse_mode='HTML'
    )

async def tasks_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📂 Задачи по категории"""
    await update.message.reply_text(
        '📂 <b>ЗАДАЧИ ПО КАТЕГОРИИ</b>\n\n'
        '• нет категорий',
        parse_mode='HTML'
    )

async def all_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Все задачи"""
    await update.message.reply_text(
        '📋 <b>ВСЕ ЗАДАЧИ</b>\n\n'
        '• нет задач',
        parse_mode='HTML'
    )

# ==================== ПОЛНЫЙ КАЛЕНДАРЬ ====================
def get_calendar_menu():
    """Подменю календаря"""
    keyboard = [
        ['🗓 На дату', '🗓 Завтра'],
        ['🗓 Неделя', '🗓 Месяц', '🗓 Период'],
        ['🔙 Назад в меню']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📆 Полный календарь - подменю"""
    await update.message.reply_text(
        '📆 <b>ПОЛНЫЙ КАЛЕНДАРЬ</b>\n\n'
        'Выбери период:',
        reply_markup=get_calendar_menu(),
        parse_mode='HTML'
    )

async def calendar_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🗓 Календарь на дату"""
    await update.message.reply_text(
        '🗓 <b>КАЛЕНДАРЬ НА ДАТУ</b>\n\n'
        '• нет событий',
        parse_mode='HTML'
    )

async def calendar_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🗓 Календарь завтра"""
    await update.message.reply_text(
        '🗓 <b>КАЛЕНДАРЬ ЗАВТРА</b>\n\n'
        '• нет событий',
        parse_mode='HTML'
    )

async def calendar_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🗓 Календарь неделя"""
    await update.message.reply_text(
        '🗓 <b>КАЛЕНДАРЬ НА НЕДЕЛЮ</b>\n\n'
        '• нет событий',
        parse_mode='HTML'
    )

async def calendar_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🗓 Календарь месяц"""
    await update.message.reply_text(
        '🗓 <b>КАЛЕНДАРЬ НА МЕСЯЦ</b>\n\n'
        '• нет событий',
        parse_mode='HTML'
    )

async def calendar_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🗓 Календарь период"""
    await update.message.reply_text(
        '🗓 <b>КАЛЕНДАРЬ НА ПЕРИОД</b>\n\n'
        '• нет событий',
        parse_mode='HTML'
    )

# ==================== УПРАВЛЕНИЕ ====================
def get_management_menu():
    """Подменю управления"""
    keyboard = [
        ['📚 Управление парами', '📝 Управление задачами'],
        ['📂 Управление категориями', '⏰ Напоминания'],
        ['🔙 Назад в меню']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔧 Управление - подменю"""
    await update.message.reply_text(
        '🔧 <b>УПРАВЛЕНИЕ</b>\n\n'
        'Выбери что управлять:',
        reply_markup=get_management_menu(),
        parse_mode='HTML'
    )

def get_classes_menu():
    """Подменю управления парами"""
    keyboard = [
        ['➕ Добавить пару', '✏️ Изменить пару'],
        ['🗑 Удалить пару'],
        ['🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def manage_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📚 Управление парами"""
    await update.message.reply_text(
        '📚 <b>УПРАВЛЕНИЕ ПАРАМИ</b>\n\n'
        'Выбери действие:',
        reply_markup=get_classes_menu(),
        parse_mode='HTML'
    )

async def add_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """➕ Добавить пару"""
    await update.message.reply_text(
        '➕ <b>ДОБАВИТЬ ПАРУ</b>\n\n'
        'Эта функция вскоре будет реализована',
        parse_mode='HTML'
    )

def get_tasks_manage_menu():
    """Подменю управления задачами"""
    keyboard = [
        ['➕ Добавить задачу', '✏️ Изменить задачу'],
        ['🗑 Удалить задачу'],
        ['🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def manage_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📝 Управление задачами"""
    await update.message.reply_text(
        '📝 <b>УПРАВЛЕНИЕ ЗАДАЧАМИ</b>\n\n'
        'Выбери действие:',
        reply_markup=get_tasks_manage_menu(),
        parse_mode='HTML'
    )

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """➕ Добавить задачу"""
    await update.message.reply_text(
        '➕ <b>ДОБАВИТЬ ЗАДАЧУ</b>\n\n'
        'Эта функция вскоре будет реализована',
        parse_mode='HTML'
    )

def get_categories_menu():
    """Подменю управления категориями"""
    keyboard = [
        ['📋 Мои категории', '➕ Добавить категорию'],
        ['✏️ Изменить категорию', '🗑 Удалить категорию'],
        ['🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def manage_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📂 Управление категориями"""
    await update.message.reply_text(
        '📂 <b>УПРАВЛЕНИЕ КАТЕГОРИЯМИ</b>\n\n'
        'Выбери действие:',
        reply_markup=get_categories_menu(),
        parse_mode='HTML'
    )

async def my_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📋 Мои категории"""
    await update.message.reply_text(
        '📋 <b>МОИ КАТЕГОРИИ</b>\n\n'
        '• нет категорий',
        parse_mode='HTML'
    )

async def reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """⏰ Напоминания"""
    await update.message.reply_text(
        '⏰ <b>НАПОМИНАНИЯ</b>\n\n'
        '• нет активных напоминаний',
        parse_mode='HTML'
    )

# ==================== ПОМОЩЬ ====================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ℹ️ Помощь"""
    await update.message.reply_text(
        'ℹ️ <b>СПРАВКА</b>\n\n'
        '<b>Основные возможности:</b>\n'
        '📊 Мой день - пары и задачи на сегодня\n'
        '📅 Расписание - просмотр расписания\n'
        '📝 Мои задачи - управление задачами\n'
        '📆 Полный календарь - просмотр всех событий\n'
        '🔧 Управление - добавление/редактирование данных\n\n'
        '<b>Команды:</b>\n'
        '/start - главное меню\n'
        '/help - эта справка',
        parse_mode='HTML'
    )

# ==================== ОБРАБОТЧИК СООБЩЕНИЙ ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех сообщений из меню"""
    user_message = update.message.text
    
    # Главное меню
    if user_message == '📊 Мой день':
        await my_day(update, context)
    elif user_message == '📅 Расписание':
        await schedule(update, context)
    elif user_message == '📝 Мои задачи':
        await tasks(update, context)
    elif user_message == '📆 Полный календарь':
        await calendar(update, context)
    elif user_message == '🔧 Управление':
        await management(update, context)
    elif user_message == 'ℹ️ Помощь':
        await help_command(update, context)
    
    # Расписание
    elif user_message == '📅 Сегодня':
        await schedule_today(update, context)
    elif user_message == '📅 Завтра':
        await schedule_tomorrow(update, context)
    elif user_message == '📋 Неделя':
        await schedule_week(update, context)
    elif user_message == '📆 Месяц':
        await schedule_month(update, context)
    
    # Задачи
    elif user_message == '📅 Задачи на дату':
        await tasks_by_date(update, context)
    elif user_message == '📅 Задачи за период':
        await tasks_by_period(update, context)
    elif user_message == '📂 Задачи по категории':
        await tasks_by_category(update, context)
    elif user_message == '📋 Все задачи':
        await all_tasks(update, context)
    
    # Календарь
    elif user_message == '🗓 На дату':
        await calendar_date(update, context)
    elif user_message == '🗓 Завтра':
        await calendar_tomorrow(update, context)
    elif user_message == '🗓 Неделя':
        await calendar_week(update, context)
    elif user_message == '🗓 Месяц':
        await calendar_month(update, context)
    elif user_message == '🗓 Период':
        await calendar_period(update, context)
    
    # Управление
    elif user_message == '📚 Управление парами':
        await manage_classes(update, context)
    elif user_message == '📝 Управление задачами':
        await manage_tasks(update, context)
    elif user_message == '📂 Управление категориями':
        await manage_categories(update, context)
    elif user_message == '⏰ Напоминания':
        await reminders(update, context)
    
    # Управление парами
    elif user_message == '➕ Добавить пару':
        await add_class(update, context)
    elif user_message == '✏️ Изменить пару':
        await update.message.reply_text('✏️ <b>ИЗМЕНИТЬ ПАРУ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    elif user_message == '🗑 Удалить пару':
        await update.message.reply_text('🗑 <b>УДАЛИТЬ ПАРУ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    
    # Управление задачами
    elif user_message == '➕ Добавить задачу':
        await add_task(update, context)
    elif user_message == '✏️ Изменить задачу':
        await update.message.reply_text('✏️ <b>ИЗМЕНИТЬ ЗАДАЧУ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    elif user_message == '🗑 Удалить задачу':
        await update.message.reply_text('🗑 <b>УДАЛИТЬ ЗАДАЧУ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    
    # Управление категориями
    elif user_message == '📋 Мои категории':
        await my_categories(update, context)
    elif user_message == '➕ Добавить категорию':
        await update.message.reply_text('➕ <b>ДОБАВИТЬ КАТЕГОРИЮ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    elif user_message == '✏️ Изменить категорию':
        await update.message.reply_text('✏️ <b>ИЗМЕНИТЬ КАТЕГОРИЮ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    elif user_message == '🗑 Удалить категорию':
        await update.message.reply_text('🗑 <b>УДАЛИТЬ КАТЕГОРИЮ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    
    # Кнопка назад
    elif user_message == '🔙 Назад в меню' or user_message == '🔙 Назад':
        await start(update, context)
    
    else:
        await update.message.reply_text('Не знаю такой команды. Используй меню выше 👆')

# ==================== ОШИБКИ ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    print(f'⚠️ Ошибка: {context.error}')

# ==================== MAIN ====================
async def main():
    """Главная функция"""
    try:
        # Создаем приложение
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('help', help_command))
        
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
        
        # Устанавливаем webhook
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
