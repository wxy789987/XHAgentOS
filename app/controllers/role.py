# 角色管理控制器
import json
import tornado.web
from app.controllers.base import BaseHandler
from app.models.role import RoleRepository


class RoleHandler(BaseHandler):
    """角色管理页面"""
    @tornado.web.authenticated
    def get(self):
        self.render("role_list.html", title="角色管理")


class RoleListHandler(BaseHandler):
    """获取角色列表（JSON）"""
    @tornado.web.authenticated
    def get(self):
        rows = RoleRepository.get_all()
        data = []
        for r in rows:
            user_count = RoleRepository.get_user_count(r["id"])
            data.append({
                "id": r["id"],
                "name": r["name"],
                "code": r["code"],
                "description": r["description"],
                "is_system": r["is_system"],
                "user_count": user_count,
                "create_at": r["create_at"],
            })
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({"code": 0, "msg": "", "data": data}, ensure_ascii=False, default=str))


class RoleAddHandler(BaseHandler):
    """新增角色"""
    @tornado.web.authenticated
    def post(self):
        name = self.get_body_argument("name", "").strip()
        code = self.get_body_argument("code", "").strip()
        description = self.get_body_argument("description", "").strip()
        if not name or not code:
            return self.write(json.dumps({"code": 1, "msg": "名称和编码不能为空"}))
        ok = RoleRepository.create(name, code, description)
        if ok:
            self.write(json.dumps({"code": 0, "msg": "新增成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "编码已存在"}))


class RoleEditHandler(BaseHandler):
    """编辑角色"""
    @tornado.web.authenticated
    def post(self):
        rid = int(self.get_body_argument("id"))
        name = self.get_body_argument("name", "").strip()
        description = self.get_body_argument("description", "").strip()
        ok = RoleRepository.update(rid, name=name, description=description)
        if ok:
            self.write(json.dumps({"code": 0, "msg": "更新成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "系统角色不能修改名称或删除"}))


class RoleDeleteHandler(BaseHandler):
    """删除角色"""
    @tornado.web.authenticated
    def post(self):
        rid = int(self.get_body_argument("id"))
        ok = RoleRepository.delete(rid)
        if ok:
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "系统角色不能删除"}))
