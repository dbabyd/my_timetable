import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional

DB_FILE = 'timetable.db'

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        """Инициализация БД"""
        self.db_file = DB_FILE
        self.init_db()
    
    def get_connection(self):
        """Получить подключение к БД"""
        return sqlite3.connect(self.db_file)
    
    def init_db(self):
        """Создать таблицы если их нет"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пар
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                classroom TEXT,
                teacher TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица задач
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== ПАРЫ ====================
    
    def add_class(self, user_id: int, name: str, date: str, start_time: str, 
                  end_time: str = None, classroom: str = None, teacher: str = None) -> bool:
        """Добавить пару"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO classes (user_id, name, date, start_time, end_time, classroom, teacher)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, date, start_time, end_time, classroom, teacher))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f'Ошибка при добавлении пары: {e}')
            return False
    
    def get_classes(self, user_id: int) -> List[Dict]:
        """Получить все пары пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, date, start_time, end_time, classroom, teacher
                FROM classes
                WHERE user_id = ?
                ORDER BY date, start_time
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            classes = []
            for row in rows:
                classes.append({
                    'id': row[0],
                    'name': row[1],
                    'date': row[2],
                    'start_time': row[3],
                    'end_time': row[4],
                    'classroom': row[5],
                    'teacher': row[6]
                })
            
            return classes
        except Exception as e:
            print(f'Ошибка при получении пар: {e}')
            return []
    
    def get_classes_by_date(self, user_id: int, date: str) -> List[Dict]:
        """Получить пары на конкретную дату"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, date, start_time, end_time, classroom, teacher
                FROM classes
                WHERE user_id = ? AND date = ?
                ORDER BY start_time
            ''', (user_id, date))
            
            rows = cursor.fetchall()
            conn.close()
            
            classes = []
            for row in rows:
                classes.append({
                    'id': row[0],
                    'name': row[1],
                    'date': row[2],
                    'start_time': row[3],
                    'end_time': row[4],
                    'classroom': row[5],
                    'teacher': row[6]
                })
            
            return classes
        except Exception as e:
            print(f'Ошибка при получении пар: {e}')
            return []
    
    def delete_class(self, user_id: int, class_id: int) -> bool:
        """Удалить пару по ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM classes WHERE id = ? AND user_id = ?', (class_id, user_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f'Ошибка при удалении пары: {e}')
            return False
    
    def delete_class_by_name(self, user_id: int, name: str) -> bool:
        """Удалить пару по названию"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM classes WHERE user_id = ? AND name = ?', (user_id, name))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f'Ошибка при удалении пары: {e}')
            return False
    
    # ==================== ЗАДАЧИ ====================
    
    def add_task(self, user_id: int, name: str, date: str, status: str, category: str = None) -> bool:
        """Добавить задачу"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tasks (user_id, name, date, status, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, date, status, category))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f'Ошибка при добавлении задачи: {e}')
            return False
    
    def get_tasks(self, user_id: int) -> List[Dict]:
        """Получить все задачи пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, date, status, category
                FROM tasks
                WHERE user_id = ?
                ORDER BY date
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                tasks.append({
                    'id': row[0],
                    'name': row[1],
                    'date': row[2],
                    'status': row[3],
                    'category': row[4]
                })
            
            return tasks
        except Exception as e:
            print(f'Ошибка при получении задач: {e}')
            return []
    
    def get_tasks_by_date(self, user_id: int, date: str) -> List[Dict]:
        """Получить задачи на конкретную дату"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, date, status, category
                FROM tasks
                WHERE user_id = ? AND date = ?
                ORDER BY date
            ''', (user_id, date))
            
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                tasks.append({
                    'id': row[0],
                    'name': row[1],
                    'date': row[2],
                    'status': row[3],
                    'category': row[4]
                })
            
            return tasks
        except Exception as e:
            print(f'Ошибка при получении задач: {e}')
            return []
    
    def delete_task(self, user_id: int, task_id: int) -> bool:
        """Удалить задачу по ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f'Ошибка при удалении задачи: {e}')
            return False
    
    def delete_task_by_name(self, user_id: int, name: str) -> bool:
        """Удалить задачу по названию"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM tasks WHERE user_id = ? AND name = ?', (user_id, name))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f'Ошибка при удалении задачи: {e}')
            return False

# Глобальный э��земпляр БД
db = Database()
