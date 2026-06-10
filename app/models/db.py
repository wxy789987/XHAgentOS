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
            conn.execute("ALTER TABLE users ADD COLUMN role_id INTEGER DEFAULT 2")
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
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                model_name TEXT NOT NULL,
                base_url TEXT NOT NULL DEFAULT '',
                api_key TEXT NOT NULL DEFAULT '',
                max_tokens INTEGER DEFAULT 4096,
                temperature REAL DEFAULT 0.7,
                is_active INTEGER DEFAULT 1,
                is_default INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                update_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS model_chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS lookout_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url_template TEXT NOT NULL DEFAULT '',
                headers TEXT NOT NULL DEFAULT '{}',
                item_selector TEXT DEFAULT '',
                title_selector TEXT DEFAULT '',
                url_selector TEXT DEFAULT '',
                summary_selector TEXT DEFAULT '',
                time_selector TEXT DEFAULT '',
                page_param TEXT DEFAULT 'pn',
                page_size INTEGER DEFAULT 10,
                is_active INTEGER DEFAULT 1,
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                update_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS lookout_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                summary TEXT DEFAULT '',
                content TEXT DEFAULT '',
                publish_time TEXT DEFAULT '',
                keywords TEXT DEFAULT '',
                status TEXT DEFAULT 'collected',
                deep_status TEXT DEFAULT 'pending',
                deep_record_id INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS lookout_deep_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL UNIQUE,
                source_id INTEGER NOT NULL,
                url TEXT NOT NULL DEFAULT '',
                raw_content TEXT DEFAULT '',
                ai_summary TEXT DEFAULT '',
                ai_keywords TEXT DEFAULT '',
                ai_analysis TEXT DEFAULT '',
                ai_features TEXT DEFAULT '',
                ai_anomalies TEXT DEFAULT '',
                ai_relations TEXT DEFAULT '',
                ai_distribution TEXT DEFAULT '',
                content_length INTEGER DEFAULT 0,
                crawl_status TEXT DEFAULT 'pending',
                ai_status TEXT DEFAULT 'pending',
                error_message TEXT DEFAULT '',
                crawl_time TEXT DEFAULT '',
                ai_process_time TEXT DEFAULT '',
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                update_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                skill_type TEXT NOT NULL DEFAULT 'api',
                category TEXT DEFAULT '',
                config TEXT DEFAULT '{}',
                parameters TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                update_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS skill_call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id INTEGER NOT NULL,
                input_data TEXT DEFAULT '{}',
                output_data TEXT DEFAULT '{}',
                status TEXT DEFAULT 'running',
                duration_ms INTEGER DEFAULT 0,
                error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS digital_employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                model_id INTEGER NOT NULL DEFAULT 0,
                skill_ids TEXT DEFAULT '[]',
                description TEXT DEFAULT '',
                system_prompt TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                update_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS employee_call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                input_data TEXT DEFAULT '{}',
                output_data TEXT DEFAULT '{}',
                status TEXT DEFAULT 'running',
                duration_ms INTEGER DEFAULT 0,
                error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT '',
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                message_count INTEGER DEFAULT 0,
                created_by INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                update_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                content TEXT NOT NULL DEFAULT '',
                sentiment TEXT DEFAULT '',
                topic TEXT DEFAULT '',
                entities TEXT DEFAULT '[]',
                violation_flag INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS violation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL DEFAULT 0,
                violation_type TEXT NOT NULL DEFAULT '',
                violation_content TEXT DEFAULT '',
                matched_keyword TEXT DEFAULT '',
                severity TEXT DEFAULT 'low',
                status TEXT DEFAULT 'pending',
                create_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS dialogues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                description TEXT DEFAULT '',
                model_id INTEGER DEFAULT 0,
                system_prompt TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                update_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS dialogue_call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dialogue_id INTEGER NOT NULL,
                input_data TEXT DEFAULT '{}',
                output_data TEXT DEFAULT '{}',
                status TEXT DEFAULT 'running',
                duration_ms INTEGER DEFAULT 0,
                error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS datascreens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '',
                description TEXT DEFAULT '',
                screen_type TEXT DEFAULT 'chart',
                chart_config TEXT DEFAULT '{}',
                raw_data TEXT DEFAULT '[]',
                data_source TEXT DEFAULT 'manual',
                layout_config TEXT DEFAULT '{}',
                is_active INTEGER DEFAULT 1,
                created_by INTEGER DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                update_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS datascreen_call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datascreen_id INTEGER NOT NULL,
                action TEXT DEFAULT 'view',
                detail TEXT DEFAULT '{}',
                status TEXT DEFAULT 'success',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        # 用户侧对话功能 - 好友表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_id INTEGER NOT NULL,
                status TEXT DEFAULT 'accepted',
                remark TEXT DEFAULT '',
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, friend_id)
            )
        ''')
        # 用户侧对话功能 - 群组表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                owner_id INTEGER NOT NULL,
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                update_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        # 用户侧对话功能 - 群组成员表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(group_id, user_id)
            )
        ''')
        # 用户侧对话功能 - 好友请求表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                message TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                update_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        # 用户侧对话功能 - 群组消息表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                msg_type TEXT DEFAULT 'text',
                create_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        # 用户侧对话功能 - 群组数字员工表
        conn.execute('''
            CREATE TABLE IF NOT EXISTS group_employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                added_by INTEGER NOT NULL DEFAULT 0,
                create_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(group_id, employee_id)
            )
        ''')