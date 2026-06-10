# 功能管理控制器（动态菜单管理）
import json
import tornado.web
from app.controllers.base import BaseHandler
from app.models.feature import FeatureRepository


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
        icon = self.get_body_argument("icon", "")
        parent_id = int(self.get_body_argument("parent_id", 0))
        url = self.get_body_argument("url", "").strip()
        sort = int(self.get_body_argument("sort", 0))
        if not name or not code:
            return self.write(json.dumps({"code": 1, "msg": "名称和编码不能为空"}))
        ok = FeatureRepository.create(name, code, icon, parent_id, url, sort)
        if ok:
            self.write(json.dumps({"code": 0, "msg": "新增成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "编码已存在"}))


class FeatureEditHandler(BaseHandler):
    """编辑功能"""
    @tornado.web.authenticated
    def post(self):
        fid = int(self.get_body_argument("id"))
        name = self.get_body_argument("name", "").strip()
        icon = self.get_body_argument("icon", "")
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
    """获取当前用户可见菜单（JSON，供左侧导航使用）"""
    @tornado.web.authenticated
    def get(self):
        menus = FeatureRepository.get_active_menus()
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(menus, ensure_ascii=False, default=str))
