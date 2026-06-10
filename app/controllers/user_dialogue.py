# 用户侧对话功能 - 控制层
from typing import Optional, List
import json
import time
import re
import logging
import traceback
import threading
import tornado.web
import tornado.ioloop
from app.controllers.base import BaseHandler
from app.models.user_dialogue import FriendRepository, FriendRequestRepository, GroupRepository, GroupMessageRepository
from app.models.ai_model import AiModelRepository
from app.models.employee import EmployeeRepository, EmployeeCallLogRepository

logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = True
try:
    from openai import OpenAI
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None


class UserChatHandler(BaseHandler):
    """用户对话主页"""
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_info()
        friends = FriendRepository.get_friends(user["id"])
        groups = GroupRepository.get_my_groups(user["id"])
        users_list = FriendRepository.search_users("")
        employees = EmployeeRepository.get_all()
        self.render("user_chat.html", title="对话",
                     username=user["username"],
                     user_id=user["id"],
                     friends=friends,
                     groups=groups,
                     users=users_list,
                     employees=employees)


class UserChatEmployeeHandler(BaseHandler):
    """与数字员工对话"""
    @tornado.web.authenticated
    def post(self):
        employee_id = int(self.get_argument("employee_id", 0))
        message = self.get_argument("message", "").strip()
        history = json.loads(self.get_argument("history", "[]"))

        employee = EmployeeRepository.get_by_id(employee_id)
        if not employee:
            self.write({"code": 1, "msg": "数字员工不存在"})
            return

        model_id = employee.get("model_id", 0)
        if not model_id:
            models = AiModelRepository.get_all()
            model = next((m for m in models if m["is_default"]), models[0] if models else None)
        else:
            model = AiModelRepository.get_by_id(model_id)

        if not model:
            self.write({"code": 1, "msg": "没有可用的AI模型"})
            return

        if not OPENAI_AVAILABLE:
            self.write({"code": 1, "msg": "OpenAI SDK未安装"})
            return

        system_prompt = employee.get("system_prompt", "")
        if not system_prompt:
            system_prompt = f"你是{employee['name']}，一个智能数字员工。请友好、专业地回答用户的问题。"

        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-10:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": message})

        start = time.time()
        try:
            import httpx
            client = OpenAI(
                api_key=model["api_key"],
                base_url=model["base_url"],
                http_client=httpx.Client(timeout=120.0),
            )
            response = client.chat.completions.create(
                model=model["model_name"],
                messages=messages,
                max_tokens=model.get("max_tokens", 4096),
                temperature=model.get("temperature", 0.7),
            )
            reply = response.choices[0].message.content
            duration = int((time.time() - start) * 1000)

            output_data = {"reply": reply, "employee": employee["name"]}
            EmployeeCallLogRepository.create(employee_id, {"input": message, "history": history}, output_data, "success", duration)

            self.write({"code": 0, "data": {"reply": reply, "employee_name": employee["name"]}})
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            err_msg = str(e)
            logger.error(f"员工对话异常: {traceback.format_exc()}")
            EmployeeCallLogRepository.create(employee_id, {"input": message}, err_msg, "failed", duration, err_msg)
            self.write({"code": 1, "msg": f"调用失败: {err_msg}"})


class FriendListHandler(BaseHandler):
    """好友列表"""
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_info()
        friends = FriendRepository.get_friends(user["id"])
        self.write({"code": 0, "data": friends})


class FriendSearchHandler(BaseHandler):
    """搜索用户"""
    @tornado.web.authenticated
    def get(self):
        keyword = self.get_argument("keyword", "")
        user = self.get_current_user_info()
        users = FriendRepository.search_users(keyword)
        users = [u for u in users if u["id"] != user["id"]]
        self.write({"code": 0, "data": users})


class FriendAddHandler(BaseHandler):
    """发送好友请求"""
    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_info()
        friend_id = int(self.get_argument("friend_id", 0))
        message = self.get_argument("message", "")
        if friend_id == user["id"]:
            self.write({"code": 1, "msg": "不能添加自己为好友"})
            return
        FriendRepository.add_friend(user["id"], friend_id)
        self.write({"code": 0, "msg": "添加成功"})


class FriendRemoveHandler(BaseHandler):
    """删除好友"""
    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_info()
        friend_id = int(self.get_argument("friend_id", 0))
        FriendRepository.remove_friend(user["id"], friend_id)
        self.write({"code": 0, "msg": "删除成功"})


class FriendRequestHandler(BaseHandler):
    """好友请求管理页面"""
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_info()
        requests = FriendRequestRepository.get_pending_requests(user["id"])
        self.write({"code": 0, "data": requests})


