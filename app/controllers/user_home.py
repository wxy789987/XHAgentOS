# 用户侧首页控制层
import tornado.web
from app.controllers.base import BaseHandler


class UserIndexHandler(BaseHandler):
    """用户侧首页"""
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_info()
        self.render("user_index.html", title="XHAgentOS 用户中心",
                     username=user["username"])


class UserLogoutHandler(BaseHandler):
    """用户退出"""
    def get(self):
        self.clear_cookie("username")
        self.redirect("/auth/login")
