import os
import sys
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from aiohttp import web
from database import db
from datetime import datetime

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

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню без приветствия"""
    await update.message.reply_text(
        'Выбери действие:',
        reply_markup=get_main_menu()
    )

# ==================== МОЙ ДЕНЬ ====================
async def my_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """📊 Мой день - показывает пары и задачи на сегодня"""
    from datetime import datetime
    user_id = update.effective_user.id
    today = datetime.now().strftime('%d.%m')
    
    classes = db.get_classes_by_date(user_id, today)
    tasks = db.get_tasks_by_date(user_id, today)
    
    classes_text = '\n'.join([
        f"• <b>{c['name']}</b> - {c['start_time']}" + (f"-{c['end_time']}" if c['end_time'] else "") + 
        (f" ({c['classroom']})" if c['classroom'] else "")
        for c in classes
    ]) if classes else "• нет пар"
    
    tasks_text = '\n'.join([
        f"• <b>{t['name']}</b> - {t['status']}" + (f" ({t['category']})" if t['category'] else "")
        for t in tasks
    ]) if tasks else "• нет задач"
    
    await update.message.reply_text(
        f'📊 <b>МОЙ ДЕНЬ ({today})</b>\n\n'
        f'⏰ <b>Пары на сегодня:</b>\n'
        f'{classes_text}\n\n'
        f'📝 <b>Задачи на сегодня:</b>\n'
        f'{tasks_text}',
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
    from datetime import datetime
    user_id = update.effective_user.id
    today = datetime.now().strftime('%d.%m')
    
    classes = db.get_classes_by_date(user_id, today)
    classes_text = '\n'.join([
        f"• <b>{c['name']}</b> - {c['start_time']}" + (f"-{c['end_time']}" if c['end_time'] else "") + 
        (f" | {c['classroom']}" if c['classroom'] else "") + (f" | {c['teacher']}" if c['teacher'] else "")
        for c in classes
    ]) if classes else "• нет пар"
    
    await update.message.reply_text(
        f'📅 <b>РАСПИСАНИЕ НА СЕГОДНЯ ({today})</b>\n\n{classes_text}',
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
    print(f"DEBUG: Функция tasks() вызвана. Текст: {update.message.text}")
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
    user_id = update.effective_user.id
    all_tasks_list = db.get_tasks(user_id)
    
    tasks_text = '\n'.join([
        f"• <b>{t['name']}</b> ({t['date']}) - {t['status']}" + (f" | {t['category']}" if t['category'] else "")
        for t in all_tasks_list
    ]) if all_tasks_list else "• нет задач"
    
    await update.message.reply_text(
        f'📋 <b>ВСЕ ЗАДАЧИ</b>\n\n{tasks_text}',
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
    context.user_data['adding_class'] = True
    await update.message.reply_text(
        '➕ <b>ДОБАВИТЬ ПАРУ</b>\n\n'
        'Введи данные в формате:\n'
        '<code>Название; дата (ДД.MM); время начала (ЧЧ:МM); время конца (ЧЧ:МM); аудитория; преподаватель</code>\n\n'
        'Пример:\n'
        '<code>Математика; 15.06; 09:00; 10:30; 305; Иванов И.И.</code>\n\n'
        'Время конца, аудитория и преподаватель - необязательны.',
        parse_mode='HTML'
    )

async def delete_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🗑 Удалить пару"""
    user_id = update.effective_user.id
    classes = db.get_classes(user_id)
    
    if not classes:
        await update.message.reply_text('❌ У тебя нет добавленных пар.')
        return
    
    classes_list = '\n'.join([f"<b>{i+1}.</b> {c['name']} ({c['date']})" for i, c in enumerate(classes)])
    context.user_data['deleting_class'] = True
    
    await update.message.reply_text(
        f'🗑 <b>УДАЛИТЬ ПАРУ</b>\n\n'
        f'Твои пары:\n{classes_list}\n\n'
        f'Введи номер пары или её название для удаления:',
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
    context.user_data['adding_task'] = True
    await update.message.reply_text(
        '➕ <b>ДОБАВИТЬ ЗАДАЧУ</b>\n\n'
        'Введи данные в формате:\n'
        '<code>Название; дата (ДД.MM); статус (выполнена/не выполнена); категория</code>\n\n'
        'Пример:\n'
        '<code>Курсовая по БД; 20.06; не выполнена; Учёба</code>\n\n'
        'Категория - необязательна.',
        parse_mode='HTML'
    )

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🗑 Удалить задачу"""
    user_id = update.effective_user.id
    tasks = db.get_tasks(user_id)
    
    if not tasks:
        await update.message.reply_text('❌ У тебя нет добавленных задач.')
        return
    
    tasks_list = '\n'.join([f"<b>{i+1}.</b> {t['name']} ({t['date']})" for i, t in enumerate(tasks)])
    context.user_data['deleting_task'] = True
    
    await update.message.reply_text(
        f'🗑 <b>УДАЛИТЬ ЗАДАЧУ</b>\n\n'
        f'Твои задачи:\n{tasks_list}\n\n'
        f'Введи номер задачи или её название для удаления:',
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
    user_message = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Логирование для отладки
    print(f"DEBUG: Получено сообщение: '{user_message}' | Длина: {len(user_message)} | Код: {[ord(c) for c in user_message]}")
    
    # Обработка добавления пары
    if context.user_data.get('adding_class'):
        try:
            parts = [p.strip() for p in user_message.split(';')]
            if len(parts) < 3:
                await update.message.reply_text('❌ Ошибка формата! Укажи минимум: Название; дата; время начала')
                return
            
            name = parts[0]
            date = parts[1]
            start_time = parts[2]
            end_time = parts[3] if len(parts) > 3 else None
            classroom = parts[4] if len(parts) > 4 else None
            teacher = parts[5] if len(parts) > 5 else None
            
            if db.add_class(user_id, name, date, start_time, end_time, classroom, teacher):
                await update.message.reply_text(f'✅ Пара "<b>{name}</b>" добавлена!', parse_mode='HTML')
                context.user_data['adding_class'] = False
                await show_main_menu(update, context)
            else:
                await update.message.reply_text('❌ Ошибка при добавлении пары.')
        except Exception as e:
            await update.message.reply_text(f'❌ Ошибка: {e}')
        return
    
    # Обработка удаления пары
    if context.user_data.get('deleting_class'):
        classes = db.get_classes(user_id)
        try:
            # Пытаемся распарсить как номер
            class_num = int(user_message) - 1
            if 0 <= class_num < len(classes):
                class_id = classes[class_num]['id']
                if db.delete_class(user_id, class_id):
                    await update.message.reply_text(f'✅ Пара удалена!', parse_mode='HTML')
                    context.user_data['deleting_class'] = False
                    await show_main_menu(update, context)
                    return
        except ValueError:
            # Пытаемся удалить по названию
            if db.delete_class_by_name(user_id, user_message):
                await update.message.reply_text(f'✅ Пара удалена!', parse_mode='HTML')
                context.user_data['deleting_class'] = False
                await show_main_menu(update, context)
                return
        
        await update.message.reply_text('❌ Пара не найдена.')
        return
    
    # Обработка добавления задачи
    if context.user_data.get('adding_task'):
        try:
            parts = [p.strip() for p in user_message.split(';')]
            if len(parts) < 3:
                await update.message.reply_text('❌ Ошибка формата! Укажи минимум: Название; дата; статус')
                return
            
            name = parts[0]
            date = parts[1]
            status = parts[2]
            category = parts[3] if len(parts) > 3 else None
            
            if db.add_task(user_id, name, date, status, category):
                await update.message.reply_text(f'✅ Задача "<b>{name}</b>" добавлена!', parse_mode='HTML')
                context.user_data['adding_task'] = False
                await show_main_menu(update, context)
            else:
                await update.message.reply_text('❌ Ошибка при добавлении задачи.')
        except Exception as e:
            await update.message.reply_text(f'❌ Ошибка: {e}')
        return
    
    # Обработка удаления задачи
    if context.user_data.get('deleting_task'):
        tasks = db.get_tasks(user_id)
        try:
            # Пытаемся распарсить как номер
            task_num = int(user_message) - 1
            if 0 <= task_num < len(tasks):
                task_id = tasks[task_num]['id']
                if db.delete_task(user_id, task_id):
                    await update.message.reply_text(f'✅ Задача удалена!', parse_mode='HTML')
                    context.user_data['deleting_task'] = False
                    await show_main_menu(update, context)
                    return
        except ValueError:
            # Пытаемся удалить по названию
            if db.delete_task_by_name(user_id, user_message):
                await update.message.reply_text(f'✅ Задача удалена!', parse_mode='HTML')
                context.user_data['deleting_task'] = False
                await show_main_menu(update, context)
                return
        
        await update.message.reply_text('❌ Задача не найдена.')
        return
    
    # Главное меню - используем in вместо ==
    if 'Мой день' in user_message:
        await my_day(update, context)
    elif 'Расписание' in user_message and 'Полный' not in user_message:
        await schedule(update, context)
    elif 'Мои задачи' in user_message:
        print("DEBUG: Распознано 'Мои задачи', вызываю tasks()")
        await tasks(update, context)
    elif 'Полный календарь' in user_message:
        await calendar(update, context)
    elif 'Управление' in user_message:
        await management(update, context)
    elif 'Помощь' in user_message:
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
        await delete_class(update, context)
    
    # Управление задачами
    elif user_message == '➕ Добавить задачу':
        await add_task(update, context)
    elif user_message == '✏️ Изменить задачу':
        await update.message.reply_text('✏️ <b>ИЗМЕНИТЬ ЗАДАЧУ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    elif user_message == '🗑 Удалить задачу':
        await delete_task(update, context)
    
    # Управление категориями
    elif user_message == '📋 Мои категории':
        await my_categories(update, context)
    elif user_message == '➕ Добавить категорию':
        await update.message.reply_text('➕ <b>ДОБАВИТЬ КАТЕГОРИЮ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    elif user_message == '✏️ Изменить категорию':
        await update.message.reply_text('✏️ <b>ИЗМЕНИТЬ КАТЕГОРИЮ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    elif user_message == '🗑 Удалить категорию':
        await update.message.reply_text('🗑 <b>УДАЛИТЬ КАТЕГОРИЮ</b>\n\nЭта функция вскоре будет реализована', parse_mode='HTML')
    
    # Кнопка назад - показывает меню БЕЗ приветствия
    elif 'Назад' in user_message:
        await show_main_menu(update, context)
    
    else:
        print(f"DEBUG: Сообщение не распознано: '{user_message}'")
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
