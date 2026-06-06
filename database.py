# 2) `database.py`

Полностью замени содержимое `database.py` на это:

```python
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

DB_FILE = "timetable.db"


class Database:
    """Класс для работы с базой данных"""

    def __init__(self):
        self.db_file = DB_FILE
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def _date_expr(self, field_name: str = "date") -> str:
        """
        Преобразование даты из ДД.ММ.ГГГГ в YYYY-MM-DD для корректной сортировки и сравнения в SQLite.
        """
        return f"substr({field_name}, 7, 4) || '-' || substr({field_name}, 4, 2) || '-' || substr({field_name}, 1, 2)"

    def _to_iso(self, date_str: str) -> str:
        return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                day_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                time TEXT NOT NULL,
                room TEXT DEFAULT '',
                teacher TEXT DEFAULT '',
                reminder TEXT DEFAULT '🚫 Не напоминать',
                repeat TEXT DEFAULT '🚫 Без повтора',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                date TEXT NOT NULL,
                time TEXT DEFAULT '',
                cat_name TEXT DEFAULT 'Без категории',
                cat_emoji TEXT DEFAULT '📌',
                reminder TEXT DEFAULT '🚫 Не напоминать',
                repeat TEXT DEFAULT '🚫 Без повтора',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                emoji TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def _ensure_default_categories(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM categories WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()["cnt"]

        if count == 0:
            defaults = [
                ("Учёба", "📖"),
                ("Работа", "💼"),
                ("Спорт", "🏋️"),
                ("Личное", "🎯"),
                ("Здоровье", "🩺"),
                ("Курсовая/Диплом", "🎓"),
            ]
            for name, emoji in defaults:
                cursor.execute(
                    "INSERT INTO categories (user_id, name, emoji) VALUES (?, ?, ?)",
                    (user_id, name, emoji),
                )
            conn.commit()

        conn.close()

    # ==================== ПАРЫ ====================

    def add_lesson(
        self,
        user_id: int,
        day_name: str,
        subject: str,
        time: str,
        room: str = "",
        teacher: str = "",
        reminder: str = "🚫 Не напоминать",
        repeat: str = "🚫 Без повтора",
    ) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lessons (user_id, day_name, subject, time, room, teacher, reminder, repeat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, day_name, subject, time, room, teacher, reminder, repeat))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка добавления пары: {e}")
            return False

    def get_lessons_by_day(self, user_id: int, day_name: str) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, day_name, subject, time, room, teacher, reminder, repeat
            FROM lessons
            WHERE user_id = ? AND day_name = ?
            ORDER BY time
        """, (user_id, day_name))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_all_lessons(self, user_id: int) -> Dict[str, List[Dict]]:
        result = {}
        days = [
            "Понедельник", "Вторник", "Среда", "Четверг",
            "Пятница", "Суббота", "Воскресенье"
        ]
        for day in days:
            lessons = self.get_lessons_by_day(user_id, day)
            if lessons:
                result[day] = lessons
        return result

    def get_days_with_lessons(self, user_id: int) -> List[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT day_name FROM lessons
            WHERE user_id = ?
            ORDER BY CASE day_name
                WHEN 'Понедельник' THEN 1
                WHEN 'Вторник' THEN 2
                WHEN 'Среда' THEN 3
                WHEN 'Четверг' THEN 4
                WHEN 'Пятница' THEN 5
                WHEN 'Суббота' THEN 6
                WHEN 'Воскресенье' THEN 7
            END
        """, (user_id,))
        result = [row["day_name"] for row in cursor.fetchall()]
        conn.close()
        return result

    def delete_lesson(self, user_id: int, lesson_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, subject, time
            FROM lessons
            WHERE id = ? AND user_id = ?
        """, (lesson_id, user_id))
        row = cursor.fetchone()

        if row:
            result = dict(row)
            cursor.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
            conn.commit()
            conn.close()
            return result

        conn.close()
        return None

    def update_lesson_field(self, lesson_id: int, field: str, value: str) -> bool:
        allowed = {"subject", "time", "room", "teacher", "reminder", "repeat"}
        if field not in allowed:
            return False

        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"UPDATE lessons SET {field} = ? WHERE id = ?", (value, lesson_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка обновления пары: {e}")
            return False

    def get_lesson_by_id(self, lesson_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, day_name, subject, time, room, teacher, reminder, repeat
            FROM lessons
            WHERE id = ?
        """, (lesson_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ==================== ЗАДАЧИ ====================

    def add_task(
        self,
        user_id: int,
        title: str,
        date: str,
        description: str = "",
        time: str = "",
        cat_name: str = "Без категории",
        cat_emoji: str = "📌",
        reminder: str = "🚫 Не напоминать",
        repeat: str = "🚫 Без повтора",
    ) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (
                    user_id, title, description, date, time,
                    cat_name, cat_emoji, reminder, repeat
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, title, description, date, time,
                cat_name, cat_emoji, reminder, repeat
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка добавления задачи: {e}")
            return False

    def get_all_tasks(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, title, description, date, time,
                   cat_name, cat_emoji, reminder, repeat
            FROM tasks
            WHERE user_id = ?
            ORDER BY {self._date_expr('date')}, time
        """, (user_id,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_tasks_by_date(self, user_id: int, date: str) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description, date, time,
                   cat_name, cat_emoji, reminder, repeat
            FROM tasks
            WHERE user_id = ? AND date = ?
            ORDER BY time
        """, (user_id, date))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_tasks_by_date_range(self, user_id: int, start_date: str, end_date: str) -> List[Dict]:
        start_iso = self._to_iso(start_date)
        end_iso = self._to_iso(end_date)

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, title, description, date, time,
                   cat_name, cat_emoji, reminder, repeat
            FROM tasks
            WHERE user_id = ?
              AND {self._date_expr('date')} >= ?
              AND {self._date_expr('date')} <= ?
            ORDER BY {self._date_expr('date')}, time
        """, (user_id, start_iso, end_iso))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_tasks_by_category(self, user_id: int, cat_name: str, cat_emoji: str) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, title, description, date, time,
                   cat_name, cat_emoji, reminder, repeat
            FROM tasks
            WHERE user_id = ? AND cat_name = ? AND cat_emoji = ?
            ORDER BY {self._date_expr('date')}, time
        """, (user_id, cat_name, cat_emoji))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def delete_task(self, user_id: int, task_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, cat_emoji
            FROM tasks
            WHERE id = ? AND user_id = ?
        """, (task_id, user_id))
        row = cursor.fetchone()

        if row:
            result = dict(row)
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            conn.close()
            return result

        conn.close()
        return None

    def update_task_field(self, task_id: int, field: str, value: str) -> bool:
        allowed = {
            "title", "description", "date", "time",
            "cat_name", "cat_emoji", "reminder", "repeat"
        }
        if field not in allowed:
            return False

        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"UPDATE tasks SET {field} = ? WHERE id = ?", (value, task_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка обновления задачи: {e}")
            return False

    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description, date, time,
                   cat_name, cat_emoji, reminder, repeat
            FROM tasks
            WHERE id = ?
        """, (task_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ==================== КАТЕГОРИИ ====================

    def get_categories(self, user_id: int) -> List[Dict]:
        self._ensure_default_categories(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, emoji
            FROM categories
            WHERE user_id = ?
            ORDER BY id
        """, (user_id,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def add_category(self, user_id: int, name: str, emoji: str) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO categories (user_id, name, emoji) VALUES (?, ?, ?)",
                (user_id, name, emoji),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка добавления категории: {e}")
            return False

    def delete_category(self, user_id: int, cat_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, emoji
            FROM categories
            WHERE id = ? AND user_id = ?
        """, (cat_id, user_id))
        row = cursor.fetchone()

        if row:
            category = dict(row)

            # Все задачи этой категории переводим в "Без категории"
            cursor.execute("""
                UPDATE tasks
                SET cat_name = 'Без категории', cat_emoji = '📌'
                WHERE user_id = ? AND cat_name = ? AND cat_emoji = ?
            """, (user_id, category["name"], category["emoji"]))

            cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
            conn.commit()
            conn.close()
            return category

        conn.close()
        return None

    def update_category_field(self, cat_id: int, field: str, value: str) -> bool:
        allowed = {"name", "emoji"}
        if field not in allowed:
            return False

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, user_id, name, emoji FROM categories WHERE id = ?", (cat_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False

            old = dict(row)
            old_name = old["name"]
            old_emoji = old["emoji"]
            user_id = old["user_id"]

            cursor.execute(f"UPDATE categories SET {field} = ? WHERE id = ?", (value, cat_id))

            new_name = value if field == "name" else old_name
            new_emoji = value if field == "emoji" else old_emoji

            # Обновляем задачи, которые были привязаны к этой категории
            cursor.execute("""
                UPDATE tasks
                SET cat_name = ?, cat_emoji = ?
                WHERE user_id = ? AND cat_name = ? AND cat_emoji = ?
            """, (new_name, new_emoji, user_id, old_name, old_emoji))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка обновления категории: {e}")
            return False

    def get_category_by_id(self, cat_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, emoji FROM categories WHERE id = ?", (cat_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ==================== НАПОМИНАНИЯ ====================

    def get_all_reminders(self, user_id: int) -> List[Dict]:
        result = []
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT day_name, time, subject, reminder
            FROM lessons
            WHERE user_id = ? AND reminder != '🚫 Не напоминать'
            ORDER BY day_name, time
        """, (user_id,))
        for row in cursor.fetchall():
            result.append({
                "type": "lesson",
                "day_name": row["day_name"],
                "time": row["time"],
                "subject": row["subject"],
                "reminder": row["reminder"],
            })

        cursor.execute(f"""
            SELECT title, date, time, cat_emoji, reminder
            FROM tasks
            WHERE user_id = ? AND reminder != '🚫 Не напоминать'
            ORDER BY {self._date_expr('date')}, time
        """, (user_id,))
        for row in cursor.fetchall():
            result.append({
                "type": "task",
                "title": row["title"],
                "date": row["date"],
                "time": row["time"],
                "cat_emoji": row["cat_emoji"],
                "reminder": row["reminder"],
            })

        conn.close()
        return result


# Глобальный экземпляр БД
db = Database()
