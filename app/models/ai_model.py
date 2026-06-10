# AI模型数据访问层
from app.models.db import get_connection

class AiModelRepository:
    @staticmethod
    def get_all():
        """获取所有模型"""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM ai_models ORDER BY is_default DESC, id DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_page(page=1, page_size=6):
        """分页获取模型"""
        with get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) AS cnt FROM ai_models").fetchone()["cnt"]
            offset = (page - 1) * page_size
            rows = conn.execute(
                "SELECT * FROM ai_models ORDER BY is_default DESC, id DESC LIMIT ? OFFSET ?",
                (page_size, offset),
            ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def get_by_id(model_id):
        """根据ID获取模型"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM ai_models WHERE id=?", (model_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(name, model_name, base_url, api_key, max_tokens=4096, temperature=0.7):
        """新增模型"""
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO ai_models (name, model_name, base_url, api_key, max_tokens, temperature) VALUES (?, ?, ?, ?, ?, ?)",
                (name, model_name, base_url, api_key, max_tokens, temperature),
            )
            return cur.lastrowid

    @staticmethod
    def update(model_id, name, model_name, base_url, api_key, max_tokens, temperature, is_active):
        """更新模型"""
        with get_connection() as conn:
            conn.execute(
                "UPDATE ai_models SET name=?, model_name=?, base_url=?, api_key=?, max_tokens=?, temperature=?, is_active=?, update_at=datetime('now') WHERE id=?",
                (name, model_name, base_url, api_key, max_tokens, temperature, is_active, model_id),
            )

    @staticmethod
    def delete(model_id):
        """删除模型"""
        with get_connection() as conn:
            conn.execute("DELETE FROM ai_models WHERE id=?", (model_id,))

    @staticmethod
    def batch_delete(ids):
        """批量删除"""
        with get_connection() as conn:
            placeholders = ",".join(["?"] * len(ids))
            conn.execute(f"DELETE FROM ai_models WHERE id IN ({placeholders})", ids)

    @staticmethod
    def batch_toggle_active(ids, is_active):
        """批量启用/禁用"""
        with get_connection() as conn:
            placeholders = ",".join(["?"] * len(ids))
            conn.execute(
                f"UPDATE ai_models SET is_active=?, update_at=datetime('now') WHERE id IN ({placeholders})",
                [is_active] + ids,
            )

    @staticmethod
    def set_default(model_id):
        """设置默认模型（仅一个模型为默认）"""
        with get_connection() as conn:
            conn.execute("UPDATE ai_models SET is_default=0")
            conn.execute("UPDATE ai_models SET is_default=1 WHERE id=?", (model_id,))

    @staticmethod
    def get_default():
        """获取默认模型"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM ai_models WHERE is_default=1 AND is_active=1 LIMIT 1").fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_token_stats(model_id=None):
        """获取Token使用统计"""
        with get_connection() as conn:
            if model_id:
                rows = conn.execute(
                    "SELECT strftime('%Y-%m-%d', create_at) AS date, SUM(prompt_tokens) AS prompt_tokens, SUM(completion_tokens) AS completion_tokens, SUM(total_tokens) AS total_tokens FROM model_chat_logs WHERE model_id=? GROUP BY date ORDER BY date DESC LIMIT 30",
                    (model_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT strftime('%Y-%m-%d', create_at) AS date, SUM(prompt_tokens) AS prompt_tokens, SUM(completion_tokens) AS completion_tokens, SUM(total_tokens) AS total_tokens FROM model_chat_logs GROUP BY date ORDER BY date DESC LIMIT 30"
                ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def log_chat(model_id, prompt_tokens, completion_tokens):
        """记录对话Token消耗"""
        total_tokens = prompt_tokens + completion_tokens
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO model_chat_logs (model_id, prompt_tokens, completion_tokens, total_tokens) VALUES (?, ?, ?, ?)",
                (model_id, prompt_tokens, completion_tokens, total_tokens),
            )