class FriendRequestAcceptHandler(BaseHandler):
    """接受好友请求"""
    @tornado.web.authenticated
    def post(self):
        request_id = int(self.get_argument("request_id", 0))
        FriendRequestRepository.accept_request(request_id)
        self.write({"code": 0, "msg": "已接受"})


class FriendRequestRejectHandler(BaseHandler):
    """拒绝好友请求"""
    @tornado.web.authenticated
    def post(self):
        request_id = int(self.get_argument("request_id", 0))
        FriendRequestRepository.reject_request(request_id)
        self.write({"code": 0, "msg": "已拒绝"})


class GroupCreateHandler(BaseHandler):
    """创建群组"""
    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_info()
        name = self.get_argument("name", "").strip()
        description = self.get_argument("description", "").strip()
        if not name:
            self.write({"code": 1, "msg": "群组名称不能为空"})
            return
        group_id = GroupRepository.create(name, description, user["id"])
        self.write({"code": 0, "msg": "创建成功", "group_id": group_id})


class GroupListHandler(BaseHandler):
    """我的群组列表"""
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_info()
        groups = GroupRepository.get_my_groups(user["id"])
        self.write({"code": 0, "data": groups})


class GroupSearchHandler(BaseHandler):
    """搜索群组"""
    @tornado.web.authenticated
    def get(self):
        keyword = self.get_argument("keyword", "")
        groups = GroupRepository.search_groups(keyword)
        self.write({"code": 0, "data": groups})


class GroupJoinHandler(BaseHandler):
    """加入群组"""
    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_info()
        group_id = int(self.get_argument("group_id", 0))
        GroupRepository.join_group(group_id, user["id"])
        self.write({"code": 0, "msg": "已加入群组"})


class GroupMembersHandler(BaseHandler):
    """群组成员列表"""
    @tornado.web.authenticated
    def get(self):
        group_id = int(self.get_argument("group_id", 0))
        members = GroupRepository.get_members(group_id)
        self.write({"code": 0, "data": members})


class GroupInviteHandler(BaseHandler):
    """邀请成员加入群组"""
    @tornado.web.authenticated
    def post(self):
        group_id = int(self.get_argument("group_id", 0))
        user_id = int(self.get_argument("user_id", 0))
        GroupRepository.invite_member(group_id, user_id)
        self.write({"code": 0, "msg": "已邀请"})


class GroupInviteEmployeeHandler(BaseHandler):
    """添加数字员工到群组"""
    @tornado.web.authenticated
    def post(self):
        group_id = int(self.get_argument("group_id", 0))
        employee_id = int(self.get_argument("employee_id", 0))
        GroupRepository.invite_employee(group_id, employee_id)
        self.write({"code": 0, "msg": "已添加"})


class GroupEmployeeListHandler(BaseHandler):
    """获取群组的数字员工列表"""
    @tornado.web.authenticated
    def get(self):
        group_id = int(self.get_argument("group_id", 0))
        employees = GroupRepository.get_employees(group_id)
        self.write({"code": 0, "data": employees})


