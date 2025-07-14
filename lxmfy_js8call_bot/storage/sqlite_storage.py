"""SQLite storage backend for the JS8Call LXMF bot."""

import ast
import json
import logging
import sqlite3
import threading
from typing import Any

from lxmfy.storage import StorageBackend


class SQLiteStorage(StorageBackend):
    """SQLite implementation of the StorageBackend interface."""

    def __init__(self, db_file: str):
        """Initialize SQLite storage.

        Args:
            db_file: Path to the SQLite database file
        """
        self.db_file = db_file
        self.db_lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.setup_database()

    def setup_database(self):
        """Initialize database connection and create tables."""
        with self.db_lock:
            self.db_conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.create_tables()

    def create_tables(self):
        """Create necessary database tables if they don't exist."""
        with self.db_conn:
            self.db_conn.executescript(
                """
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
            """
            )

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from storage.

        Args:
            key: The key to retrieve
            default: Value to return if key doesn't exist

        Returns:
            The stored value or default if not found
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("SELECT value FROM storage WHERE key = ?", (key,))
                result = cursor.fetchone()
                if result:
                    try:
                        return json.loads(result[0])
                    except json.JSONDecodeError:
                        self.logger.warning("Could not decode JSON for key %s, attempting literal_eval.", key)
                        try:
                            return ast.literal_eval(result[0])
                        except (ValueError, SyntaxError):
                            self.logger.error("Could not literal_eval for key %s, returning raw string.", key)
                            return result[0]
                return default
            except Exception as e:
                self.logger.error("Error getting key %s: %s", key, e)
                return default
            finally:
                cursor.close()

    def set(self, key: str, value: Any) -> None:
        """Store a value in storage.

        Args:
            key: The key to store
            value: The value to store
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO storage (key, value) VALUES (?, ?)",
                    (key, json.dumps(value)),
                )
                self.db_conn.commit()
            except Exception as e:
                self.logger.error("Error setting key %s: %s", key, e)
                raise
            finally:
                cursor.close()

    def delete(self, key: str) -> None:
        """Delete a value from storage.

        Args:
            key: The key to delete
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("DELETE FROM storage WHERE key = ?", (key,))
                self.db_conn.commit()
            except Exception as e:
                self.logger.error("Error deleting key %s: %s", key, e)
                raise
            finally:
                cursor.close()

    def exists(self, key: str) -> bool:
        """Check if a key exists in storage.

        Args:
            key: The key to check

        Returns:
            True if key exists, False otherwise
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("SELECT 1 FROM storage WHERE key = ?", (key,))
                return cursor.fetchone() is not None
            finally:
                cursor.close()

    def scan(self, prefix: str) -> list:
        """Scan for keys with a given prefix.

        Args:
            prefix: The prefix to search for

        Returns:
            List of matching keys
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute(
                    "SELECT key FROM storage WHERE key LIKE ?", (f"{prefix}%",)
                )
                return [row[0] for row in cursor.fetchall()]
            finally:
                cursor.close()

    def insert_message(self, sender: str, receiver: str, message: str) -> None:
        """Insert a new message into the database.

        Args:
            sender: Message sender
            receiver: Message receiver
            message: Message content
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
                    (sender, receiver, message),
                )
                self.db_conn.commit()
            finally:
                cursor.close()

    def get_unprocessed_messages(self) -> list:
        """Retrieve all unprocessed messages.

        Returns:
            List of unprocessed messages
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("SELECT * FROM messages WHERE processed = 0")
                return cursor.fetchall()
            finally:
                cursor.close()

    def mark_message_processed(self, message_id: int) -> None:
        """Mark a message as processed.

        Args:
            message_id: ID of the message to mark
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute(
                    "UPDATE messages SET processed = 1 WHERE id = ?", (message_id,)
                )
                self.db_conn.commit()
            finally:
                cursor.close()

    def cleanup(self):
        """Close database connection and cleanup resources."""
        if hasattr(self, "db_conn"):
            self.db_conn.close()

    def get_users(self) -> list:
        """Get all users from the database.

        Returns:
            List of user records
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("SELECT * FROM users")
                return cursor.fetchall()
            finally:
                cursor.close()

    def save_user(self, user_hash: str, groups: str, muted_groups: str) -> None:
        """Save or update a user in the database.

        Args:
            user_hash: User's unique hash
            groups: User's subscribed groups
            muted_groups: User's muted groups
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO users (user_hash, groups, muted_groups)
                    VALUES (?, ?, ?)
                    """,
                    (user_hash, groups, muted_groups),
                )
                self.db_conn.commit()
            finally:
                cursor.close()

    def remove_user(self, user_hash: str) -> None:
        """Remove a user from the database.

        Args:
            user_hash: Hash of the user to remove
        """
        with self.db_lock:
            cursor = self.db_conn.cursor()
            try:
                cursor.execute("DELETE FROM users WHERE user_hash = ?", (user_hash,))
                self.db_conn.commit()
            finally:
                cursor.close()
