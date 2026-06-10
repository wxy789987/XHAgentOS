# 数字员工数据访问层
import json
from app.models.db import get_connection


class EmployeeRepository:
    @staticmethod
    def get_all():
        """获取所有数字员工"""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM digital_employees ORDER BY id DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_page(page=1, page_size=10, keyword=""):
        """分页获取数字员工"""
        with get_connection() as conn:
            conditions = []
            params = []
            if keyword:
                conditions.append("(name LIKE ? OR description LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            where = "WHERE " + " AND ".join(conditions) if conditions else ""

            total = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM digital_employees {where}", params
            ).fetchone()["cnt"]
            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM digital_employees {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def get_by_id(employee_id):
        """根据ID获取数字员工"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM digital_employees WHERE id=?", (employee_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(name, model_id, skill_ids, description, system_prompt, created_by=0):
        """新增数字员工"""
        with get_connection() as conn:
            skill_ids_str = json.dumps(skill_ids, ensure_ascii=False) if isinstance(skill_ids, (list, tuple)) else skill_ids
            cur = conn.execute(
                "INSERT INTO digital_employees (name, model_id, skill_ids, description, system_prompt, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                (name, model_id, skill_ids_str, description, system_prompt, created_by),
            )
            return cur.lastrowid

    @staticmethod
    def update(employee_id, name, model_id, skill_ids, description, system_prompt, is_active=1):
        """更新数字员工"""
        with get_connection() as conn:
            skill_ids_str = json.dumps(skill_ids, ensure_ascii=False) if isinstance(skill_ids, (list, tuple)) else skill_ids
            conn.execute(
                "UPDATE digital_employees SET name=?, model_id=?, skill_ids=?, description=?, system_prompt=?, is_active=?, update_at=datetime('now') WHERE id=?",
                (name, model_id, skill_ids_str, description, system_prompt, is_active, employee_id),
            )

    @staticmethod
    def delete(employee_id):
        """删除数字员工"""
        with get_connection() as conn:
            conn.execute("DELETE FROM digital_employees WHERE id=?", (employee_id,))


class EmployeeCallLogRepository:
    @staticmethod
    def get_page(page=1, page_size=20, employee_id=None):
        """分页获取调用记录"""
        with get_connection() as conn:
            if employee_id:
                total = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM employee_call_logs WHERE employee_id=?", (employee_id,)
                ).fetchone()["cnt"]
                offset = (page - 1) * page_size
                rows = conn.execute(
                    "SELECT * FROM employee_call_logs WHERE employee_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
                    (employee_id, page_size, offset),
                ).fetchall()
            else:
                total = conn.execute("SELECT COUNT(*) AS cnt FROM employee_call_logs").fetchone()["cnt"]
                offset = (page - 1) * page_size
                rows = conn.execute(
                    "SELECT * FROM employee_call_logs ORDER BY id DESC LIMIT ? OFFSET ?",
                    (page_size, offset),
                ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def create(employee_id, input_data, output_data, status, duration_ms=0, error_message=""):
        """记录调用日志"""
        with get_connection() as conn:
            input_str = json.dumps(input_data, ensure_ascii=False) if isinstance(input_data, dict) else str(input_data)
            output_str = json.dumps(output_data, ensure_ascii=False) if isinstance(output_data, dict) else str(output_data)
            conn.execute(
                "INSERT INTO employee_call_logs (employee_id, input_data, output_data, status, duration_ms, error_message) VALUES (?, ?, ?, ?, ?, ?)",
                (employee_id, input_str, output_str, status, duration_ms, error_message),
            )
