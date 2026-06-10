# 对话管理数据访问层
import json
from app.models.db import get_connection


class DialogueRepository:
    @staticmethod
    def get_all():
        """获取所有对话记录"""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM dialogues ORDER BY id DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_page(page=1, page_size=10, keyword=""):
        """分页获取对话记录"""
        with get_connection() as conn:
            conditions = []
            params = []
            if keyword:
                conditions.append("(name LIKE ? OR description LIKE ? OR content LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
            where = "WHERE " + " AND ".join(conditions) if conditions else ""

            total = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM dialogues {where}", params
            ).fetchone()["cnt"]
            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM dialogues {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def get_by_id(dialogue_id):
        """根据ID获取对话记录"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM dialogues WHERE id=?", (dialogue_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(name, content, description, model_id=0, system_prompt="", created_by=0):
        """新增对话记录"""
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO dialogues (name, content, description, model_id, system_prompt, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                (name, content, description, model_id, system_prompt, created_by),
            )
            return cur.lastrowid

    @staticmethod
    def update(dialogue_id, name, content, description, model_id=0, system_prompt="", is_active=1):
        """更新对话记录"""
        with get_connection() as conn:
            conn.execute(
                "UPDATE dialogues SET name=?, content=?, description=?, model_id=?, system_prompt=?, is_active=?, update_at=datetime('now') WHERE id=?",
                (name, content, description, model_id, system_prompt, is_active, dialogue_id),
            )

    @staticmethod
    def delete(dialogue_id):
        """删除对话记录"""
        with get_connection() as conn:
            conn.execute("DELETE FROM dialogues WHERE id=?", (dialogue_id,))


class DialogueCallLogRepository:
    @staticmethod
    def get_page(page=1, page_size=20, dialogue_id=None):
        """分页获取调用记录"""
        with get_connection() as conn:
            if dialogue_id:
                total = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM dialogue_call_logs WHERE dialogue_id=?", (dialogue_id,)
                ).fetchone()["cnt"]
                offset = (page - 1) * page_size
                rows = conn.execute(
                    "SELECT * FROM dialogue_call_logs WHERE dialogue_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
                    (dialogue_id, page_size, offset),
                ).fetchall()
            else:
                total = conn.execute("SELECT COUNT(*) AS cnt FROM dialogue_call_logs").fetchone()["cnt"]
                offset = (page - 1) * page_size
                rows = conn.execute(
                    "SELECT * FROM dialogue_call_logs ORDER BY id DESC LIMIT ? OFFSET ?",
                    (page_size, offset),
                ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def create(dialogue_id, input_data, output_data, status, duration_ms=0, error_message=""):
        """记录调用日志"""
        with get_connection() as conn:
            input_str = json.dumps(input_data, ensure_ascii=False) if isinstance(input_data, dict) else str(input_data)
            output_str = json.dumps(output_data, ensure_ascii=False) if isinstance(output_data, dict) else str(output_data)
            conn.execute(
                "INSERT INTO dialogue_call_logs (dialogue_id, input_data, output_data, status, duration_ms, error_message) VALUES (?, ?, ?, ?, ?, ?)",
                (dialogue_id, input_str, output_str, status, duration_ms, error_message),
            )
