# 权限数据访问模型（功能-角色映射）
from app.models.db import get_connection


class PermissionRepository:
    @staticmethod
    def get_permissions_by_role(role_id):
        """获取角色已授权的功能ID列表"""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT feature_id FROM role_permissions WHERE role_id=?",
                (role_id,),
            ).fetchall()
        return [r["feature_id"] for r in rows]

    @staticmethod
    def set_permissions(role_id, feature_ids):
        """设置角色的权限（先清空再批量插入）"""
        with get_connection() as conn:
            conn.execute("DELETE FROM role_permissions WHERE role_id=?", (role_id,))
            for fid in feature_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO role_permissions (role_id, feature_id) VALUES (?, ?)",
                    (role_id, fid),
                )
        return True

    @staticmethod
    def get_roles_by_feature(feature_id):
        """获取拥有某功能的所有角色"""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT r.* FROM roles r JOIN role_permissions rp ON r.id=rp.role_id WHERE rp.feature_id=?",
                (feature_id,),
            ).fetchall()
        return rows
