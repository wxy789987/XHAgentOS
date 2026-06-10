"""
基类：
- tornado.web.RequestHandler
- 处理cookie / session / token
- @authenticated
- RBAC权限支持
"""
import tornado.web
from app.models.user import UserRepository
from app.models.permission import PermissionRepository


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        username = self.get_secure_cookie("username")
        if not username:
            return None
        return username.decode('utf-8')

    def get_current_user_role_id(self):
        """获取当前登录用户的角色ID"""
        username = self.current_user
        if not username:
            return 2
        user = UserRepository.get_user_by_username(username)
        if user:
            return user["role_id"] if "role_id" in user else 2
        return 2

    def get_current_user_permissions(self):
        """获取当前登录用户的功能权限ID列表"""
        role_id = self.get_current_user_role_id()
        if not role_id:
            return []
        return PermissionRepository.get_permissions_by_role(role_id)

    def has_permission(self, feature_id):
        """检查当前用户是否有权限访问指定功能"""
        permissions = self.get_current_user_permissions()
        return feature_id in permissions

    def get_current_user_info(self):
        """获取当前用户完整信息（包含角色和权限）"""
        username = self.current_user
        if not username:
            return None
        user = UserRepository.get_user_by_username(username)
        if not user:
            return None
        user_dict = dict(user)
        user_dict["permissions"] = self.get_current_user_permissions()
        return user_dict
