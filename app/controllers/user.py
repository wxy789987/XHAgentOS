# 用户管理控制器（CRUD + 分页）
import json
import tornado.web
from app.controllers.base import BaseHandler
from app.models.user import UserRepository


class UserHandler(BaseHandler):
    """用户管理页面"""
    @tornado.web.authenticated
    def get(self):
        self.render("user_list.html", title="用户管理")


class UserListDataHandler(BaseHandler):
    """获取用户列表数据（分页JSON）"""
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        limit = int(self.get_argument("limit", 28))
        rows, total = UserRepository.list_users(page, limit)
        data = []
        for row in rows:
            data.append({
                "id": row["id"],
                "username": row["username"],
                "create_at": row["create_at"],
            })
        result = {"code": 0, "msg": "", "count": total, "data": data}
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(result, ensure_ascii=False))


class UserAddHandler(BaseHandler):
    """新增用户"""
    @tornado.web.authenticated
    def post(self):
        username = self.get_body_argument("username", "").strip()
        password = self.get_body_argument("password", "").strip()
        if not username or not password:
            return self.write(json.dumps({"code": 1, "msg": "用户名和密码不能为空"}))
        if UserRepository.create_user(username, password):
            self.write(json.dumps({"code": 0, "msg": "新增成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "用户名已存在"}))


class UserEditHandler(BaseHandler):
    """编辑用户"""
    @tornado.web.authenticated
    def post(self):
        user_id = int(self.get_body_argument("id"))
        username = self.get_body_argument("username", "").strip()
        password = self.get_body_argument("password", "").strip()
        if not username:
            return self.write(json.dumps({"code": 1, "msg": "用户名不能为空"}))
        ok = UserRepository.update_user(user_id, username=username, password=password if password else None)
        if ok:
            self.write(json.dumps({"code": 0, "msg": "更新成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "用户名已存在"}))


class UserDeleteHandler(BaseHandler):
    """删除用户"""
    @tornado.web.authenticated
    def post(self):
        user_id = int(self.get_body_argument("id"))
        # 不允许删除自己
        current_user = self.current_user
        target = UserRepository.get_user_by_id(user_id)
        if target and target["username"] == current_user:
            return self.write(json.dumps({"code": 1, "msg": "不能删除当前登录用户"}))
        UserRepository.delete_user(user_id)
        self.write(json.dumps({"code": 0, "msg": "删除成功"}))
