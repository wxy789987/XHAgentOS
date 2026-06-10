# 数据库连接与建表
import os
import sqlite3

def _project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

DB_PATH = os.path.join(_project_root(), "database", "app.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                create_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        # 数据库迁移：为已有 users 表添加 role_id 列（若不存在）
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role_id INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass  # 列已存在则忽略
        conn.execute('''
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                icon TEXT DEFAULT '',
                parent_id INTEGER DEFAULT 0,
                url TEXT DEFAULT '',
                sort INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                create_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                is_system INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                feature_id INTEGER NOT NULL,
                UNIQUE(role_id, feature_id)
            )
        ''')