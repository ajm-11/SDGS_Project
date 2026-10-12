import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path="sdgs_database.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # جدول القواعد
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Lifecycle_Rules (
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                extension TEXT NOT NULL,
                min_size REAL DEFAULT 0,
                max_age_days INTEGER DEFAULT 0,
                action TEXT NOT NULL,
                priority INTEGER DEFAULT 1
            )
        """)

        # جدول الملفات المحمية
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Protected_Files (
                file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL
            )
        """)

        # جدول السجلات (مع أعمدة الحجز المطلوبة للمحرك)[cite: 3]
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Activity_Logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_taken TEXT NOT NULL,
                file_name TEXT,
                original_path TEXT,
                quarantine_id TEXT,
                stored_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول المجلدات المراقبة[cite: 3]
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Monitored_Directories (
                dir_id INTEGER PRIMARY KEY AUTOINCREMENT,
                dir_path TEXT UNIQUE NOT NULL,
                exclude_flag INTEGER DEFAULT 0
            )
        """)

        # جدول الإعدادات[cite: 3]
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        conn.close()

    # --- دوال الإعدادات (Settings)[cite: 2, 3] ---
    def get_setting(self, key):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM Settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row["value"] if row else None

    def set_setting(self, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO Settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()

    # --- دوال القواعد (Rules)[cite: 2] ---
    def insert_rule(self, name, extension, min_size=0, max_age_days=0, action="Quarantine", priority=1):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Lifecycle_Rules (name, extension, min_size, max_age_days, action, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, extension, min_size, max_age_days, action, priority))
        conn.commit()
        conn.close()

    def get_all_rules(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT rule_id, name, extension, min_size, max_age_days, action, priority FROM Lifecycle_Rules")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_rule(self, rule_id, name, extension, min_size, max_age_days, action, priority):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Lifecycle_Rules 
            SET name=?, extension=?, min_size=?, max_age_days=?, action=?, priority=?
            WHERE rule_id=?
        """, (name, extension, min_size, max_age_days, action, priority, rule_id))
        conn.commit()
        conn.close()

    def delete_rule(self, rule_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Lifecycle_Rules WHERE rule_id = ?", (rule_id,))
        conn.commit()
        conn.close()

    # --- دوال المجلدات المراقبة (Monitored Directories)[cite: 3] ---
    def add_monitored_directory(self, dir_path, exclude_flag=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Monitored_Directories (dir_path, exclude_flag) VALUES (?, ?)", (dir_path, exclude_flag))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()

    def remove_monitored_directory(self, dir_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Monitored_Directories WHERE dir_path = ?", (dir_path,))
        conn.commit()
        conn.close()

    def get_monitored_directories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT dir_path FROM Monitored_Directories")
        rows = cursor.fetchall()
        conn.close()
        return [row["dir_path"] for row in rows]

    # --- دوال الملفات المحمية (Protected Files)[cite: 2] ---
    def add_protected_file(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Protected_Files (file_path) VALUES (?)", (file_path,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()

    def remove_protected_file(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Protected_Files WHERE file_path = ?", (file_path,))
        conn.commit()
        conn.close()

    def is_file_protected(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Protected_Files WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def get_protected_files(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM Protected_Files")
        rows = cursor.fetchall()
        conn.close()
        return [row["file_path"] for row in rows]

    # --- دوال السجلات (Activity Logs)[cite: 2, 3] ---
    def log_action(self, action_taken, file_name="", original_path="", quarantine_id=None, stored_path=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Activity_Logs (action_taken, file_name, original_path, quarantine_id, stored_path)
            VALUES (?, ?, ?, ?, ?)
        """, (action_taken, file_name, original_path, quarantine_id, stored_path))
        conn.commit()
        conn.close()

    def get_logs(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT log_id, action_taken, file_name, original_path, quarantine_id, stored_path, timestamp FROM Activity_Logs ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_quarantine_logs(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT log_id, quarantine_id, action_taken, original_path, stored_path, timestamp FROM Activity_Logs WHERE quarantine_id IS NOT NULL ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]