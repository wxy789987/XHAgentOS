# 用于登录/注册/退出 有关的控制层方法
import json
import tornado.web
from app.controllers.base import BaseHandler
from app.models.user import UserRepository
from app.models.role import RoleRepository


class LoginHandler(BaseHandler):
    def get(self):
        # 如果已登录，根据角色跳转
        username = self.get_current_user()
        if username:
            user = UserRepository.get_user_by_username(username)
            role_id = dict(user).get("role_id", 2) if user else 2
            if role_id == 1:
                self.redirect("/admin")
            else:
                self.redirect("/user")
            return
        self.render("login.html", title="登录", error=None)

    def post(self):
        username = self.get_body_argument("username", "").strip()
        password = self.get_body_argument("password", "")

        if not username or not password:
            self.set_status(400)
            return self.render("login.html", title="登录", error="请输入用户名或密码")

        if not UserRepository.verify_user(username, password):
            self.set_status(401)
            return self.render("login.html", title="登录", error="输入的用户名或密码错误")

        self.set_secure_cookie("username", username)

        # 根据角色跳转
        user = UserRepository.get_user_by_username(username)
        role_id = dict(user).get("role_id", 2) if user else 2
        if role_id == 1:
            self.redirect("/admin")
        else:
            self.redirect("/user")


class RegisterHandler(BaseHandler):
    def get(self):
        self.render("register.html", title="注册", error=None)

    def post(self):
        username = self.get_body_argument("username", "").strip()
        password = self.get_body_argument("password", "")

        if not username or not password:
            self.set_status(400)
            return self.render("register.html", title="注册", error="请输入用户名和密码")

        if len(username) < 2 or len(username) > 20:
            self.set_status(400)
            return self.render("register.html", title="注册", error="用户名长度应为2-20个字符")

        if len(password) < 4:
            self.set_status(400)
            return self.render("register.html", title="注册", error="密码长度至少4位")

        # 注册为普通用户(role_id=2)
        ok = UserRepository.create_user(username, password, role_id=2)
        if not ok:
            self.set_status(409)
            return self.render("register.html", title="注册", error="用户名已存在")

        # 自动登录
        self.set_secure_cookie("username", username)
        self.redirect("/user")


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("username")
        self.redirect("/")

    def post(self):
        self.clear_cookie("username")
        self.redirect("/")


class UserRolesApiHandler(BaseHandler):
    """获取角色列表（登录页角色选择用）"""
    def get(self):
        roles = RoleRepository.get_all()
        data = [{"id": r["id"], "name": r["name"], "code": r["code"]} for r in roles]
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data, ensure_ascii=False))
