# 功能管理控制器（CRUD + 菜单树）
import json
import tornado.web
from app.controllers.base import BaseHandler
from app.models.feature import FeatureRepository
from app.models.user import UserRepository
from app.models.permission import PermissionRepository


class FeatureHandler(BaseHandler):
    """功能管理页面"""
    @tornado.web.authenticated
    def get(self):
        self.render("feature_list.html", title="功能管理")


class FeatureTreeHandler(BaseHandler):
    """获取功能树（JSON）"""
    @tornado.web.authenticated
    def get(self):
        tree = FeatureRepository.get_tree()
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(tree, ensure_ascii=False, default=str))


class FeatureAddHandler(BaseHandler):
    """新增功能"""
    @tornado.web.authenticated
    def post(self):
        name = self.get_body_argument("name", "").strip()
        code = self.get_body_argument("code", "").strip()
        icon = self.get_body_argument("icon", "").strip()
        parent_id = int(self.get_body_argument("parent_id", 0))
        url = self.get_body_argument("url", "").strip()
        sort = int(self.get_body_argument("sort", 0))
        if not name or not code:
            return self.write(json.dumps({"code": 1, "msg": "名称和编码不能为空"}))
        if FeatureRepository.create(name, code, icon, parent_id, url, sort):
            self.write(json.dumps({"code": 0, "msg": "新增成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "编码已存在"}))


class FeatureEditHandler(BaseHandler):
    """编辑功能"""
    @tornado.web.authenticated
    def post(self):
        fid = int(self.get_body_argument("id"))
        name = self.get_body_argument("name", "").strip()
        icon = self.get_body_argument("icon", "").strip()
        parent_id = int(self.get_body_argument("parent_id", 0))
        url = self.get_body_argument("url", "").strip()
        sort = int(self.get_body_argument("sort", 0))
        is_active = int(self.get_body_argument("is_active", 1))
        FeatureRepository.update(fid, name=name, icon=icon, parent_id=parent_id, url=url, sort=sort, is_active=is_active)
        self.write(json.dumps({"code": 0, "msg": "更新成功"}))


class FeatureDeleteHandler(BaseHandler):
    """删除功能"""
    @tornado.web.authenticated
    def post(self):
        fid = int(self.get_body_argument("id"))
        FeatureRepository.delete(fid)
        self.write(json.dumps({"code": 0, "msg": "删除成功"}))


class FeatureMenuHandler(BaseHandler):
    """获取当前用户可见菜单（JSON，供左侧导航使用）- 根据权限过滤"""
    @tornado.web.authenticated
    def get(self):
        username = self.current_user
        user_obj = UserRepository.get_user_by_username(username)
        
        if user_obj:
            role_id = dict(user_obj).get('role_id', 2)
        else:
            role_id = 2
        
        user_permissions = PermissionRepository.get_permissions_by_role(role_id)
        
        all_features = FeatureRepository.get_all()
        active_features = [f for f in all_features if f["is_active"] == 1 and (f["url"] or f["parent_id"] == 0)]
        
        accessible_features = []
        for f in active_features:
            if f["id"] in user_permissions:
                accessible_features.append(f)
        
        parents = [dict(f) for f in accessible_features if f["parent_id"] == 0]
        result = []
        for p in parents:
            children = [dict(f) for f in accessible_features if f["parent_id"] == p["id"]]
            item = {
                "id": p["id"],
                "name": p["name"],
                "code": p["code"],
                "icon": p["icon"],
                "url": p["url"],
                "children": children,
            }
            result.append(item)
        
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(result, ensure_ascii=False, default=str))