# 权限管理控制器（功能-角色映射）
import json
import tornado.web
from app.controllers.base import BaseHandler
from app.models.role import RoleRepository
from app.models.feature import FeatureRepository
from app.models.permission import PermissionRepository


class PermissionHandler(BaseHandler):
    """权限管理页面"""
    @tornado.web.authenticated
    def get(self):
        self.render("permission_list.html", title="权限管理")


class PermissionRoleListHandler(BaseHandler):
    """获取角色列表供权限管理使用（JSON）"""
    @tornado.web.authenticated
    def get(self):
        rows = RoleRepository.get_all()
        data = [{"id": r["id"], "name": r["name"], "code": r["code"]} for r in rows]
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data, ensure_ascii=False, default=str))


class PermissionFeatureTreeHandler(BaseHandler):
    """获取功能树（带角色权限选中状态）"""
    @tornado.web.authenticated
    def get(self):
        role_id = int(self.get_argument("role_id", 0))
        all_features = FeatureRepository.get_all()
        if role_id > 0:
            checked_ids = set(PermissionRepository.get_permissions_by_role(role_id))
        else:
            checked_ids = set()

        parents = [f for f in all_features if f["parent_id"] == 0]
        tree = []
        for p in parents:
            children = []
            for f in all_features:
                if f["parent_id"] == p["id"]:
                    children.append({
                        "id": f["id"],
                        "name": f["name"],
                        "code": f["code"],
                        "checked": f["id"] in checked_ids,
                    })
            # 如果没有子节点，父节点本身作为可选功能
            if not children:
                tree.append({
                    "id": p["id"],
                    "name": p["name"],
                    "code": p["code"],
                    "checked": p["id"] in checked_ids,
                    "leaf": True,
                })
            else:
                tree.append({
                    "id": p["id"],
                    "name": p["name"],
                    "code": p["code"],
                    "children": children,
                    "leaf": False,
                })
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(tree, ensure_ascii=False, default=str))


class PermissionSaveHandler(BaseHandler):
    """保存角色权限"""
    @tornado.web.authenticated
    def post(self):
        role_id = int(self.get_body_argument("role_id"))
        feature_ids_str = self.get_body_argument("feature_ids", "")
        feature_ids = []
        if feature_ids_str:
            feature_ids = [int(x) for x in feature_ids_str.split(",") if x.strip()]
        PermissionRepository.set_permissions(role_id, feature_ids)
        self.write(json.dumps({"code": 0, "msg": "权限设置成功"}))
