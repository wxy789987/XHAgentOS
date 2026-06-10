# admin 控制层
import json
import tornado.web
from app.controllers.base import BaseHandler
from app.models.user import UserRepository
from app.models.role import RoleRepository
from app.models.feature import FeatureRepository
from app.models.permission import PermissionRepository


class AdminHandler(BaseHandler):
    """后台主页"""
    @tornado.web.authenticated
    def get(self):
        username = self.current_user if self.current_user else ""
        self.render("admin.html", title="后台首页", username=username)


class DashboardPageHandler(BaseHandler):
    """Dashboard 页面"""
    @tornado.web.authenticated
    def get(self):
        self.render("dashboard.html", title="仪表盘")


class DashboardDataHandler(BaseHandler):
    """Dashboard 数据API"""
    @tornado.web.authenticated
    def get(self):
        # 统计用户数
        _, user_total = UserRepository.list_users(1, 1)
        # 统计角色数
        roles = RoleRepository.get_all()
        role_total = len(roles)
        # 统计功能数
        features = FeatureRepository.get_all()
        feature_total = len(features)
        # 统计管理员角色用户数
        admin_user_count = RoleRepository.get_user_count(1)
        normal_user_count = RoleRepository.get_user_count(2)

        # 最近注册用户
        recent_users, _ = UserRepository.list_users(1, 5)

        data = {
            "user_total": user_total,
            "role_total": role_total,
            "feature_total": feature_total,
            "admin_user_count": admin_user_count,
            "normal_user_count": normal_user_count,
            "recent_users": [
                {"id": u["id"], "username": u["username"], "role_name": u["role_name"], "create_at": u["create_at"]}
                for u in recent_users
            ],
        }
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data, ensure_ascii=False))
