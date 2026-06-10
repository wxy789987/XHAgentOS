# 数字员工管理控制层
import json
import logging
import traceback
import tornado.web
from app.controllers.base import BaseHandler
from app.models.employee import EmployeeRepository, EmployeeCallLogRepository
from app.models.skill import SkillRepository
from app.models.ai_model import AiModelRepository

logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = True
try:
    from openai import OpenAI
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

import httpx


def generate_system_prompt(name, description, skill_ids, model_id):
    """根据技能列表自动生成系统提示词"""
    parts = [f"你是数字员工「{name}」，请根据用户的提问提供帮助。"]
    if description:
        parts.append(f"\n\n你的职责范围：{description}")

    if skill_ids:
        skills = []
        for sid in skill_ids:
            skill = SkillRepository.get_by_id(sid)
            if skill:
                skills.append(skill)
        if skills:
            parts.append("\n\n你可以使用以下技能来完成任务：")
            for i, s in enumerate(skills, 1):
                s_desc = s.get("description", "") or s.get("name", "")
                s_type = "API调用" if s.get("skill_type") == "api" else "AI处理"
                parts.append(f"\n{i}. {s['name']}（{s_type}）：{s_desc}")

            parts.append("\n\n当用户的问题需要使用某个技能时，请调用对应的技能来获取数据，不要凭空编造信息。")

    if model_id:
        model = AiModelRepository.get_by_id(model_id)
        if model:
            parts.append(f"\n\n你运行在AI模型「{model['name']}」上。")

    return "".join(parts)


class EmployeeHandler(BaseHandler):
    """数字员工管理页面"""
    @tornado.web.authenticated
    def get(self):
        username = self.current_user if self.current_user else ""
        self.render("employee_list.html", title="数字员工管理", username=username)


class EmployeeListHandler(BaseHandler):
    """数字员工列表API"""
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 10))
        keyword = self.get_argument("keyword", "")
        data = EmployeeRepository.get_page(page, page_size, keyword)
        # 补充模型名称和技能名称
        items = data.get("items", [])
        for item in items:
            model_id = item.get("model_id", 0)
            if model_id:
                model = AiModelRepository.get_by_id(model_id)
                item["model_name"] = model["name"] if model else "未知模型"
            else:
                item["model_name"] = "未选择"
            skill_ids = []
            try:
                skill_ids = json.loads(item.get("skill_ids", "[]"))
            except (json.JSONDecodeError, TypeError):
                pass
            item["skill_count"] = len(skill_ids)
        data["items"] = items
        self.write(data)


class EmployeeAddHandler(BaseHandler):
    """新增数字员工"""
    @tornado.web.authenticated
    def post(self):
        name = self.get_argument("name", "").strip()
        model_id = int(self.get_argument("model_id", 0))
        skill_ids_raw = self.get_argument("skill_ids", "[]")
        description = self.get_argument("description", "").strip()
        system_prompt = self.get_argument("system_prompt", "").strip()
        auto_generate = self.get_argument("auto_generate", "0")

        if not name:
            self.write({"code": 1, "msg": "数字员工名称不能为空"})
            return

        try:
            skill_ids = json.loads(skill_ids_raw) if isinstance(skill_ids_raw, str) else skill_ids_raw
        except json.JSONDecodeError:
            skill_ids = []

        # 自动生成系统提示词
        if auto_generate == "1" and not system_prompt:
            system_prompt = generate_system_prompt(name, description, skill_ids, model_id)

        username = self.current_user
        user = self.get_current_user_info()
        created_by = user.get("id", 0) if user else 0

        employee_id = EmployeeRepository.create(name, model_id, skill_ids, description, system_prompt, created_by)
        self.write({"code": 0, "msg": "新增成功", "id": employee_id})


class EmployeeEditHandler(BaseHandler):
    """编辑数字员工"""
    @tornado.web.authenticated
    def post(self):
        employee_id = int(self.get_argument("id", 0))
        name = self.get_argument("name", "").strip()
        model_id = int(self.get_argument("model_id", 0))
        skill_ids_raw = self.get_argument("skill_ids", "[]")
        description = self.get_argument("description", "").strip()
        system_prompt = self.get_argument("system_prompt", "").strip()
        is_active = int(self.get_argument("is_active", 1))

        if not employee_id:
            self.write({"code": 1, "msg": "参数错误"})
            return

        try:
            skill_ids = json.loads(skill_ids_raw) if isinstance(skill_ids_raw, str) else skill_ids_raw
        except json.JSONDecodeError:
            skill_ids = []

        EmployeeRepository.update(employee_id, name, model_id, skill_ids, description, system_prompt, is_active)
        self.write({"code": 0, "msg": "更新成功"})


class EmployeeDeleteHandler(BaseHandler):
    """删除数字员工"""
    @tornado.web.authenticated
    def post(self):
        employee_id = int(self.get_argument("id", 0))
        EmployeeRepository.delete(employee_id)
        self.write({"code": 0, "msg": "删除成功"})


class EmployeeGetHandler(BaseHandler):
    """获取单个数字员工详情"""
    @tornado.web.authenticated
    def get(self):
        employee_id = int(self.get_argument("id", 0))
        if not employee_id:
            self.write({"code": 1, "msg": "参数错误"})
            return
        emp = EmployeeRepository.get_by_id(employee_id)
        if not emp:
            self.write({"code": 1, "msg": "数字员工不存在"})
            return
        # 解析技能列表
        try:
            emp["skill_ids"] = json.loads(emp.get("skill_ids", "[]"))
        except (json.JSONDecodeError, TypeError):
            emp["skill_ids"] = []
        # 补充模型名称
        if emp.get("model_id"):
            model = AiModelRepository.get_by_id(emp["model_id"])
            emp["model_name"] = model["name"] if model else "未知模型"
        else:
            emp["model_name"] = "未选择"
        self.write({"code": 0, "data": emp})


