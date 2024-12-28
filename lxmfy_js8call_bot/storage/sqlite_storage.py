from lxmfy.storage import StorageBackend
import sqlite3
import threading
import logging
from typing import Any, Optional
from datetime import datetime

class SQLiteStorage(StorageBackend):
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.db_lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.setup_database()

    def setup_database(self):
        with self.db_lock:
            self.db_conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.create_tables()

    def create_tables(self):
        with self.db_conn:
            self.db_conn.executescript('''
                CREATE TABLE IF NOT EXISTS storage (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    receiver TEXT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    groupname TEXT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS urgent (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    groupname TEXT,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processed INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_hash TEXT UNIQUE,
                    groups TEXT,
                    muted_groups TEXT
                );
                
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    user_count INTEGER
                );
            ''')

    def get(self, key: str, default: Any = None) -> Any:
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("SELECT value FROM storage WHERE key = ?", (key,))
                result = cursor.fetchone()
                return result[0] if result else default
            except Exception as e:
                self.logger.error(f"Error getting key {key}: {e}")
                return default
            finally:
                cursor.close()

    def set(self, key: str, value: Any) -> None:
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO storage (key, value) VALUES (?, ?)",
                    (key, str(value))
                )
                self.db_conn.commit()
            except Exception as e:
                self.logger.error(f"Error setting key {key}: {e}")
                raise
            finally:
                cursor.close()

    def delete(self, key: str) -> None:
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("DELETE FROM storage WHERE key = ?", (key,))
                self.db_conn.commit()
            except Exception as e:
                self.logger.error(f"Error deleting key {key}: {e}")
                raise
            finally:
                cursor.close()

    def exists(self, key: str) -> bool:
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("SELECT 1 FROM storage WHERE key = ?", (key,))
                return cursor.fetchone() is not None
            finally:
                cursor.close()

    def scan(self, prefix: str) -> list:
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("SELECT key FROM storage WHERE key LIKE ?", (f"{prefix}%",))
                return [row[0] for row in cursor.fetchall()]
            finally:
                cursor.close()

    # JS8Call specific methods
    def insert_message(self, sender: str, receiver: str, message: str) -> None:
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
                    (sender, receiver, message)
                )
                self.db_conn.commit()
            finally:
                cursor.close()

    def get_unprocessed_messages(self) -> list:
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("SELECT * FROM messages WHERE processed = 0")
                return cursor.fetchall()
            finally:
                cursor.close()

    def mark_message_processed(self, message_id: int) -> None:
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute(
                    "UPDATE messages SET processed = 1 WHERE id = ?",
                    (message_id,)
                )
                self.db_conn.commit()
            finally:
                cursor.close()

    def cleanup(self):
        if hasattr(self, 'db_conn'):
            self.db_conn.close()

    def get_users(self):
        """Get all users from the database"""
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("SELECT * FROM users")
                return cursor.fetchall()
            finally:
                cursor.close()

    def save_user(self, user_hash: str, groups: str, muted_groups: str):
        """Save or update a user in the database"""
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO users (user_hash, groups, muted_groups)
                    VALUES (?, ?, ?)
                    """,
                    (user_hash, groups, muted_groups)
                )
                self.db_conn.commit()
            finally:
                cursor.close()

    def remove_user(self, user_hash: str):
        """Remove a user from the database"""
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("DELETE FROM users WHERE user_hash = ?", (user_hash,))
                self.db_conn.commit()
            finally:
                cursor.close() 