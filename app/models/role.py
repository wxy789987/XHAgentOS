# 角色数据访问模型
import sqlite3
from app.models.db import get_connection


class RoleRepository:
    @staticmethod
    def get_all():
        """获取所有角色"""
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM roles ORDER BY id ASC").fetchall()
        return rows

    @staticmethod
    def get_by_id(role_id):
        with get_connection() as conn:
            return conn.execute("SELECT * FROM roles WHERE id=?", (role_id,)).fetchone()

    @staticmethod
    def get_by_code(code):
        with get_connection() as conn:
            return conn.execute("SELECT * FROM roles WHERE code=?", (code,)).fetchone()

    @staticmethod
    def create(name, code, description=""):
        """新增角色"""
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO roles (name, code, description) VALUES (?, ?, ?)",
                    (name, code, description),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def update(role_id, name=None, description=None):
        """更新角色（系统角色不可修改名称）"""
        role = RoleRepository.get_by_id(role_id)
        if not role:
            return False
        if role["is_system"] == 1 and name is not None and name != role["name"]:
            return False  # 系统角色不能改名
        sets = []
        params = []
        if name is not None:
            sets.append("name=?")
            params.append(name)
        if description is not None:
            sets.append("description=?")
            params.append(description)
        if not sets:
            return True
        params.append(role_id)
        with get_connection() as conn:
            conn.execute(f"UPDATE roles SET {', '.join(sets)} WHERE id=?", params)
        return True

    @staticmethod
    def delete(role_id):
        """删除角色（系统角色不可删除）"""
        role = RoleRepository.get_by_id(role_id)
        if not role or role["is_system"] == 1:
            return False
        with get_connection() as conn:
            conn.execute("DELETE FROM role_permissions WHERE role_id=?", (role_id,))
            conn.execute("DELETE FROM roles WHERE id=?", (role_id,))
        return True

    @staticmethod
    def get_user_count(role_id):
        """获取某个角色下的用户数"""
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM users WHERE role_id=?", (role_id,)).fetchone()
        return row["cnt"]