class EmployeeDetailHandler(BaseHandler):
    """数字员工详情页面"""
    @tornado.web.authenticated
    def get(self):
        employee_id = self.get_argument("id", 0)
        username = self.current_user if self.current_user else ""
        self.render("employee_detail.html", title="数字员工详情", username=username, employee_id=employee_id)


class EmployeeModelsHandler(BaseHandler):
    """获取所有可用AI模型"""
    @tornado.web.authenticated
    def get(self):
        models = AiModelRepository.get_all()
        self.write({"code": 0, "data": models})


class EmployeeSkillsHandler(BaseHandler):
    """获取所有可用技能"""
    @tornado.web.authenticated
    def get(self):
        skills = SkillRepository.get_all()
        self.write({"code": 0, "data": skills})


class EmployeeCallHandler(BaseHandler):
    """执行数字员工调用（测试/调用）"""
    @tornado.web.authenticated
    def post(self):
        employee_id = int(self.get_argument("employee_id", 0))
        input_raw = self.get_argument("input_data", "{}")

        emp = EmployeeRepository.get_by_id(employee_id)
        if not emp:
            self.write({"code": 1, "msg": "数字员工不存在"})
            return

        try:
            input_data = json.loads(input_raw) if isinstance(input_raw, str) else input_raw
        except json.JSONDecodeError:
            input_data = {"text": input_raw}

        import time
        start_time = time.time()

        try:
            result = self._call_employee(emp, input_data)
            duration = int((time.time() - start_time) * 1000)
            if result.get("code") == 0:
                EmployeeCallLogRepository.create(employee_id, input_data, result.get("data", {}), "success", duration)
                self.write(result)
            else:
                EmployeeCallLogRepository.create(employee_id, input_data, result.get("msg", ""), "failed", duration, result.get("msg", ""))
                self.write(result)
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            err_msg = str(e)
            logger.error(f"数字员工调用异常: employee_id={employee_id}, error={traceback.format_exc()}")
            EmployeeCallLogRepository.create(employee_id, input_data, err_msg, "failed", duration, err_msg)
            self.write({"code": 1, "msg": f"调用失败: {err_msg}"})

    def _call_employee(self, emp, input_data):
        """调用数字员工（通过AI模型）"""
        model_id = emp.get("model_id", 0)
        if not model_id:
            return {"code": 1, "msg": "数字员工未配置AI模型，请先选择模型"}

        model = AiModelRepository.get_by_id(model_id)
        if not model:
            return {"code": 1, "msg": "关联的AI模型不存在或已被删除"}

        if not OPENAI_AVAILABLE or OpenAI is None:
            return {"code": 1, "msg": "OpenAI SDK未安装"}

        system_prompt = emp.get("system_prompt", "") or f"你是数字员工「{emp['name']}」，请根据用户的问题提供帮助。"

        # 获取用户的输入文本
        text = input_data.get("text", "") or input_data.get("input", "") or json.dumps(input_data, ensure_ascii=False)

        # 构建消息
        messages = [{"role": "system", "content": system_prompt}]

        # 如果有关联技能，将技能信息也注入到系统提示中
        try:
            skill_ids = json.loads(emp.get("skill_ids", "[]"))
        except (json.JSONDecodeError, TypeError):
            skill_ids = []

        if skill_ids:
            skill_details = []
            for sid in skill_ids:
                skill = SkillRepository.get_by_id(sid)
                if skill and skill.get("is_active"):
                    skill_details.append(skill)
            if skill_details:
                skill_context = "\n\n你可以使用的技能："
                for s in skill_details:
                    config = s.get("config", {})
                    if isinstance(config, str):
                        try:
                            config = json.loads(config)
                        except json.JSONDecodeError:
                            config = {}
                    url_info = f"（接口：{config.get('url', 'N/A')}）" if s.get("skill_type") == "api" else ""
                    skill_context += f"\n- {s['name']}{url_info}：{s.get('description', '') or s['name']}"
                skill_context += "\n\n当需要获取实时数据时，请调用对应技能。如果无法调用技能或技能不可用，请如实告知用户。"
                # 将技能上下文追加到第一条系统消息
                messages[0]["content"] += skill_context

        messages.append({"role": "user", "content": text})

        try:
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
            return {"code": 0, "msg": "调用成功", "data": {"reply": reply, "model": model["name"]}}

        except Exception as e:
            return {"code": 1, "msg": f"AI调用失败: {str(e)}"}


class EmployeeCallLogHandler(BaseHandler):
    """调用记录API"""
    @tornado.web.authenticated
    def get(self):
        employee_id = self.get_argument("employee_id", "")
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 20))
        eid = int(employee_id) if employee_id else None
        data = EmployeeCallLogRepository.get_page(page, page_size, eid)
        self.write(data)


class EmployeeGeneratePromptHandler(BaseHandler):
    """自动生成系统提示词"""
    @tornado.web.authenticated
    def post(self):
        name = self.get_argument("name", "").strip()
        description = self.get_argument("description", "").strip()
        skill_ids_raw = self.get_argument("skill_ids", "[]")
        model_id = int(self.get_argument("model_id", 0))

        try:
            skill_ids = json.loads(skill_ids_raw) if isinstance(skill_ids_raw, str) else skill_ids_raw
        except json.JSONDecodeError:
            skill_ids = []

        system_prompt = generate_system_prompt(name, description, skill_ids, model_id)
        self.write({"code": 0, "data": {"system_prompt": system_prompt}})
