# 数智大屏数据访问层
import json
from app.models.db import get_connection


class DatascreenRepository:
    @staticmethod
    def get_all():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM datascreens ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_page(page=1, page_size=10, keyword=""):
        with get_connection() as conn:
            conditions = []
            params = []
            if keyword:
                conditions.append("(name LIKE ? OR description LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            total = conn.execute(f"SELECT COUNT(*) AS cnt FROM datascreens {where}", params).fetchone()["cnt"]
            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM datascreens {where} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def get_by_id(ds_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM datascreens WHERE id=?", (ds_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(name, description, screen_type, chart_config, raw_data, layout_config, created_by=0):
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO datascreens (name, description, screen_type, chart_config, raw_data, layout_config, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, description, screen_type,
                 json.dumps(chart_config, ensure_ascii=False) if isinstance(chart_config, (dict, list)) else chart_config,
                 json.dumps(raw_data, ensure_ascii=False) if isinstance(raw_data, (dict, list)) else raw_data,
                 json.dumps(layout_config, ensure_ascii=False) if isinstance(layout_config, (dict, list)) else layout_config,
                 created_by),
            )
            return cur.lastrowid

    @staticmethod
    def update(ds_id, name, description, screen_type, chart_config, raw_data, layout_config, is_active=1):
        with get_connection() as conn:
            conn.execute(
                "UPDATE datascreens SET name=?, description=?, screen_type=?, chart_config=?, raw_data=?, layout_config=?, is_active=?, update_at=datetime('now') WHERE id=?",
                (name, description, screen_type,
                 json.dumps(chart_config, ensure_ascii=False) if isinstance(chart_config, (dict, list)) else chart_config,
                 json.dumps(raw_data, ensure_ascii=False) if isinstance(raw_data, (dict, list)) else raw_data,
                 json.dumps(layout_config, ensure_ascii=False) if isinstance(layout_config, (dict, list)) else layout_config,
                 is_active, ds_id),
            )

    @staticmethod
    def delete(ds_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM datascreens WHERE id=?", (ds_id,))


class DatascreenCallLogRepository:
    @staticmethod
    def get_page(page=1, page_size=20, datascreen_id=None):
        with get_connection() as conn:
            if datascreen_id:
                total = conn.execute("SELECT COUNT(*) AS cnt FROM datascreen_call_logs WHERE datascreen_id=?", (datascreen_id,)).fetchone()["cnt"]
                offset = (page - 1) * page_size
                rows = conn.execute(
                    "SELECT * FROM datascreen_call_logs WHERE datascreen_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
                    (datascreen_id, page_size, offset),
                ).fetchall()
            else:
                total = conn.execute("SELECT COUNT(*) AS cnt FROM datascreen_call_logs").fetchone()["cnt"]
                offset = (page - 1) * page_size
                rows = conn.execute(
                    "SELECT * FROM datascreen_call_logs ORDER BY id DESC LIMIT ? OFFSET ?",
                    (page_size, offset),
                ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def create(datascreen_id, action, detail=None):
        with get_connection() as conn:
            detail_str = json.dumps(detail, ensure_ascii=False) if detail else "{}"
            conn.execute(
                "INSERT INTO datascreen_call_logs (datascreen_id, action, detail) VALUES (?, ?, ?)",
                (datascreen_id, action, detail_str),
            )
