import os
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer

# v0.3 加载动态登录业务
from app.controllers.auth import LoginHandler, LogoutHandler, RegisterHandler, UserRolesApiHandler
from app.controllers.user_home import UserIndexHandler, UserLogoutHandler
from app.controllers.home import AdminHandler, DashboardPageHandler, DashboardDataHandler
from app.controllers.user import (
    UserHandler,
    UserListDataHandler,
    UserAddHandler,
    UserEditHandler,
    UserDeleteHandler,
    UserRolesHandler,
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
from app.controllers.ai_model import (
    AiModelHandler,
    AiModelListHandler,
    AiModelAddHandler,
    AiModelEditHandler,
    AiModelDeleteHandler,
    AiModelSetDefaultHandler,
    AiModelBatchHandler,
    AiModelChatHandler,
    AiModelChatStreamHandler,
    AiModelTokenStatsHandler,
)
from app.controllers.lookout import (
    LookoutSourceHandler,
    LookoutSourceListHandler,
    LookoutSourceAddHandler,
    LookoutSourceEditHandler,
    LookoutSourceGetHandler,
    LookoutSourceDeleteHandler,
    LookoutSourceActiveHandler,
    LookoutCollectPageHandler,
    LookoutCollectRunHandler,
    LookoutWarehouseHandler,
    LookoutWarehouseListHandler,
    LookoutWarehouseDeleteHandler,
    LookoutExportHandler,
)
from app.controllers.lookout_deep import (
    LookoutDeepHandler,
    LookoutDeepStartHandler,
    LookoutDeepStatusHandler,
    LookoutDeepGetHandler,
    LookoutDeepListHandler,
    LookoutDeepDeleteHandler,
    LookoutDeepAnalysisHandler,
    LookoutDeepSyncHandler,
)
from app.controllers.skill import (
    SkillHandler,
    SkillListHandler,
    SkillAddHandler,
    SkillEditHandler,
    SkillDeleteHandler,
    SkillGetHandler,
    SkillDetailHandler,
    SkillCategoriesHandler,
    SkillCallHandler,
    SkillAICreateHandler,
    SkillCallLogHandler,
)
from app.controllers.employee import (
    EmployeeHandler,
    EmployeeListHandler,
    EmployeeAddHandler,
    EmployeeEditHandler,
    EmployeeDeleteHandler,
    EmployeeGetHandler,
    EmployeeDetailHandler,
    EmployeeModelsHandler,
    EmployeeSkillsHandler,
    EmployeeCallHandler,
    EmployeeCallLogHandler,
    EmployeeGeneratePromptHandler,
)
from app.controllers.conversation import (
    ConversationHandler,
    ConversationListHandler,
    ConversationAddHandler,
    ConversationEditHandler,
    ConversationDeleteHandler,
    ConversationGetHandler,
    ConversationDetailHandler,
    MessageListHandler,
    MessageAddHandler,
    MessageAnalyzeHandler,
    MessageAnalyzeAllHandler,
    ViolationListHandler,
    ViolationUpdateHandler,
    ViolationMonitorPageHandler,
    ConversationCheckAllHandler,
)
from app.controllers.dialogue import (
    DialogueHandler,
    DialogueListHandler,
    DialogueGetHandler,
    DialogueAddHandler,
    DialogueEditHandler,
    DialogueDeleteHandler,
    DialogueDetailHandler,
    DialogueModelsHandler,
    DialogueCallHandler,
    DialogueCallLogHandler,
)
from app.controllers.datascreen import (
    DatascreenHandler,
    DatascreenListHandler,
    DatascreenGetHandler,
    DatascreenAddHandler,
    DatascreenEditHandler,
    DatascreenDeleteHandler,
    DatascreenViewHandler,
    DatascreenRenderHandler,
    DatascreenExportHandler,
    DatascreenCallLogHandler,
    DatascreenPreviewHandler,
)
from app.controllers.settings import (
    SettingsHandler,
    SettingsConfigHandler,
    SettingsLogsHandler,
    SettingsMonitorHandler,
    SettingsAnalysisHandler,
    SettingsMonitorDataHandler,
)
from app.controllers.user_dialogue import (
    UserChatHandler,
    UserChatEmployeeHandler,
    FriendListHandler,
    FriendSearchHandler,
    FriendAddHandler,
    FriendRemoveHandler,
    FriendRequestHandler,
    FriendRequestAcceptHandler,
    FriendRequestRejectHandler,
    GroupCreateHandler,
    GroupListHandler,
    GroupSearchHandler,
    GroupJoinHandler,
    GroupMembersHandler,
    GroupInviteHandler,
    GroupInviteEmployeeHandler,
    GroupEmployeeListHandler,
    GroupMessageSendHandler,
    GroupMessageListHandler,
    EmployeeListHandler as UserEmployeeListHandler,
    ChatExportHandler,
    ChatAnalyzeHandler,
)
from app.models.db import init_db
from app.models.user import UserRepository
from app.models.feature import FeatureRepository
from app.models.role import RoleRepository
from app.models.permission import PermissionRepository
from app.models.ai_model import AiModelRepository


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
        (99, "首页", "dashboard", "layui-icon-home", 0, "/admin/dashboard", 0, 1),
        (1, "用户管理", "user_mgr", "layui-icon-user", 0, "/admin/user", 1, 1),
        (2, "功能管理", "feature_mgr", "layui-icon-set", 0, "/admin/feature", 2, 1),
        (3, "角色管理", "role_mgr", "layui-icon-auz", 0, "/admin/role", 3, 1),
        (4, "权限管理", "perm_mgr", "layui-icon-password", 0, "/admin/permission", 4, 1),
        (6, "模型引擎", "ai_model_mgr", "layui-icon-app", 0, "/admin/ai_model", 5, 1),
        (7, "瞭望管理", "lookout_mgr", "layui-icon-search", 0, "/admin/lookout/source", 6, 1),
        (12, "技能管理", "skill_mgr", "layui-icon-component", 0, "/admin/skill", 8, 1),
        (13, "数字员工", "employee_mgr", "layui-icon-username", 0, "/admin/employee", 9, 1),
        (14, "会话管理", "conversation_mgr", "layui-icon-dialogue", 0, "/admin/conversation", 10, 1),
        (15, "对话管理", "dialogue_mgr", "layui-icon-speaker", 0, "/admin/dialogue", 11, 1),
        (16, "数智大屏", "datascreen_mgr", "layui-icon-chart", 0, "/admin/datascreen", 12, 1),
        (5, "系统管理", "sys_mgr", "layui-icon-set", 0, "/admin/settings", 7, 1),
        # 系统管理子菜单
        (17, "系统配置", "settings_config", "layui-icon-set", 5, "/admin/settings/config", 1, 1),
        (18, "日志查看", "settings_logs", "layui-icon-file-text", 5, "/admin/settings/logs", 2, 1),
        (19, "性能监控", "settings_monitor", "layui-icon-chart", 5, "/admin/settings/monitor", 3, 1),
        (20, "日志分析", "settings_analysis", "layui-icon-bar-chart", 5, "/admin/settings/analysis", 4, 1),
    ]
    for fid, name, code, icon, parent_id, url, sort, active in features:
        conn.execute(
            "INSERT OR IGNORE INTO features (id, name, code, icon, parent_id, url, sort, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (fid, name, code, icon, parent_id, url, sort, active),
        )
    # 更新已有功能菜单（处理种子数据变更）
    conn.execute("UPDATE features SET name='模型引擎', code='ai_model_mgr', icon='layui-icon-app', url='/admin/ai_model', sort=5, is_active=1 WHERE id=6")
    conn.execute("UPDATE features SET name='瞭望管理', code='lookout_mgr', icon='layui-icon-search', url='/admin/lookout/source', sort=6, is_active=1 WHERE id=7")
    conn.execute("UPDATE features SET name='技能管理', code='skill_mgr', icon='layui-icon-component', url='/admin/skill', sort=8, is_active=1 WHERE id=12")
    conn.execute("UPDATE features SET sort=7 WHERE id=5")
    # 清理测试数据
    conn.execute("DELETE FROM features WHERE code='1'")
    conn.commit()

    # 清理残留的 id=0 数据（之前首页功能误用 id=0 导致与 parent_id=0 冲突）
    conn.execute("DELETE FROM role_permissions WHERE feature_id=0")
    conn.execute("DELETE FROM features WHERE id=0")
    conn.commit()
    conn.close()

    # 为超级管理员赋予所有功能权限（包括新增的模型引擎）
    all_feature_ids = [f[0] for f in features]
    # 通过查询获取所有功能ID（含已存在的）
    with db.get_connection() as c:
        existing_ids = [r["id"] for r in c.execute("SELECT id FROM features").fetchall()]
    PermissionRepository.set_permissions(1, existing_ids)

    # 创建默认瞭望源（百度新闻）
    lookout_model = __import__('app.models.lookout', fromlist=['LookoutSourceRepository'])
    if not lookout_model.LookoutSourceRepository.get_all():
        lookout_model.LookoutSourceRepository.create(
            name="百度新闻",
            url_template="https://www.baidu.com/s?rtt=1&bsst=1&cl=undefined&tn=news&rsv_dl=ns_pc&word={keyword}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://www.baidu.com/",
            },
            item_selector="#content_left .result, .result",
            title_selector="h3 a",
            summary_selector=".c-abstract",
            time_selector=".c-color-gray",
            page_param="pn",
            page_size=10,
        )

    # 创建默认模型（如果没有模型）
    if not AiModelRepository.get_all():
        AiModelRepository.create(
            name="Qwen3.5 Flash",
            model_name="qwen3.5-flash",
            base_url="https://aigc-api.aitoolcore.com/api/v1",
            api_key="sk-aigc-d487f15bdd0f885f97939282b0a6a4f508666660",
            max_tokens=4096,
            temperature=0.7,
        )
        # 设置第一个模型为默认
        default_model = AiModelRepository.get_all()
        if default_model:
            AiModelRepository.set_default(default_model[0]["id"])

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
            (r"/auth/register", RegisterHandler),
            (r"/auth/roles", UserRolesApiHandler),
            # 用户侧首页
            (r"/user", UserIndexHandler),
            (r"/user/logout", UserLogoutHandler),
            # 后台主页
            (r"/admin", AdminHandler),
            (r"/admin/dashboard", DashboardPageHandler),
            (r"/admin/dashboard/data", DashboardDataHandler),
            # 用户管理
            (r"/admin/user", UserHandler),
            (r"/admin/user/list", UserListDataHandler),
            (r"/admin/user/add", UserAddHandler),
            (r"/admin/user/edit", UserEditHandler),
            (r"/admin/user/delete", UserDeleteHandler),
            (r"/admin/user/roles", UserRolesHandler),
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
            # AI模型管理
            (r"/admin/ai_model", AiModelHandler),
            (r"/admin/ai_model/list", AiModelListHandler),
            (r"/admin/ai_model/add", AiModelAddHandler),
            (r"/admin/ai_model/edit", AiModelEditHandler),
            (r"/admin/ai_model/delete", AiModelDeleteHandler),
            (r"/admin/ai_model/set_default", AiModelSetDefaultHandler),
            (r"/admin/ai_model/batch", AiModelBatchHandler),
            (r"/admin/ai_model/chat", AiModelChatHandler),
            (r"/admin/ai_model/chat_stream", AiModelChatStreamHandler),
            (r"/admin/ai_model/token_stats", AiModelTokenStatsHandler),
            # 瞭望管理
            (r"/admin/lookout/source", LookoutSourceHandler),
            (r"/admin/lookout/source/list", LookoutSourceListHandler),
            (r"/admin/lookout/source/add", LookoutSourceAddHandler),
            (r"/admin/lookout/source/edit", LookoutSourceEditHandler),
            (r"/admin/lookout/source/delete", LookoutSourceDeleteHandler),
            (r"/admin/lookout/source/get", LookoutSourceGetHandler),
            (r"/admin/lookout/source/active", LookoutSourceActiveHandler),
            (r"/admin/lookout/collect", LookoutCollectPageHandler),
            (r"/admin/lookout/collect/run", LookoutCollectRunHandler),
            (r"/admin/lookout/warehouse", LookoutWarehouseHandler),
            (r"/admin/lookout/warehouse/list", LookoutWarehouseListHandler),
            (r"/admin/lookout/warehouse/delete", LookoutWarehouseDeleteHandler),
            (r"/admin/lookout/export", LookoutExportHandler),
            # AI深度采集
            (r"/admin/lookout/deep", LookoutDeepHandler),
            (r"/admin/lookout/deep/list", LookoutDeepListHandler),
            (r"/admin/lookout/deep/start", LookoutDeepStartHandler),
            (r"/admin/lookout/deep/status", LookoutDeepStatusHandler),
            (r"/admin/lookout/deep/get", LookoutDeepGetHandler),
            (r"/admin/lookout/deep/delete", LookoutDeepDeleteHandler),
            (r"/admin/lookout/deep/analysis", LookoutDeepAnalysisHandler),
            (r"/admin/lookout/deep/sync", LookoutDeepSyncHandler),
            # 技能管理
            (r"/admin/skill", SkillHandler),
            (r"/admin/skill/list", SkillListHandler),
            (r"/admin/skill/add", SkillAddHandler),
            (r"/admin/skill/edit", SkillEditHandler),
            (r"/admin/skill/delete", SkillDeleteHandler),
            (r"/admin/skill/get", SkillGetHandler),
            (r"/admin/skill/detail", SkillDetailHandler),
            (r"/admin/skill/categories", SkillCategoriesHandler),
            (r"/admin/skill/call", SkillCallHandler),
            (r"/admin/skill/ai_create", SkillAICreateHandler),
            (r"/admin/skill/logs", SkillCallLogHandler),
            # 数字员工管理
            (r"/admin/employee", EmployeeHandler),
            (r"/admin/employee/list", EmployeeListHandler),
            (r"/admin/employee/add", EmployeeAddHandler),
            (r"/admin/employee/edit", EmployeeEditHandler),
            (r"/admin/employee/delete", EmployeeDeleteHandler),
            (r"/admin/employee/get", EmployeeGetHandler),
            (r"/admin/employee/detail", EmployeeDetailHandler),
            (r"/admin/employee/models", EmployeeModelsHandler),
            (r"/admin/employee/skills", EmployeeSkillsHandler),
            (r"/admin/employee/call", EmployeeCallHandler),
            (r"/admin/employee/logs", EmployeeCallLogHandler),
            (r"/admin/employee/generate_prompt", EmployeeGeneratePromptHandler),
            # 会话管理
            (r"/admin/conversation", ConversationHandler),
            (r"/admin/conversation/list", ConversationListHandler),
            (r"/admin/conversation/add", ConversationAddHandler),
            (r"/admin/conversation/edit", ConversationEditHandler),
            (r"/admin/conversation/delete", ConversationDeleteHandler),
            (r"/admin/conversation/get", ConversationGetHandler),
            (r"/admin/conversation/detail", ConversationDetailHandler),
            # 消息管理
            (r"/admin/conversation/messages", MessageListHandler),
            (r"/admin/conversation/message/add", MessageAddHandler),
            (r"/admin/conversation/message/analyze", MessageAnalyzeHandler),
            (r"/admin/conversation/message/analyze_all", MessageAnalyzeAllHandler),
            # 违规监控
            (r"/admin/conversation/violations", ViolationListHandler),
            (r"/admin/conversation/violation/update", ViolationUpdateHandler),
            (r"/admin/conversation/violation/monitor", ViolationMonitorPageHandler),
            (r"/admin/conversation/check_all", ConversationCheckAllHandler),
            # 对话管理
            (r"/admin/dialogue", DialogueHandler),
            (r"/admin/dialogue/list", DialogueListHandler),
            (r"/admin/dialogue/get", DialogueGetHandler),
            (r"/admin/dialogue/add", DialogueAddHandler),
            (r"/admin/dialogue/edit", DialogueEditHandler),
            (r"/admin/dialogue/delete", DialogueDeleteHandler),
            (r"/admin/dialogue/detail", DialogueDetailHandler),
            (r"/admin/dialogue/models", DialogueModelsHandler),
            (r"/admin/dialogue/call", DialogueCallHandler),
            (r"/admin/dialogue/logs", DialogueCallLogHandler),
            # 数智大屏
            (r"/admin/datascreen", DatascreenHandler),
            (r"/admin/datascreen/list", DatascreenListHandler),
            (r"/admin/datascreen/get", DatascreenGetHandler),
            (r"/admin/datascreen/add", DatascreenAddHandler),
            (r"/admin/datascreen/edit", DatascreenEditHandler),
            (r"/admin/datascreen/delete", DatascreenDeleteHandler),
            (r"/admin/datascreen/view", DatascreenViewHandler),
            (r"/admin/datascreen/render", DatascreenRenderHandler),
            (r"/admin/datascreen/export", DatascreenExportHandler),
            (r"/admin/datascreen/logs", DatascreenCallLogHandler),
            (r"/admin/datascreen/preview", DatascreenPreviewHandler),
            # 系统设置
            (r"/admin/settings", SettingsHandler),
            (r"/admin/settings/config", SettingsConfigHandler),
            (r"/admin/settings/logs", SettingsLogsHandler),
            (r"/admin/settings/monitor", SettingsMonitorHandler),
            (r"/admin/settings/analysis", SettingsAnalysisHandler),
            (r"/admin/settings/monitor/data", SettingsMonitorDataHandler),
            # 用户侧对话功能
            (r"/user/chat", UserChatHandler),
            (r"/user/chat/employee", UserChatEmployeeHandler),
            (r"/user/friends/list", FriendListHandler),
            (r"/user/friends/search", FriendSearchHandler),
            (r"/user/friends/add", FriendAddHandler),
            (r"/user/friends/remove", FriendRemoveHandler),
            (r"/user/friends/requests", FriendRequestHandler),
            (r"/user/friends/accept", FriendRequestAcceptHandler),
            (r"/user/friends/reject", FriendRequestRejectHandler),
            (r"/user/groups/create", GroupCreateHandler),
            (r"/user/groups/list", GroupListHandler),
            (r"/user/groups/search", GroupSearchHandler),
            (r"/user/groups/join", GroupJoinHandler),
            (r"/user/groups/members", GroupMembersHandler),
            (r"/user/groups/invite", GroupInviteHandler),
            (r"/user/groups/invite_employee", GroupInviteEmployeeHandler),
            (r"/user/groups/employees", GroupEmployeeListHandler),
            (r"/user/group/message/send", GroupMessageSendHandler),
            (r"/user/group/messages", GroupMessageListHandler),
            (r"/user/employees/list", UserEmployeeListHandler),
            (r"/user/chat/export", ChatExportHandler),
            (r"/user/chat/analyze", ChatAnalyzeHandler),
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

class DebugMenuHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        from app.models.user import UserRepository
        from app.models.permission import PermissionRepository
        from app.models.feature import FeatureRepository
        
        username = self.current_user
        user = UserRepository.get_user_by_username(username)
        role_id = user.get('role_id', 0) if user else 0
        perms = PermissionRepository.get_permissions_by_role(role_id)
        
        all_features = FeatureRepository.get_all()
        active_features = [f for f in all_features if f['is_active'] == 1 and f['url']]
        accessible = [f for f in active_features if f['id'] in perms]
        
        result = {
            'username': username,
            'role_id': role_id,
            'permissions': perms,
            'all_features': [f['id'] for f in all_features],
            'active_features': [f['id'] for f in active_features],
            'accessible': [f['id'] for f in accessible],
            'accessible_names': [(f['id'], f['name']) for f in accessible]
        }
        self.write(json.dumps(result))

application.add_handlers(r'.*', [
    (r'/admin/debug/menu', DebugMenuHandler),
])
