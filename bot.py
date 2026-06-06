
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from database import db

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("8924718816:AAHssdcvvw3K-ivD4BW9b0O4ZJ2vcMGFpC4")

DAYS = [
    "Понедельник", "Вторник", "Среда",
    "Четверг", "Пятница", "Суббота", "Воскресенье",
]

MONTHS = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

VALID_REM = [
    "За 15 минут", "За 30 минут", "За 1 час",
    "За 2 часа", "За 24 часа", "🚫 Не напоминать",
]

VALID_REP = [
    "🔄 Каждый день", "🔄 Каждую неделю",
    "🔄 Каждый месяц", "🚫 Без повтора",
]

# Состояния диалогов — пары
(
    AL_DAY, AL_INFO, AL_REM, AL_CREM_TYPE, AL_CREM_VAL, AL_REP,
    DL_DAY, DL_PICK,
    EL_DAY, EL_PICK, EL_FIELD, EL_VAL,
) = range(12)

# Состояния диалогов — задачи
(
    AT_CAT, AT_INFO, AT_DT, AT_REM, AT_CREM_TYPE, AT_CREM_VAL, AT_REP,
    DT_PICK,
    ET_PICK, ET_FIELD, ET_VAL,
    VT_DATE, VT_FROM, VT_TO, VT_CAT,
) = range(100, 115)

# Состояния диалогов — категории
(
    AC_EMOJI, AC_NAME,
    DC_PICK,
    EC_PICK, EC_FIELD, EC_VAL,
) = range(200, 206)

# Состояния диалогов — календарь
(
    CAL_DATE, CAL_FROM, CAL_TO,
) = range(300, 303)


# ═══════════ Утилиты ═══════════

def valid_time(t: str) -> bool:
    try:
        datetime.strptime(t.strip(), "%H:%M")
        return True
    except ValueError:
        return False


def valid_date(d: str) -> bool:
    try:
        datetime.strptime(d.strip(), "%d.%m.%Y")
        return True
    except ValueError:
        return False


def pretty_date(ds: str) -> str:
    try:
        dt = datetime.strptime(ds, "%d.%m.%Y")
        return f"{dt.day} {MONTHS[dt.month]} {dt.year}, {DAYS[dt.weekday()]}"
    except ValueError:
        return ds


def date_range(d1: str, d2: str) -> list[str]:
    start = datetime.strptime(d1, "%d.%m.%Y")
    end = datetime.strptime(d2, "%d.%m.%Y")
    result = []
    cur = start
    while cur <= end:
        result.append(cur.strftime("%d.%m.%Y"))
        cur += timedelta(days=1)
    return result


def fmt_lesson(lesson: dict) -> str:
    text = (
        f"🕐 {lesson.get('time', '—')}\n"
        f"📖 {lesson.get('subject', '—')}\n"
        f"🏫 {lesson.get('room', '—')}\n"
        f"👨‍🏫 {lesson.get('teacher', '—')}"
    )
    r = lesson.get("reminder", "")
    if r and r != "🚫 Не напоминать":
        text += f"\n⏰ {r}"
    rp = lesson.get("repeat", "")
    if rp and rp != "🚫 Без повтора":
        text += f"\n🔁 {rp}"
    return text


def fmt_task(task: dict) -> str:
    text = (
        f"{task.get('cat_emoji', '📌')} {task.get('cat_name', 'Без категории')}\n"
        f"📝 {task.get('title', '—')}"
    )
    if task.get("description"):
        text += f"\n💬 {task['description']}"
    if task.get("date"):
        text += f"\n📅 {pretty_date(task['date'])}"
    if task.get("time"):
        text += f"\n🕐 {task['time']}"
    r = task.get("reminder", "")
    if r and r != "🚫 Не напоминать":
        text += f"\n⏰ {r}"
    rp = task.get("repeat", "")
    if rp and rp != "🚫 Без повтора":
        text += f"\n🔁 {rp}"
    return text


# ═══════════ Клавиатуры ═══════════

def kb(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

K_MAIN = [
    ["📊 Мой день"],
    ["📅 Расписание", "📝 Мои задачи"],
    ["📆 Полный календарь"],
    ["🔧 Управление", "ℹ️ Помощь"],
]
K_SCHED = [
    ["📅 Сегодня", "📅 Завтра"],
    ["📋 Неделя", "📆 Месяц"],
    ["🔙 Меню"],
]
K_TASKS = [
    ["📅 Задачи на дату", "📅 Задачи за период"],
    ["📂 Задачи по категории", "📋 Все задачи"],
    ["🔙 Меню"],
]
K_CAL = [
    ["🗓 Календарь на дату", "🗓 Календарь завтра"],
    ["🗓 Календарь неделя", "🗓 Календарь месяц"],
    ["🗓 Календарь период"],
    ["🔙 Меню"],
]
K_MNG = [
    ["📚 Управление парами", "📝 Управление задачами"],
    ["📂 Управление категориями", "⏰ Напоминания"],
    ["🔙 Меню"],
]
K_ML = [["➕ Добавить пару"], ["✏️ Изменить пару", "🗑 Удалить пару"], ["🔙 К управлению"]]
K_MT = [["➕ Добавить задачу"], ["✏️ Изменить задачу", "🗑 Удалить задачу"], ["🔙 К управлению"]]
K_MC = [["📋 Мои категории"], ["➕ Добавить категорию"], ["✏️ Изменить категорию", "🗑 Удалить категорию"], ["🔙 К управлению"]]
K_X = [["❌ Отмена"]]
K_DAYS = [[d] for d in DAYS] + [["❌ Отмена"]]
K_REM = [["За 15 минут", "За 30 минут"], ["За 1 час", "За 2 часа"], ["За 24 часа"], ["⏰ Своё время", "🚫 Не напоминать"], ["❌ Отмена"]]
K_CREM = [["⏱ За N минут до"], ["🕐 В точное время"], ["❌ Отмена"]]
K_REP = [["🔄 Каждый день", "🔄 Каждую неделю"], ["🔄 Каждый месяц", "🚫 Без повтора"], ["❌ Отмена"]]


def kb_cats(user_id: int):
    cats = db.get_categories(user_id)
    rows = [[f"{c['emoji']} {c['name']}"] for c in cats]
    rows += [["📌 Без категории"], ["❌ Отмена"]]
    return rows


# ═══════════ Команды ═══════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    db._ensure_default_categories(uid)
    await ctx.bot.set_my_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("help", "Помощь"),
    ])
    text = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Я — твой бот-помощник для учёбы 🎓\n\n"
        "Здесь ты можешь:\n"
        "• вести расписание пар\n"
        "• добавлять задачи с напоминаниями\n"
        "• использовать категории\n"
        "• видеть всё в одном календаре\n\n"
        "Выбирай раздел 👇"
    )
    await update.message.reply_text(text, reply_markup=kb(K_MAIN))


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ Справка\n\n"
        "📊 Мой день — пары и задачи на сегодня\n"
        "📅 Расписание — пары по дням\n"
        "📝 Мои задачи — задачи на дату, за период, по категории\n"
        "📆 Полный календарь — пары и задачи вместе\n"
        "🔧 Управление — добавить, изменить, удалить\n\n"
        "/start — перезапуск"
    )
    await update.message.reply_text(text, reply_markup=kb(K_MAIN))


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Отменено", reply_markup=kb(K_MAIN))
    return ConversationHandler.END


