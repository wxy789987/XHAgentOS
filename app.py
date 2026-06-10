import os
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer

# v0.3 加载动态登录业务
from app.controllers.auth import LoginHandler, LogoutHandler
from app.controllers.home import AdminHandler
from app.controllers.user import (
    UserHandler,
    UserListDataHandler,
    UserAddHandler,
    UserEditHandler,
    UserDeleteHandler,
)
from app.controllers.feature import (
    FeatureHandler,
    FeatureTreeHandler,
    FeatureAddHandler,
    FeatureEditHandler,
    FeatureDeleteHandler,
    FeatureMenuHandler,
)
from app.controllers.role import (
    RoleHandler,
    RoleListHandler,
    RoleAddHandler,
    RoleEditHandler,
    RoleDeleteHandler,
)
from app.controllers.permission import (
    PermissionHandler,
    PermissionRoleListHandler,
    PermissionFeatureTreeHandler,
    PermissionSaveHandler,
)
from app.models.db import init_db
from app.models.user import UserRepository
from app.models.feature import FeatureRepository
from app.models.role import RoleRepository
from app.models.permission import PermissionRepository


def seed_data():
    """初始化种子数据"""
    # 创建默认角色
    db = __import__('app.models.db', fromlist=['get_connection'])
    conn = db.get_connection()

    # 创建系统角色
    roles = [
        (1, "超级管理员", "admin", "系统内置超级管理员", 1),
        (2, "普通用户", "user", "系统内置普通用户", 1),
    ]
    for rid, name, code, desc, system in roles:
        conn.execute(
            "INSERT OR IGNORE INTO roles (id, name, code, description, is_system) VALUES (?, ?, ?, ?, ?)",
            (rid, name, code, desc, system),
        )
    conn.commit()

    # 创建默认功能菜单
    features = [
        # 一级菜单（父级）
        (1, "用户管理", "user_mgr", "layui-icon-user", 0, "/admin/user", 1, 1),
        (2, "功能管理", "feature_mgr", "layui-icon-set", 0, "/admin/feature", 2, 1),
        (3, "角色管理", "role_mgr", "layui-icon-auz", 0, "/admin/role", 3, 1),
        (4, "权限管理", "perm_mgr", "layui-icon-password", 0, "/admin/permission", 4, 1),
        (5, "系统管理", "sys_mgr", "layui-icon-set", 0, "", 5, 1),
        # 二级菜单（系统管理的子功能，预留）
    ]
    for fid, name, code, icon, parent_id, url, sort, active in features:
        conn.execute(
            "INSERT OR IGNORE INTO features (id, name, code, icon, parent_id, url, sort, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (fid, name, code, icon, parent_id, url, sort, active),
        )
    conn.commit()

    # 为超级管理员赋予所有功能权限
    all_feature_ids = [f[0] for f in features]
    PermissionRepository.set_permissions(1, all_feature_ids)

    conn.close()

    # 创建默认管理员账号
    if not UserRepository.get_user_by_username("admin"):
        UserRepository.create_user("admin", "admin123")
        print(">>> 默认管理员账号已创建 (admin/admin123)")
        # 设置管理员角色为超级管理员
        admin = UserRepository.get_user_by_username("admin")
        if admin:
            with db.get_connection() as c:
                c.execute("UPDATE users SET role_id=1 WHERE id=?", (admin["id"],))


def make_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    settings = dict(
        template_path=os.path.join(base_dir, "app", "templates"),
        static_path=os.path.join(base_dir, "app", "static"),
        cookie_secret="demo-cookie-secrete-change-me",
        login_url="/auth/login",
        xsrf_cookies=True,
        debug=True,
        auto_reload=True,
    )

    return tornado.web.Application(
        [
            # 认证
            (r"/", LoginHandler),
            (r"/auth/login", LoginHandler),
            (r"/auth/logout", LogoutHandler),
            # 后台主页
            (r"/admin", AdminHandler),
            # 用户管理
            (r"/admin/user", UserHandler),
            (r"/admin/user/list", UserListDataHandler),
            (r"/admin/user/add", UserAddHandler),
            (r"/admin/user/edit", UserEditHandler),
            (r"/admin/user/delete", UserDeleteHandler),
            # 功能管理
            (r"/admin/feature", FeatureHandler),
            (r"/admin/feature/tree", FeatureTreeHandler),
            (r"/admin/feature/add", FeatureAddHandler),
            (r"/admin/feature/edit", FeatureEditHandler),
            (r"/admin/feature/delete", FeatureDeleteHandler),
            (r"/admin/feature/menu", FeatureMenuHandler),
            # 角色管理
            (r"/admin/role", RoleHandler),
            (r"/admin/role/list", RoleListHandler),
            (r"/admin/role/add", RoleAddHandler),
            (r"/admin/role/edit", RoleEditHandler),
            (r"/admin/role/delete", RoleDeleteHandler),
            # 权限管理
            (r"/admin/permission", PermissionHandler),
            (r"/admin/permission/role_list", PermissionRoleListHandler),
            (r"/admin/permission/feature_tree", PermissionFeatureTreeHandler),
            (r"/admin/permission/save", PermissionSaveHandler),
        ],
        **settings,
    )


if __name__ == "__main__":
    init_db()
    seed_data()
    app = make_app()
    server = HTTPServer(app)
    server.listen(10086)
    print("Server Start At http://127.0.0.1:10086")
    tornado.ioloop.IOLoop.current().start()