class GroupMessageSendHandler(BaseHandler):
    """发送群消息"""
    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_info()
        group_id = int(self.get_argument("group_id", 0))
        content = self.get_argument("content", "").strip()
        if not content:
            self.write({"code": 1, "msg": "消息不能为空"})
            return
        msg_id = GroupMessageRepository.send(group_id, user["id"], content, "text")

        # 异步触发群组中数字员工的自动回复（通过 IOLoop 延迟执行，不阻塞响应）
        try:
            employees = GroupRepository.get_employees(group_id)
            mentioned_emps = self._get_mentioned_employees(content, employees)
            if mentioned_emps is None:
                targets = employees
            elif mentioned_emps:
                targets = mentioned_emps
            else:
                targets = []

            if targets:
                # 在线程中异步执行，不阻塞当前请求
                tornado.ioloop.IOLoop.current().add_callback(
                    self._async_trigger_replies, group_id, targets, content, user["username"]
                )
        except Exception as e:
            logger.error(f"准备触发数字员工回复异常: {e}")

        self.write({"code": 0, "msg": "发送成功", "message_id": msg_id})

    async def _async_trigger_replies(self, group_id, employees, content, username):
        """异步触发数字员工回复，不阻塞主线程"""
        for emp in employees:
            self._trigger_employee_reply(group_id, emp, content, username)

    @staticmethod
    def _get_mentioned_employees(content: str, employees: List[dict]) -> Optional[List[dict]]:
        """解析消息内容中的@提及，返回匹配的数字员工列表
        返回值: None=无@符号，[] = 有@但没匹配到员工，[...] = 匹配到的员工列表
        """
        if not content or not employees:
            return None
        # 匹配 @员工名称 模式（中英文名称，直到空格或标点）
        pattern = r'@([^\s,，。！？、；;：]+)'
        matches = re.findall(pattern, content)
        if not matches:
            return None  # 没有@符号
        mentioned = []
        for emp in employees:
            emp_name = emp.get("name", "")
            for mention in matches:
                if mention == emp_name:
                    mentioned.append(emp)
                    break
        return mentioned  # 返回[]表示有@但没匹配到

    def _call_ai_model(self, model, system_prompt, user_message):
        """调用AI模型获取回复"""
        import httpx
        from openai import OpenAI
        client = OpenAI(
            api_key=model["api_key"],
            base_url=model["base_url"],
            http_client=httpx.Client(timeout=60.0),
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        response = client.chat.completions.create(
            model=model["model_name"],
            messages=messages,
            max_tokens=model.get("max_tokens", 2048),
            temperature=model.get("temperature", 0.7),
        )
        return response.choices[0].message.content

    def _trigger_employee_reply(self, group_id, employee, user_message, username):
        """触发单个数字员工回复群消息"""
        try:
            model_id = employee.get("model_id", 0)
            if not model_id:
                models = AiModelRepository.get_all()
                model = next((m for m in models if m["is_default"]), models[0] if models else None)
            else:
                model = AiModelRepository.get_by_id(model_id)

            if not model or not OPENAI_AVAILABLE:
                return

            system_prompt = employee.get("system_prompt", "")
            if not system_prompt:
                system_prompt = f"你是{employee['name']}，一个智能数字员工。请在群聊中以你的身份友好、专业地回答用户的问题。"

            full_message = f"用户{username}说: {user_message}"
            reply = self._call_ai_model(model, system_prompt, full_message)
            if reply:
                # 以数字员工身份发送回复到群组
                GroupMessageRepository.send(
                    group_id=group_id,
                    user_id=0,  # 0表示数字员工
                    content=f"@{employee['name']}: {reply}",
                    msg_type="employee_reply"
                )
                # 记录调用日志
                EmployeeCallLogRepository.create(
                    employee["id"],
                    {"input": full_message, "group_id": group_id},
                    {"reply": reply, "employee": employee["name"]},
                    "success",
                    0
                )
        except Exception as e:
            logger.error(f"数字员工[{employee.get('name','')}]回复异常: {traceback.format_exc()}")


class GroupMessageListHandler(BaseHandler):
    """群消息列表"""
    @tornado.web.authenticated
    def get(self):
        group_id = int(self.get_argument("group_id", 0))
        page = int(self.get_argument("page", 1))
        messages = GroupMessageRepository.get_messages(group_id, page)
        self.write({"code": 0, "data": messages})


class EmployeeListHandler(BaseHandler):
    """可用的数字员工列表"""
    @tornado.web.authenticated
    def get(self):
        employees = EmployeeRepository.get_all()
        self.write({"code": 0, "data": employees})


class ChatExportHandler(BaseHandler):
    """导出对话记录"""
    @tornado.web.authenticated
    def get(self):
        employee_id = self.get_argument("employee_id", "")
        logs = []
        if employee_id:
            data = EmployeeCallLogRepository.get_page(1, 1000, int(employee_id))
            logs = data.get("items", [])

        lines = ["对话记录导出", "=" * 40, f"导出时间: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
        for log in logs:
            try:
                inp = json.loads(log.get("input_data", "{}"))
                out = json.loads(log.get("output_data", "{}"))
                lines.append(f"[{log['created_at']}]")
                lines.append(f"问: {inp.get('input', str(inp))}")
                lines.append(f"答: {out.get('reply', str(out))}")
                lines.append("")
            except:
                lines.append(f"[{log['created_at']}] {log.get('input_data', '')}")

        content = "\n".join(lines)
        self.set_header("Content-Type", "text/plain; charset=utf-8")
        self.set_header("Content-Disposition", "attachment; filename=chat_export.txt")
        self.write(content)


class ChatAnalyzeHandler(BaseHandler):
    """分析对话记录（简单统计）"""
    @tornado.web.authenticated
    def get(self):
        employee_id = self.get_argument("employee_id", "")
        data = EmployeeCallLogRepository.get_page(1, 1000, int(employee_id) if employee_id else None)
        logs = data.get("items", [])

        total = len(logs)
        success = sum(1 for l in logs if l.get("status") == "success")
        failed = total - success
        avg_duration = sum(l.get("duration_ms", 0) for l in logs) / total if total > 0 else 0

        self.write({"code": 0, "data": {
            "total": total,
            "success": success,
            "failed": failed,
            "avg_duration_ms": round(avg_duration, 1),
        }})