# ═══════════ Навигация ═══════════

async def nav_main(u, c): await u.message.reply_text("Выбирай раздел 👇", reply_markup=kb(K_MAIN))
async def nav_sched(u, c): await u.message.reply_text("📅 Расписание\n\nВыбери период:", reply_markup=kb(K_SCHED))
async def nav_tasks(u, c): await u.message.reply_text("📝 Мои задачи\n\nКак показать?", reply_markup=kb(K_TASKS))
async def nav_cal(u, c): await u.message.reply_text("📆 Полный календарь\n\nПары + задачи:", reply_markup=kb(K_CAL))
async def nav_mng(u, c): await u.message.reply_text("🔧 Управление\n\nЧто настроить?", reply_markup=kb(K_MNG))
async def nav_ml(u, c): await u.message.reply_text("📚 Пары\n\nВыбери действие:", reply_markup=kb(K_ML))
async def nav_mt(u, c): await u.message.reply_text("📝 Задачи\n\nВыбери действие:", reply_markup=kb(K_MT))
async def nav_mc(u, c): await u.message.reply_text("📂 Категории\n\nВыбери действие:", reply_markup=kb(K_MC))


# ═══════════ Мой день ═══════════

async def my_day(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    now = datetime.now()
    day_name = DAYS[now.weekday()]
    ds = now.strftime("%d.%m.%Y")
    lessons = db.get_lessons_by_day(uid, day_name)
    tasks = db.get_tasks_by_date(uid, ds)
    text = f"📊 Сегодня — {pretty_date(ds)}\n\n"
    if lessons:
        text += "📚 Пары:\n\n"
        for le in lessons:
            text += fmt_lesson(le) + "\n\n"
    if tasks:
        text += "📝 Задачи:\n\n"
        for ta in tasks:
            text += fmt_task(ta) + "\n\n"
    if not lessons and not tasks:
        text += "На сегодня ничего не запланировано 🎉"
    await update.message.reply_text(text, reply_markup=kb(K_MAIN))


# ═══════════ Расписание ═══════════

async def sched_today(u, c):
    uid = u.effective_user.id
    day_name = DAYS[datetime.now().weekday()]
    lessons = db.get_lessons_by_day(uid, day_name)
    text = f"📅 {day_name}\n\n"
    text += "\n\n".join(fmt_lesson(le) for le in lessons) if lessons else "На сегодня пар нет 🎉"
    await u.message.reply_text(text, reply_markup=kb(K_SCHED))


async def sched_tmr(u, c):
    uid = u.effective_user.id
    day_name = DAYS[(datetime.now() + timedelta(days=1)).weekday()]
    lessons = db.get_lessons_by_day(uid, day_name)
    text = f"📅 {day_name}\n\n"
    text += "\n\n".join(fmt_lesson(le) for le in lessons) if lessons else "На завтра пар нет 🎉"
    await u.message.reply_text(text, reply_markup=kb(K_SCHED))


async def sched_week(u, c):
    uid = u.effective_user.id
    all_lessons = db.get_all_lessons(uid)
    text = "📋 Расписание на неделю\n\n"
    if not all_lessons:
        text += "На этой неделе пар нет 🎉"
    else:
        for day, lessons in all_lessons.items():
            text += f"📅 {day}\n"
            for le in lessons:
                text += f"    🕐 {le['time']} — {le['subject']} ({le.get('room', '—')})\n"
            text += "\n"
    await u.message.reply_text(text, reply_markup=kb(K_SCHED))


async def sched_month(u, c):
    uid = u.effective_user.id
    now = datetime.now()
    text = f"📆 {MONTHS[now.month].capitalize()} {now.year}\n\n"
    found = False
    day_num = 1
    while True:
        try:
            dt = datetime(now.year, now.month, day_num)
        except ValueError:
            break
        day_name = DAYS[dt.weekday()]
        lessons = db.get_lessons_by_day(uid, day_name)
        if lessons:
            found = True
            text += f"📅 {dt.day} {MONTHS[now.month]}, {day_name}\n"
            for le in lessons:
                text += f"    🕐 {le['time']} — {le['subject']}\n"
            text += "\n"
        day_num += 1
    if not found:
        text += "В этом месяце пар нет 🎉"
    await u.message.reply_text(text, reply_markup=kb(K_SCHED))


# ═══════════ Просмотр задач ═══════════

async def view_tasks_all(u, c):
    uid = u.effective_user.id
    tasks = db.get_all_tasks(uid)
    text = "📋 Все задачи\n\n"
    if not tasks:
        text += "У тебя пока нет задач"
    else:
        for i, ta in enumerate(tasks, 1):
            text += f"{i}. {fmt_task(ta)}\n\n"
    await u.message.reply_text(text, reply_markup=kb(K_TASKS))


async def vt_date_s(u, c):
    await u.message.reply_text("📅 Введи дату (ДД.ММ.ГГГГ):", reply_markup=kb(K_X))
    return VT_DATE

async def vt_date(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_TASKS))
        return ConversationHandler.END
    if not valid_date(u.message.text):
        await u.message.reply_text("❌ Формат: ДД.ММ.ГГГГ", reply_markup=kb(K_X))
        return VT_DATE
    ds = u.message.text.strip()
    tasks = db.get_tasks_by_date(u.effective_user.id, ds)
    text = f"📅 Задачи на {pretty_date(ds)}\n\n"
    text += "\n\n".join(f"{i}. {fmt_task(ta)}" for i, ta in enumerate(tasks, 1)) if tasks else "На эту дату задач нет"
    await u.message.reply_text(text, reply_markup=kb(K_TASKS))
    return ConversationHandler.END


