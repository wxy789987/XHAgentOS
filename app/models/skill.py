# 技能管理数据访问层
import json
from datetime import datetime
from app.models.db import get_connection


class SkillRepository:
    @staticmethod
    def get_all():
        """获取所有技能"""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM skills ORDER BY id DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_page(page=1, page_size=10, keyword="", skill_type="", category=""):
        """分页获取技能"""
        with get_connection() as conn:
            conditions = []
            params = []
            if keyword:
                conditions.append("(name LIKE ? OR description LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if skill_type:
                conditions.append("skill_type=?")
                params.append(skill_type)
            if category:
                conditions.append("category=?")
                params.append(category)
            where = "WHERE " + " AND ".join(conditions) if conditions else ""

            total = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM skills {where}", params
            ).fetchone()["cnt"]
            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM skills {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def get_by_id(skill_id):
        """根据ID获取技能"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM skills WHERE id=?", (skill_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(name, description, skill_type, category, config, parameters, created_by=0):
        """新增技能"""
        with get_connection() as conn:
            config_str = json.dumps(config, ensure_ascii=False) if isinstance(config, (dict, list)) else config
            params_str = json.dumps(parameters, ensure_ascii=False) if isinstance(parameters, (dict, list)) else parameters
            cur = conn.execute(
                "INSERT INTO skills (name, description, skill_type, category, config, parameters, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, description, skill_type, category, config_str, params_str, created_by),
            )
            return cur.lastrowid

    @staticmethod
    def update(skill_id, name, description, skill_type, category, config, parameters, is_active=1):
        """更新技能"""
        with get_connection() as conn:
            config_str = json.dumps(config, ensure_ascii=False) if isinstance(config, (dict, list)) else config
            params_str = json.dumps(parameters, ensure_ascii=False) if isinstance(parameters, (dict, list)) else parameters
            conn.execute(
                "UPDATE skills SET name=?, description=?, skill_type=?, category=?, config=?, parameters=?, is_active=?, update_at=datetime('now') WHERE id=?",
                (name, description, skill_type, category, config_str, params_str, is_active, skill_id),
            )

    @staticmethod
    def delete(skill_id):
        """删除技能"""
        with get_connection() as conn:
            conn.execute("DELETE FROM skills WHERE id=?", (skill_id,))

    @staticmethod
    def get_categories():
        """获取所有分类"""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT category FROM skills WHERE category != '' AND is_active=1 ORDER BY category"
            ).fetchall()
            return [r["category"] for r in rows]


class SkillCallLogRepository:
    @staticmethod
    def get_page(page=1, page_size=20, skill_id=None):
        """分页获取调用记录"""
        with get_connection() as conn:
            if skill_id:
                total = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM skill_call_logs WHERE skill_id=?", (skill_id,)
                ).fetchone()["cnt"]
                offset = (page - 1) * page_size
                rows = conn.execute(
                    "SELECT * FROM skill_call_logs WHERE skill_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
                    (skill_id, page_size, offset),
                ).fetchall()
            else:
                total = conn.execute("SELECT COUNT(*) AS cnt FROM skill_call_logs").fetchone()["cnt"]
                offset = (page - 1) * page_size
                rows = conn.execute(
                    "SELECT * FROM skill_call_logs ORDER BY id DESC LIMIT ? OFFSET ?",
                    (page_size, offset),
                ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def create(skill_id, input_data, output_data, status, duration_ms=0, error_message=""):
        """记录调用日志"""
        with get_connection() as conn:
            input_str = json.dumps(input_data, ensure_ascii=False) if isinstance(input_data, dict) else str(input_data)
            output_str = json.dumps(output_data, ensure_ascii=False) if isinstance(output_data, dict) else str(output_data)
            conn.execute(
                "INSERT INTO skill_call_logs (skill_id, input_data, output_data, status, duration_ms, error_message) VALUES (?, ?, ?, ?, ?, ?)",
                (skill_id, input_str, output_str, status, duration_ms, error_message),
            )
