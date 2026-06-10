# 瞭望管理数据访问层
import json
from app.models.db import get_connection

class LookoutSourceRepository:
    @staticmethod
    def get_all():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM lookout_sources ORDER BY id DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_page(page=1, page_size=10):
        with get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) AS cnt FROM lookout_sources").fetchone()["cnt"]
            offset = (page - 1) * page_size
            rows = conn.execute(
                "SELECT * FROM lookout_sources ORDER BY id DESC LIMIT ? OFFSET ?",
                (page_size, offset),
            ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def get_by_id(source_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM lookout_sources WHERE id=?", (source_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def create(name, url_template, headers, item_selector="", title_selector="",
               url_selector="", summary_selector="", time_selector="",
               page_param="pn", page_size=10):
        with get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO lookout_sources 
                   (name, url_template, headers, item_selector, title_selector,
                    url_selector, summary_selector, time_selector, page_param, page_size)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, url_template, json.dumps(headers, ensure_ascii=False) if isinstance(headers, dict) else headers,
                 item_selector, title_selector, url_selector, summary_selector, time_selector,
                 page_param, page_size),
            )
            return cur.lastrowid

    @staticmethod
    def update(source_id, name, url_template, headers, item_selector="", title_selector="",
               url_selector="", summary_selector="", time_selector="",
               page_param="pn", page_size=10, is_active=1):
        with get_connection() as conn:
            conn.execute(
                """UPDATE lookout_sources SET name=?, url_template=?, headers=?,
                   item_selector=?, title_selector=?, url_selector=?, summary_selector=?,
                   time_selector=?, page_param=?, page_size=?, is_active=?,
                   update_at=datetime('now') WHERE id=?""",
                (name, url_template,
                 json.dumps(headers, ensure_ascii=False) if isinstance(headers, dict) else headers,
                 item_selector, title_selector, url_selector, summary_selector, time_selector,
                 page_param, page_size, is_active, source_id),
            )

    @staticmethod
    def delete(source_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM lookout_sources WHERE id=?", (source_id,))

    @staticmethod
    def get_active_sources():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM lookout_sources WHERE is_active=1 ORDER BY id DESC"
            ).fetchall()
            return [dict(r) for r in rows]


class LookoutRecordRepository:
    @staticmethod
    def get_page(page=1, page_size=20, source_id=None, keyword="",
                 date_from="", date_to="", status="", deep_status=None):
        with get_connection() as conn:
            conditions = []
            params = []
            if source_id:
                conditions.append("r.source_id=?")
                params.append(source_id)
            if keyword:
                conditions.append("(r.title LIKE ? OR r.summary LIKE ? OR r.keywords LIKE ?)")
                kw = f"%{keyword}%"
                params.extend([kw, kw, kw])
            if date_from:
                conditions.append("r.create_at >= ?")
                params.append(date_from)
            if date_to:
                conditions.append("r.create_at <= ?")
                params.append(date_to + " 23:59:59")
            if status:
                conditions.append("r.status=?")
                params.append(status)
            if deep_status == 'pending':
                conditions.append("(r.deep_status IS NULL OR r.deep_status != 'completed')")
            elif deep_status == 'completed':
                conditions.append("r.deep_status='completed'")

            where = ""
            if conditions:
                where = "WHERE " + " AND ".join(conditions)

            total = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM lookout_records r {where}",
                params,
            ).fetchone()["cnt"]

            offset = (page - 1) * page_size
            rows = conn.execute(
                f"""SELECT r.*, s.name AS source_name 
                    FROM lookout_records r 
                    LEFT JOIN lookout_sources s ON r.source_id = s.id
                    {where} ORDER BY r.id DESC LIMIT ? OFFSET ?""",
                params + [page_size, offset],
            ).fetchall()
            return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}

    @staticmethod
    def bulk_insert(source_id, items):
        """批量插入采集记录，items: [{title, url, summary, publish_time, content}]"""
        with get_connection() as conn:
            count = 0
            for item in items:
                # 去重：相同source_id + url不重复插入
                existing = conn.execute(
                    "SELECT id FROM lookout_records WHERE source_id=? AND url=?",
                    (source_id, item.get("url", "")),
                ).fetchone()
                if existing:
                    continue
                conn.execute(
                    """INSERT INTO lookout_records 
                       (source_id, title, url, summary, content, publish_time, keywords, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'collected')""",
                    (source_id, item.get("title", ""), item.get("url", ""),
                     item.get("summary", ""), item.get("content", ""),
                     item.get("publish_time", ""), item.get("keywords", "")),
                )
                count += 1
            return count

    @staticmethod
    def get_by_ids(ids):
        with get_connection() as conn:
            placeholders = ",".join(["?"] * len(ids))
            rows = conn.execute(
                f"SELECT * FROM lookout_records WHERE id IN ({placeholders}) ORDER BY id DESC",
                ids,
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def delete(ids):
        with get_connection() as conn:
            placeholders = ",".join(["?"] * len(ids))
            conn.execute(f"DELETE FROM lookout_records WHERE id IN ({placeholders})", ids)

    @staticmethod
    def get_all_for_export(source_id=None, keyword="", date_from="", date_to="", status=""):
        """导出用：获取全部匹配记录（不分页）"""
        with get_connection() as conn:
            conditions = []
            params = []
            if source_id:
                conditions.append("r.source_id=?")
                params.append(source_id)
            if keyword:
                conditions.append("(r.title LIKE ? OR r.summary LIKE ?)")
                kw = f"%{keyword}%"
                params.extend([kw, kw])
            if date_from:
                conditions.append("r.create_at >= ?")
                params.append(date_from)
            if date_to:
                conditions.append("r.create_at <= ?")
                params.append(date_to + " 23:59:59")
            if status:
                conditions.append("r.status=?")
                params.append(status)

            where = ""
            if conditions:
                where = "WHERE " + " AND ".join(conditions)

            rows = conn.execute(
                f"""SELECT r.*, s.name AS source_name 
                    FROM lookout_records r 
                    LEFT JOIN lookout_sources s ON r.source_id = s.id
                    {where} ORDER BY r.id DESC""",
                params,
            ).fetchall()
            return [dict(r) for r in rows]