async def vt_period_s(u, c):
    await u.message.reply_text("📅 Начало периода (ДД.ММ.ГГГГ):", reply_markup=kb(K_X))
    return VT_FROM

async def vt_from(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_TASKS))
        return ConversationHandler.END
    if not valid_date(u.message.text):
        await u.message.reply_text("❌ Формат: ДД.ММ.ГГГГ", reply_markup=kb(K_X))
        return VT_FROM
    c.user_data["vf"] = u.message.text.strip()
    await u.message.reply_text("📅 Конец периода (ДД.ММ.ГГГГ):", reply_markup=kb(K_X))
    return VT_TO

async def vt_to(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_TASKS))
        return ConversationHandler.END
    if not valid_date(u.message.text):
        await u.message.reply_text("❌ Формат: ДД.ММ.ГГГГ", reply_markup=kb(K_X))
        return VT_TO
    d1, d2 = c.user_data["vf"], u.message.text.strip()
    tasks = db.get_tasks_by_date_range(u.effective_user.id, d1, d2)
    text = f"📅 Задачи {d1} — {d2}\n\n"
    text += "\n\n".join(f"{i}. {fmt_task(ta)}" for i, ta in enumerate(tasks, 1)) if tasks else "За этот период задач нет"
    await u.message.reply_text(text, reply_markup=kb(K_TASKS))
    return ConversationHandler.END


async def vt_cat_s(u, c):
    await u.message.reply_text("📂 Выбери категорию:", reply_markup=kb(kb_cats(u.effective_user.id)))
    return VT_CAT

async def vt_cat(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_TASKS))
        return ConversationHandler.END
    selected = u.message.text
    parts = selected.split(" ", 1)
    if len(parts) < 2:
        await u.message.reply_text("Отменено", reply_markup=kb(K_TASKS))
        return ConversationHandler.END
    cat_emoji, cat_name = parts[0], parts[1]
    tasks = db.get_tasks_by_category(u.effective_user.id, cat_name, cat_emoji)
    text = f"📂 {selected}\n\n"
    text += "\n\n".join(f"{i}. {fmt_task(ta)}" for i, ta in enumerate(tasks, 1)) if tasks else "В этой категории задач нет"
    await u.message.reply_text(text, reply_markup=kb(K_TASKS))
    return ConversationHandler.END


# ═══════════ Полный календарь ═══════════

async def cal_tmr(u, c):
    uid = u.effective_user.id
    tmr = datetime.now() + timedelta(days=1)
    ds = tmr.strftime("%d.%m.%Y")
    day_name = DAYS[tmr.weekday()]
    lessons = db.get_lessons_by_day(uid, day_name)
    tasks = db.get_tasks_by_date(uid, ds)
    text = f"📆 {pretty_date(ds)}\n\n"
    if lessons:
        text += "📚 Пары:\n" + "\n\n".join(fmt_lesson(le) for le in lessons) + "\n\n"
    if tasks:
        text += "📝 Задачи:\n" + "\n\n".join(fmt_task(ta) for ta in tasks) + "\n\n"
    if not lessons and not tasks:
        text += "На завтра ничего не запланировано 🎉"
    await u.message.reply_text(text, reply_markup=kb(K_CAL))


async def cal_week(u, c):
    uid = u.effective_user.id
    now = datetime.now()
    start = now - timedelta(days=now.weekday())
    text = "📆 Неделя — пары + задачи\n\n"
    found = False
    for i in range(7):
        dt = start + timedelta(days=i)
        ds = dt.strftime("%d.%m.%Y")
        day_name = DAYS[dt.weekday()]
        lessons = db.get_lessons_by_day(uid, day_name)
        tasks = db.get_tasks_by_date(uid, ds)
        if lessons or tasks:
            found = True
            text += f"📅 {pretty_date(ds)}\n"
            for le in lessons:
                text += f"    🕐 {le['time']} — {le['subject']}\n"
            for ta in tasks:
                tp = f"🕐 {ta['time']} " if ta.get("time") else ""
                text += f"    {tp}{ta.get('cat_emoji', '📌')} {ta['title']}\n"
            text += "\n"
    if not found:
        text += "На этой неделе ничего не запланировано 🎉"
    await u.message.reply_text(text, reply_markup=kb(K_CAL))


async def cal_month(u, c):
    uid = u.effective_user.id
    now = datetime.now()
    text = f"📆 {MONTHS[now.month].capitalize()} — пары + задачи\n\n"
    found = False
    day_num = 1
    while True:
        try:
            dt = datetime(now.year, now.month, day_num)
        except ValueError:
            break
        ds = dt.strftime("%d.%m.%Y")
        day_name = DAYS[dt.weekday()]
        lessons = db.get_lessons_by_day(uid, day_name)
        tasks = db.get_tasks_by_date(uid, ds)
        if lessons or tasks:
            found = True
            text += f"📅 {dt.day} {MONTHS[now.month]}, {day_name}\n"
            for le in lessons:
                text += f"    🕐 {le['time']} — {le['subject']}\n"
            for ta in tasks:
                tp = f"🕐 {ta['time']} " if ta.get("time") else ""
                text += f"    {tp}{ta.get('cat_emoji', '📌')} {ta['title']}\n"
            text += "\n"
        day_num += 1
    if not found:
        text += "В этом месяце ничего не запланировано 🎉"
    await u.message.reply_text(text, reply_markup=kb(K_CAL))


