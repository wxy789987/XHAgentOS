# 功能模块数据访问模型
import sqlite3
from app.models.db import get_connection


class FeatureRepository:
    @staticmethod
    def get_all():
        """获取所有功能列表"""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM features ORDER BY sort ASC, id ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_tree():
        """获取功能树（父子结构）"""
        all_features = FeatureRepository.get_all()
        parents = [f for f in all_features if f["parent_id"] == 0]
        result = []
        for p in parents:
            children = [f for f in all_features if f["parent_id"] == p["id"]]
            result.append({
                "id": p["id"],
                "name": p["name"],
                "code": p["code"],
                "icon": p["icon"],
                "url": p["url"],
                "sort": p["sort"],
                "is_active": p["is_active"],
                "children": children,
            })
        return result

    @staticmethod
    def get_active_menus():
        """获取启用的菜单（左侧导航用）"""
        all_features = FeatureRepository.get_all()
        active = [f for f in all_features if f["is_active"] == 1]
        parents = [f for f in active if f["parent_id"] == 0]
        result = []
        for p in parents:
            children = [f for f in active if f["parent_id"] == p["id"] and f["url"]]
            item = {
                "id": p["id"],
                "name": p["name"],
                "code": p["code"],
                "icon": p["icon"],
                "url": p["url"],
                "children": children,
            }
            result.append(item)
        return result

    @staticmethod
    def create(name, code, icon="", parent_id=0, url="", sort=0):
        """新增功能"""
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO features (name, code, icon, parent_id, url, sort) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, code, icon, parent_id, url, sort),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(feature_id, name=None, icon=None, parent_id=None, url=None, sort=None, is_active=None):
        """更新功能"""
        sets = []
        params = []
        if name is not None:
            sets.append("name=?")
            params.append(name)
        if icon is not None:
            sets.append("icon=?")
            params.append(icon)
        if parent_id is not None:
            sets.append("parent_id=?")
            params.append(parent_id)
        if url is not None:
            sets.append("url=?")
            params.append(url)
        if sort is not None:
            sets.append("sort=?")
            params.append(sort)
        if is_active is not None:
            sets.append("is_active=?")
            params.append(is_active)
        if not sets:
            return True
        params.append(feature_id)
        with get_connection() as conn:
            conn.execute(f"UPDATE features SET {', '.join(sets)} WHERE id=?", params)
        return True

    @staticmethod
    def delete(feature_id):
        """删除功能（同时删除子功能和权限映射）"""
        with get_connection() as conn:
            conn.execute("DELETE FROM role_permissions WHERE feature_id=?", (feature_id,))
            conn.execute("DELETE FROM features WHERE parent_id=?", (feature_id,))
            conn.execute("DELETE FROM features WHERE id=?", (feature_id,))
        return True

    @staticmethod
    def get_by_id(feature_id):
        with get_connection() as conn:
            return conn.execute("SELECT * FROM features WHERE id=?", (feature_id,)).fetchone()

    @staticmethod
    def get_by_code(code):
        with get_connection() as conn:
            return conn.execute("SELECT * FROM features WHERE code=?", (code,)).fetchone()
