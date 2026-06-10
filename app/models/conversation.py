# 会话管理数据访问层
import json
from app.models.db import get_connection


class ConversationRepository:
    @staticmethod
    def get_page(page=1, page_size=10, keyword="", status=""):
        """分页获取会话"""
        with get_connection() as conn:
            conditions = []
            params = []
            if keyword:
                conditions.append("(title LIKE ? OR description LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if status:
                conditions.append("status=?")
                params.append(status)
            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            total = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM conversations {where}", params
            ).fetchone()["cnt"]
            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM conversations {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def get_by_id(conversation_id):
        """根据ID获取会话"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(title, description="", created_by=0):
        """新增会话"""
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO conversations (title, description, created_by) VALUES (?, ?, ?)",
                (title, description, created_by),
            )
            return cur.lastrowid

    @staticmethod
    def update(conversation_id, title, description, status):
        """更新会话"""
        with get_connection() as conn:
            conn.execute(
                "UPDATE conversations SET title=?, description=?, status=?, update_at=datetime('now') WHERE id=?",
                (title, description, status, conversation_id),
            )

    @staticmethod
    def delete(conversation_id):
        """删除会话及其关联数据"""
        with get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id=?", (conversation_id,))
            conn.execute("DELETE FROM violation_logs WHERE conversation_id=?", (conversation_id,))
            conn.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))

    @staticmethod
    def update_message_count(conversation_id):
        """更新会话的消息计数"""
        with get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM messages WHERE conversation_id=?", (conversation_id,)
            ).fetchone()["cnt"]
            conn.execute("UPDATE conversations SET message_count=?, update_at=datetime('now') WHERE id=?", (count, conversation_id))


class MessageRepository:
    @staticmethod
    def get_page(conversation_id, page=1, page_size=50):
        """分页获取消息"""
        with get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) AS cnt FROM messages WHERE conversation_id=?", (conversation_id,)
            ).fetchone()["cnt"]
            offset = (page - 1) * page_size
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
                (conversation_id, page_size, offset),
            ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def get_by_id(message_id):
        """根据ID获取消息"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(conversation_id, role, content):
        """新增消息"""
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
                (conversation_id, role, content),
            )
            return cur.lastrowid

    @staticmethod
    def update_analysis(message_id, sentiment, topic, entities):
        """更新消息分析结果"""
        entities_str = json.dumps(entities, ensure_ascii=False) if isinstance(entities, (list, tuple)) else entities
        with get_connection() as conn:
            conn.execute(
                "UPDATE messages SET sentiment=?, topic=?, entities=? WHERE id=?",
                (sentiment, topic, entities_str, message_id),
            )

    @staticmethod
    def set_violation_flag(message_id, flag=1):
        """设置违规标记"""
        with get_connection() as conn:
            conn.execute("UPDATE messages SET violation_flag=? WHERE id=?", (flag, message_id))


class ViolationLogRepository:
    @staticmethod
    def get_page(page=1, page_size=20, conversation_id=None, severity=""):
        """分页获取违规记录"""
        with get_connection() as conn:
            conditions = []
            params = []
            if conversation_id:
                conditions.append("conversation_id=?")
                params.append(conversation_id)
            if severity:
                conditions.append("severity=?")
                params.append(severity)
            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            total = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM violation_logs {where}", params
            ).fetchone()["cnt"]
            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM violation_logs {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def create(conversation_id, message_id, violation_type, violation_content, matched_keyword="", severity="low"):
        """新增违规记录"""
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO violation_logs (conversation_id, message_id, violation_type, violation_content, matched_keyword, severity) VALUES (?, ?, ?, ?, ?, ?)",
                (conversation_id, message_id, violation_type, violation_content, matched_keyword, severity),
            )
            return cur.lastrowid

    @staticmethod
    def get_by_id(violation_id):
        """获取单个违规记录"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM violation_logs WHERE id=?", (violation_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_status(violation_id, status):
        """更新违规处理状态"""
        with get_connection() as conn:
            conn.execute("UPDATE violation_logs SET status=? WHERE id=?", (status, violation_id))