async def cal_date_s(u, c):
    await u.message.reply_text("📅 Дата (ДД.ММ.ГГГГ):", reply_markup=kb(K_X))
    return CAL_DATE

async def cal_date(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_CAL))
        return ConversationHandler.END
    if not valid_date(u.message.text):
        await u.message.reply_text("❌ Формат: ДД.ММ.ГГГГ", reply_markup=kb(K_X))
        return CAL_DATE
    ds = u.message.text.strip()
    uid = u.effective_user.id
    day_name = DAYS[datetime.strptime(ds, "%d.%m.%Y").weekday()]
    lessons = db.get_lessons_by_day(uid, day_name)
    tasks = db.get_tasks_by_date(uid, ds)
    text = f"📆 {pretty_date(ds)}\n\n"
    if lessons:
        text += "📚 Пары:\n" + "\n\n".join(fmt_lesson(le) for le in lessons) + "\n\n"
    if tasks:
        text += "📝 Задачи:\n" + "\n\n".join(fmt_task(ta) for ta in tasks) + "\n\n"
    if not lessons and not tasks:
        text += "На эту дату ничего не запланировано 🎉"
    await u.message.reply_text(text, reply_markup=kb(K_CAL))
    return ConversationHandler.END


async def cal_period_s(u, c):
    await u.message.reply_text("📅 Начало (ДД.ММ.ГГГГ):", reply_markup=kb(K_X))
    return CAL_FROM

async def cal_from(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_CAL))
        return ConversationHandler.END
    if not valid_date(u.message.text):
        await u.message.reply_text("❌ Формат: ДД.ММ.ГГГГ", reply_markup=kb(K_X))
        return CAL_FROM
    c.user_data["cf"] = u.message.text.strip()
    await u.message.reply_text("📅 Конец (ДД.ММ.ГГГГ):", reply_markup=kb(K_X))
    return CAL_TO

async def cal_to(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_CAL))
        return ConversationHandler.END
    if not valid_date(u.message.text):
        await u.message.reply_text("❌ Формат: ДД.ММ.ГГГГ", reply_markup=kb(K_X))
        return CAL_TO
    d1, d2 = c.user_data["cf"], u.message.text.strip()
    uid = u.effective_user.id
    text = f"📆 {d1} — {d2}\n\n"
    found = False
    for ds in date_range(d1, d2):
        day_name = DAYS[datetime.strptime(ds, "%d.%m.%Y").weekday()]
        lessons = db.get_lessons_by_day(uid, day_name)
        tasks = db.get_tasks_by_date(uid, ds)
        if lessons or tasks:
            found = True
            text += f"📅 {pretty_date(ds)}\n"
            for le in lessons:
                text += f"    🕐 {le['time']} — {le['subject']}\n"
            for ta in tasks:
                tp = f"🕐 {ta['time']} " if ta.get("time") else ""
                text += f"    {tp}{ta.get('cat_emoji', '📌')} {ta['title']}\n"
            text += "\n"
    if not found:
        text += "За этот период ничего не запланировано 🎉"
    await u.message.reply_text(text, reply_markup=kb(K_CAL))
    return ConversationHandler.END


# ═══════════ Добавление пары ═══════════

async def al_start(u, c):
    await u.message.reply_text("📚 Выбери день недели:", reply_markup=kb(K_DAYS))
    return AL_DAY

async def al_day(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    if u.message.text not in DAYS:
        await u.message.reply_text("Выбери из списка", reply_markup=kb(K_DAYS))
        return AL_DAY
    c.user_data["day"] = u.message.text
    await u.message.reply_text(
        f"📅 {u.message.text}\n\nВведи через запятую:\n"
        "Предмет, Время, Аудитория, Преподаватель\n\n"
        "Пример:\nМатематика, 09:00, 301, Иванов И.И.",
        reply_markup=kb(K_X))
    return AL_INFO

async def al_info(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    parts = [p.strip() for p in u.message.text.split(",")]
    if len(parts) < 4:
        await u.message.reply_text("❌ Нужно 4 значения через запятую", reply_markup=kb(K_X))
        return AL_INFO
    if not valid_time(parts[1]):
        await u.message.reply_text("❌ Время в формате ЧЧ:ММ", reply_markup=kb(K_X))
        return AL_INFO
    c.user_data["subj"] = parts[0]
    c.user_data["time"] = parts[1].strip()
    c.user_data["room"] = parts[2]
    c.user_data["teach"] = parts[3]
    await u.message.reply_text("⏰ Напоминание:", reply_markup=kb(K_REM))
    return AL_REM

async def al_rem(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    if u.message.text == "⏰ Своё время":
        await u.message.reply_text("Как задать?", reply_markup=kb(K_CREM))
        return AL_CREM_TYPE
    if u.message.text not in VALID_REM:
        await u.message.reply_text("Выбери из кнопок", reply_markup=kb(K_REM))
        return AL_REM
    c.user_data["rem"] = u.message.text
    await u.message.reply_text("🔄 Повтор:", reply_markup=kb(K_REP))
    return AL_REP

async def al_crem_type(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    if u.message.text == "⏱ За N минут до":
        c.user_data["crt"] = "b"
        await u.message.reply_text("Сколько минут?", reply_markup=kb(K_X))
        return AL_CREM_VAL
    if u.message.text == "🕐 В точное время":
        c.user_data["crt"] = "e"
        await u.message.reply_text("Время (ЧЧ:ММ):", reply_markup=kb(K_X))
        return AL_CREM_VAL
    await u.message.reply_text("Выбери из кнопок", reply_markup=kb(K_CREM))
    return AL_CREM_TYPE

async def al_crem_val(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    if c.user_data.get("crt") == "b":
        try:
            m = int(u.message.text.strip())
            assert m > 0
            c.user_data["rem"] = f"За {m} мин"
        except (ValueError, AssertionError):
            await u.message.reply_text("Число больше 0", reply_markup=kb(K_X))
            return AL_CREM_VAL
    else:
        if not valid_time(u.message.text):
            await u.message.reply_text("Формат: ЧЧ:ММ", reply_markup=kb(K_X))
            return AL_CREM_VAL
        c.user_data["rem"] = f"В {u.message.text.strip()}"
    await u.message.reply_text("🔄 Повтор:", reply_markup=kb(K_REP))
    return AL_REP

async def al_rep(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    if u.message.text not in VALID_REP:
        await u.message.reply_text("Выбери из кнопок", reply_markup=kb(K_REP))
        return AL_REP
    uid = u.effective_user.id
    db.add_lesson(uid, c.user_data["day"], c.user_data["subj"], c.user_data["time"],
                  c.user_data["room"], c.user_data["teach"],
                  c.user_data.get("rem", "🚫 Не напоминать"), u.message.text)
    lesson = {"subject": c.user_data["subj"], "time": c.user_data["time"],
              "room": c.user_data["room"], "teacher": c.user_data["teach"],
              "reminder": c.user_data.get("rem", "🚫 Не напоминать"), "repeat": u.message.text}
    await u.message.reply_text(f"✅ Пара добавлена!\n\n📅 {c.user_data['day']}\n\n{fmt_lesson(lesson)}", reply_markup=kb(K_ML))
    c.user_data.clear()
    return ConversationHandler.END


# ═══════════ Удаление пары ═══════════

async def dl_start(u, c):
    uid = u.effective_user.id
    days = db.get_days_with_lessons(uid)
    if not days:
        await u.message.reply_text("У тебя пока нет пар", reply_markup=kb(K_ML))
        return ConversationHandler.END
    await u.message.reply_text("🗑 Из какого дня?", reply_markup=kb([[d] for d in days] + [["❌ Отмена"]]))
    return DL_DAY

async def dl_day(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    c.user_data["day"] = u.message.text
    uid = u.effective_user.id
    lessons = db.get_lessons_by_day(uid, u.message.text)
    if not lessons:
        await u.message.reply_text("Пар нет", reply_markup=kb(K_ML))
        return ConversationHandler.END
    rows = [[f"{le['id']}. {le['time']} — {le['subject']}"] for le in lessons] + [["❌ Отмена"]]
    await u.message.reply_text(f"Какую пару удалить из {u.message.text}?", reply_markup=kb(rows))
    return DL_PICK

async def dl_pick(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    try:
        lesson_id = int(u.message.text.split(".")[0])
        uid = u.effective_user.id
        removed = db.delete_lesson(uid, lesson_id)
        if removed:
            await u.message.reply_text(f"✅ Удалено: {removed['subject']} ({removed['time']})", reply_markup=kb(K_ML))
        else:
            await u.message.reply_text("Не найдено", reply_markup=kb(K_ML))
    except (ValueError, IndexError):
        await u.message.reply_text("Ошибка", reply_markup=kb(K_ML))
    c.user_data.clear()
    return ConversationHandler.END


# ═══════════ Редактирование пары ═══════════

async def el_start(u, c):
    uid = u.effective_user.id
    days = db.get_days_with_lessons(uid)
    if not days:
        await u.message.reply_text("У тебя пока нет пар", reply_markup=kb(K_ML))
        return ConversationHandler.END
    await u.message.reply_text("✏️ Из какого дня?", reply_markup=kb([[d] for d in days] + [["❌ Отмена"]]))
    return EL_DAY

async def el_day(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    c.user_data["day"] = u.message.text
    lessons = db.get_lessons_by_day(u.effective_user.id, u.message.text)
    rows = [[f"{le['id']}. {le['time']} — {le['subject']}"] for le in lessons] + [["❌ Отмена"]]
    await u.message.reply_text(f"Какую пару в {u.message.text}?", reply_markup=kb(rows))
    return EL_PICK

async def el_pick(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    try:
        c.user_data["lid"] = int(u.message.text.split(".")[0])
    except (ValueError, IndexError):
        return EL_PICK
    await u.message.reply_text("Что изменить?", reply_markup=kb([["📖 Предмет", "🕐 Время"], ["🏫 Аудитория", "👨‍🏫 Преподаватель"], ["❌ Отмена"]]))
    return EL_FIELD

async def el_field(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    fm = {"📖 Предмет": "subject", "🕐 Время": "time", "🏫 Аудитория": "room", "👨‍🏫 Преподаватель": "teacher"}
    f = fm.get(u.message.text)
    if not f:
        return EL_FIELD
    c.user_data["field"] = f
    pr = {"subject": "Новый предмет:", "time": "Новое время (ЧЧ:ММ):", "room": "Новая аудитория:", "teacher": "Новый преподаватель:"}
    await u.message.reply_text(pr[f], reply_markup=kb(K_X))
    return EL_VAL

async def el_val(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_ML))
        return ConversationHandler.END
    f, v = c.user_data["field"], u.message.text.strip()
    if f == "time" and not valid_time(v):
        await u.message.reply_text("Формат: ЧЧ:ММ", reply_markup=kb(K_X))
        return EL_VAL
    db.update_lesson_field(c.user_data["lid"], f, v)
    lesson = db.get_lesson_by_id(c.user_data["lid"])
    text = f"✅ Изменено!\n\n{fmt_lesson(lesson)}" if lesson else "✅ Изменено!"
    await u.message.reply_text(text, reply_markup=kb(K_ML))
    c.user_data.clear()
    return ConversationHandler.END


# ═══════════ Добавление задачи ═══════════

async def at_start(u, c):
    await u.message.reply_text("📝 Выбери категорию:", reply_markup=kb(kb_cats(u.effective_user.id)))
    return AT_CAT

async def at_cat(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    if u.message.text == "📌 Без категории":
        c.user_data["cn"], c.user_data["ce"] = "Без категории", "📌"
    else:
        parts = u.message.text.split(" ", 1)
        if len(parts) < 2:
            return AT_CAT
        c.user_data["ce"], c.user_data["cn"] = parts[0], parts[1]
    await u.message.reply_text(
        "Введи название и описание через дефис:\n\n"
        "Пример: Сдать курсовую - глава 2\n\n"
        "Если без описания — просто название", reply_markup=kb(K_X))
    return AT_INFO

async def at_info(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    parts = u.message.text.split("-", 1)
    c.user_data["title"] = parts[0].strip()
    c.user_data["desc"] = parts[1].strip() if len(parts) > 1 else ""
    await u.message.reply_text(
        "📅 Дата и время:\n\nПример: 20.06.2025 14:00\nИли только дата: 20.06.2025",
        reply_markup=kb(K_X))
    return AT_DT

async def at_dt(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    parts = u.message.text.strip().split()
    if not valid_date(parts[0]):
        await u.message.reply_text("❌ Формат: ДД.ММ.ГГГГ", reply_markup=kb(K_X))
        return AT_DT
    c.user_data["date"] = parts[0]
    c.user_data["ttime"] = parts[1].strip() if len(parts) > 1 and valid_time(parts[1]) else ""
    await u.message.reply_text("⏰ Напоминание:", reply_markup=kb(K_REM))
    return AT_REM

async def at_rem(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    if u.message.text == "⏰ Своё время":
        await u.message.reply_text("Как задать?", reply_markup=kb(K_CREM))
        return AT_CREM_TYPE
    if u.message.text not in VALID_REM:
        await u.message.reply_text("Выбери из кнопок", reply_markup=kb(K_REM))
        return AT_REM
    c.user_data["trem"] = u.message.text
    await u.message.reply_text("🔄 Повтор:", reply_markup=kb(K_REP))
    return AT_REP

async def at_crem_type(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    if u.message.text == "⏱ За N минут до":
        c.user_data["tcrt"] = "b"
        await u.message.reply_text("Сколько минут?", reply_markup=kb(K_X))
        return AT_CREM_VAL
    if u.message.text == "🕐 В точное время":
        c.user_data["tcrt"] = "e"
        await u.message.reply_text("Время (ЧЧ:ММ):", reply_markup=kb(K_X))
        return AT_CREM_VAL
    await u.message.reply_text("Выбери из кнопок", reply_markup=kb(K_CREM))
    return AT_CREM_TYPE

async def at_crem_val(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    if c.user_data.get("tcrt") == "b":
        try:
            m = int(u.message.text.strip())
            assert m > 0
            c.user_data["trem"] = f"За {m} мин"
        except (ValueError, AssertionError):
            await u.message.reply_text("Число больше 0", reply_markup=kb(K_X))
            return AT_CREM_VAL
    else:
        if not valid_time(u.message.text):
            await u.message.reply_text("Формат: ЧЧ:ММ", reply_markup=kb(K_X))
            return AT_CREM_VAL
        c.user_data["trem"] = f"В {u.message.text.strip()}"
    await u.message.reply_text("🔄 Повтор:", reply_markup=kb(K_REP))
    return AT_REP

async def at_rep(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    if u.message.text not in VALID_REP:
        await u.message.reply_text("Выбери из кнопок", reply_markup=kb(K_REP))
        return AT_REP
    uid = u.effective_user.id
    db.add_task(uid, c.user_data["title"], c.user_data["date"],
                c.user_data.get("desc", ""), c.user_data.get("ttime", ""),
                c.user_data["cn"], c.user_data["ce"],
                c.user_data.get("trem", "🚫 Не напоминать"), u.message.text)
    task = {"title": c.user_data["title"], "description": c.user_data.get("desc", ""),
            "date": c.user_data["date"], "time": c.user_data.get("ttime", ""),
            "cat_name": c.user_data["cn"], "cat_emoji": c.user_data["ce"],
            "reminder": c.user_data.get("trem", "🚫 Не напоминать"), "repeat": u.message.text}
    await u.message.reply_text(f"✅ Задача добавлена!\n\n{fmt_task(task)}", reply_markup=kb(K_MT))
    c.user_data.clear()
    return ConversationHandler.END


# ═══════════ Удаление задачи ═══════════

async def dt_start(u, c):
    tasks = db.get_all_tasks(u.effective_user.id)
    if not tasks:
        await u.message.reply_text("У тебя пока нет задач", reply_markup=kb(K_MT))
        return ConversationHandler.END
    rows = [[f"{ta['id']}. {ta.get('cat_emoji','📌')} {ta['title']}"] for ta in tasks] + [["❌ Отмена"]]
    await u.message.reply_text("🗑 Какую удалить?", reply_markup=kb(rows))
    return DT_PICK

async def dt_pick(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    try:
        task_id = int(u.message.text.split(".")[0])
        removed = db.delete_task(u.effective_user.id, task_id)
        if removed:
            await u.message.reply_text(f"✅ Удалено: {removed.get('cat_emoji','📌')} {removed['title']}", reply_markup=kb(K_MT))
        else:
            await u.message.reply_text("Не найдено", reply_markup=kb(K_MT))
    except (ValueError, IndexError):
        await u.message.reply_text("Ошибка", reply_markup=kb(K_MT))
    c.user_data.clear()
    return ConversationHandler.END


# ═══════════ Редактирование задачи ═══════════

async def et_start(u, c):
    tasks = db.get_all_tasks(u.effective_user.id)
    if not tasks:
        await u.message.reply_text("У тебя пока нет задач", reply_markup=kb(K_MT))
        return ConversationHandler.END
    rows = [[f"{ta['id']}. {ta.get('cat_emoji','📌')} {ta['title']}"] for ta in tasks] + [["❌ Отмена"]]
    await u.message.reply_text("✏️ Какую изменить?", reply_markup=kb(rows))
    return ET_PICK

async def et_pick(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    try:
        c.user_data["tid"] = int(u.message.text.split(".")[0])
    except (ValueError, IndexError):
        return ET_PICK
    await u.message.reply_text("Что изменить?", reply_markup=kb([["📝 Название", "💬 Описание"], ["📅 Дата", "🕐 Время"], ["❌ Отмена"]]))
    return ET_FIELD

async def et_field(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    fm = {"📝 Название": "title", "💬 Описание": "description", "📅 Дата": "date", "🕐 Время": "time"}
    f = fm.get(u.message.text)
    if not f:
        return ET_FIELD
    c.user_data["field"] = f
    pr = {"title": "Новое название:", "description": "Новое описание:", "date": "Новая дата (ДД.ММ.ГГГГ):", "time": "Новое время (ЧЧ:ММ):"}
    await u.message.reply_text(pr[f], reply_markup=kb(K_X))
    return ET_VAL

async def et_val(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MT))
        return ConversationHandler.END
    f, v = c.user_data["field"], u.message.text.strip()
    if f == "date" and not valid_date(v):
        await u.message.reply_text("Формат: ДД.ММ.ГГГГ", reply_markup=kb(K_X))
        return ET_VAL
    if f == "time" and v and not valid_time(v):
        await u.message.reply_text("Формат: ЧЧ:ММ", reply_markup=kb(K_X))
        return ET_VAL
    db.update_task_field(c.user_data["tid"], f, v)
    task = db.get_task_by_id(c.user_data["tid"])
    text = f"✅ Изменено!\n\n{fmt_task(task)}" if task else "✅ Изменено!"
    await u.message.reply_text(text, reply_markup=kb(K_MT))
    c.user_data.clear()
    return ConversationHandler.END


# ═══════════ Категории ═══════════

async def show_cats(u, c):
    cats = db.get_categories(u.effective_user.id)
    text = "📂 Мои категории\n\n"
    if not cats:
        text += "У тебя пока нет категорий"
    else:
        for cat in cats:
            text += f"{cat['id']}. {cat['emoji']} {cat['name']}\n"
    await u.message.reply_text(text, reply_markup=kb(K_MC))


async def ac_start(u, c):
    await u.message.reply_text("Отправь эмодзи:", reply_markup=kb(K_X))
    return AC_EMOJI

async def ac_emoji(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MC))
        return ConversationHandler.END
    c.user_data["ce"] = u.message.text.strip()
    await u.message.reply_text("Название категории:", reply_markup=kb(K_X))
    return AC_NAME

async def ac_name(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MC))
        return ConversationHandler.END
    db.add_category(u.effective_user.id, u.message.text.strip(), c.user_data["ce"])
    await u.message.reply_text(f"✅ Добавлено: {c.user_data['ce']} {u.message.text.strip()}", reply_markup=kb(K_MC))
    c.user_data.clear()
    return ConversationHandler.END


async def dc_start(u, c):
    cats = db.get_categories(u.effective_user.id)
    if not cats:
        await u.message.reply_text("Категорий нет", reply_markup=kb(K_MC))
        return ConversationHandler.END
    rows = [[f"{cat['id']}. {cat['emoji']} {cat['name']}"] for cat in cats] + [["❌ Отмена"]]
    await u.message.reply_text("🗑 Какую удалить?", reply_markup=kb(rows))
    return DC_PICK

async def dc_pick(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MC))
        return ConversationHandler.END
    try:
        cat_id = int(u.message.text.split(".")[0])
        removed = db.delete_category(u.effective_user.id, cat_id)
        if removed:
            await u.message.reply_text(f"✅ Удалено: {removed['emoji']} {removed['name']}", reply_markup=kb(K_MC))
        else:
            await u.message.reply_text("Ошибка", reply_markup=kb(K_MC))
    except (ValueError, IndexError):
        await u.message.reply_text("Ошибка", reply_markup=kb(K_MC))
    return ConversationHandler.END


async def ec_start(u, c):
    cats = db.get_categories(u.effective_user.id)
    if not cats:
        await u.message.reply_text("Категорий нет", reply_markup=kb(K_MC))
        return ConversationHandler.END
    rows = [[f"{cat['id']}. {cat['emoji']} {cat['name']}"] for cat in cats] + [["❌ Отмена"]]
    await u.message.reply_text("✏️ Какую изменить?", reply_markup=kb(rows))
    return EC_PICK

async def ec_pick(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MC))
        return ConversationHandler.END
    try:
        c.user_data["cid"] = int(u.message.text.split(".")[0])
    except (ValueError, IndexError):
        return EC_PICK
    await u.message.reply_text("Что изменить?", reply_markup=kb([["📝 Название", "😀 Эмодзи"], ["❌ Отмена"]]))
    return EC_FIELD

async def ec_field(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MC))
        return ConversationHandler.END
    if u.message.text == "📝 Название":
        c.user_data["cf"] = "name"
        await u.message.reply_text("Новое название:", reply_markup=kb(K_X))
    elif u.message.text == "😀 Эмодзи":
        c.user_data["cf"] = "emoji"
        await u.message.reply_text("Новый эмодзи:", reply_markup=kb(K_X))
    else:
        return EC_FIELD
    return EC_VAL

async def ec_val(u, c):
    if u.message.text == "❌ Отмена":
        await u.message.reply_text("Отменено", reply_markup=kb(K_MC))
        return ConversationHandler.END
    db.update_category_field(c.user_data["cid"], c.user_data["cf"], u.message.text.strip())
    cat = db.get_category_by_id(c.user_data["cid"])
    text = f"✅ Изменено: {cat['emoji']} {cat['name']}" if cat else "✅ Изменено!"
    await u.message.reply_text(text, reply_markup=kb(K_MC))
    c.user_data.clear()
    return ConversationHandler.END


# ═══════════ Напоминания ═══════════

async def show_rems(u, c):
    rems = db.get_all_reminders(u.effective_user.id)
    text = "⏰ Мои напоминания\n\n"
    if not rems:
        text += "У тебя пока нет напоминаний"
    else:
        for r in rems:
            if r["type"] == "lesson":
                text += f"📅 {r['day_name']}, {r['time']} — {r['subject']}\n⏰ {r['reminder']}\n\n"
            else:
                tp = f", {r['time']}" if r.get("time") else ""
                text += f"📅 {r.get('date', '—')}{tp} — {r.get('cat_emoji', '📌')} {r['title']}\n⏰ {r['reminder']}\n\n"
    await u.message.reply_text(text, reply_markup=kb(K_MNG))


# ═══════════ Неизвестный текст ═══════════

async def unknown(u, c):
    await u.message.reply_text("Используй кнопки меню или /start", reply_markup=kb(K_MAIN))


# ═══════════ Хелпер для диалогов ═══════════

def conv(pattern, start_fn, states_list):
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{pattern}$"), start_fn)],
        states={state: [MessageHandler(filters.TEXT & ~filters.COMMAND, fn)] for state, fn in states_list},
        fallbacks=[
            MessageHandler(filters.Regex("^❌ Отмена$"), cancel),
            CommandHandler("cancel", cancel),
        ],
    )


# ═══════════ Запуск ═══════════

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TOKEN_HERE":
        raise ValueError("Укажи BOT_TOKEN в .env")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))

    # Пары
    app.add_handler(conv("➕ Добавить пару", al_start, [
        (AL_DAY, al_day), (AL_INFO, al_info), (AL_REM, al_rem),
        (AL_CREM_TYPE, al_crem_type), (AL_CREM_VAL, al_crem_val), (AL_REP, al_rep)]))
    app.add_handler(conv("🗑 Удалить пару", dl_start, [(DL_DAY, dl_day), (DL_PICK, dl_pick)]))
    app.add_handler(conv("✏️ Изменить пару", el_start, [
        (EL_DAY, el_day), (EL_PICK, el_pick), (EL_FIELD, el_field), (EL_VAL, el_val)]))

    # Задачи
    app.add_handler(conv("➕ Добавить задачу", at_start, [
        (AT_CAT, at_cat), (AT_INFO, at_info), (AT_DT, at_dt), (AT_REM, at_rem),
        (AT_CREM_TYPE, at_crem_type), (AT_CREM_VAL, at_crem_val), (AT_REP, at_rep)]))
    app.add_handler(conv("🗑 Удалить задачу", dt_start, [(DT_PICK, dt_pick)]))
    app.add_handler(conv("✏️ Изменить задачу", et_start, [
        (ET_PICK, et_pick), (ET_FIELD, et_field), (ET_VAL, et_val)]))

    # Просмотр задач
    app.add_handler(conv("📅 Задачи на дату", vt_date_s, [(VT_DATE, vt_date)]))
    app.add_handler(conv("📅 Задачи за период", vt_period_s, [(VT_FROM, vt_from), (VT_TO, vt_to)]))
    app.add_handler(conv("📂 Задачи по категории", vt_cat_s, [(VT_CAT, vt_cat)]))

    # Календарь
    app.add_handler(conv("🗓 Календарь на дату", cal_date_s, [(CAL_DATE, cal_date)]))
    app.add_handler(conv("🗓 Календарь период", cal_period_s, [(CAL_FROM, cal_from), (CAL_TO, cal_to)]))

    # Категории
    app.add_handler(conv("➕ Добавить категорию", ac_start, [(AC_EMOJI, ac_emoji), (AC_NAME, ac_name)]))
    app.add_handler(conv("🗑 Удалить категорию", dc_start, [(DC_PICK, dc_pick)]))
    app.add_handler(conv("✏️ Изменить категорию", ec_start, [
        (EC_PICK, ec_pick), (EC_FIELD, ec_field), (EC_VAL, ec_val)]))

    # Навигация — ПОРЯДОК ВАЖЕН
    app.add_handler(MessageHandler(filters.Regex("^📝 Мои задачи$"), nav_tasks))
    app.add_handler(MessageHandler(filters.Regex("^📝 Управление задачами$"), nav_mt))
    app.add_handler(MessageHandler(filters.Regex("^📊 Мой день$"), my_day))
    app.add_handler(MessageHandler(filters.Regex("^📅 Расписание$"), nav_sched))
    app.add_handler(MessageHandler(filters.Regex("^📆 Полный календарь$"), nav_cal))
    app.add_handler(MessageHandler(filters.Regex("^🔧 Управление$"), nav_mng))
    app.add_handler(MessageHandler(filters.Regex("^📚 Управление парами$"), nav_ml))
    app.add_handler(MessageHandler(filters.Regex("^📂 Управление категориями$"), nav_mc))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Помощь$"), cmd_help))
    app.add_handler(MessageHandler(filters.Regex("^🔙 Меню$"), nav_main))
    app.add_handler(MessageHandler(filters.Regex("^🔙 К управлению$"), nav_mng))

    # Просмотры
    app.add_handler(MessageHandler(filters.Regex("^📅 Сегодня$"), sched_today))
    app.add_handler(MessageHandler(filters.Regex("^📅 Завтра$"), sched_tmr))
    app.add_handler(MessageHandler(filters.Regex("^📋 Неделя$"), sched_week))
    app.add_handler(MessageHandler(filters.Regex("^📆 Месяц$"), sched_month))
    app.add_handler(MessageHandler(filters.Regex("^📋 Все задачи$"), view_tasks_all))
    app.add_handler(MessageHandler(filters.Regex("^📋 Мои категории$"), show_cats))
    app.add_handler(MessageHandler(filters.Regex("^⏰ Напоминания$"), show_rems))
    app.add_handler(MessageHandler(filters.Regex("^🗓 Календарь завтра$"), cal_tmr))
    app.add_handler(MessageHandler(filters.Regex("^🗓 Календарь неделя$"), cal_week))
    app.add_handler(MessageHandler(filters.Regex("^🗓 Календарь месяц$"), cal_month))

    # Неизвестный текст — последний
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))

    logger.info("Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
