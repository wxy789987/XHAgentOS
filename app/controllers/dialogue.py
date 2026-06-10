# 对话管理控制层
import json
import logging
import traceback
import time
import tornado.web
from app.controllers.base import BaseHandler
from app.models.dialogue import DialogueRepository, DialogueCallLogRepository
from app.models.ai_model import AiModelRepository

logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = True
try:
    from openai import OpenAI
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None


class DialogueHandler(BaseHandler):
    """对话管理页面"""
    @tornado.web.authenticated
    def get(self):
        username = self.current_user if self.current_user else ""
        self.render("dialogue_list.html", title="对话管理", username=username)


class DialogueListHandler(BaseHandler):
    """对话记录列表API"""
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 10))
        keyword = self.get_argument("keyword", "")
        data = DialogueRepository.get_page(page, page_size, keyword)
        self.write(data)


class DialogueGetHandler(BaseHandler):
    """获取单个对话记录详情"""
    @tornado.web.authenticated
    def get(self):
        dialogue_id = int(self.get_argument("id", 0))
        d = DialogueRepository.get_by_id(dialogue_id)
        if not d:
            self.write({"code": 1, "msg": "对话记录不存在"})
            return
        if d.get("model_id"):
            model = AiModelRepository.get_by_id(d["model_id"])
            d["model_name"] = model["name"] if model else "未知模型"
        else:
            d["model_name"] = "未选择"
        self.write({"code": 0, "data": d})


class DialogueAddHandler(BaseHandler):
    """新增对话记录"""
    @tornado.web.authenticated
    def post(self):
        name = self.get_argument("name", "").strip()
        content = self.get_argument("content", "").strip()
        description = self.get_argument("description", "").strip()
        model_id = int(self.get_argument("model_id", 0))
        system_prompt = self.get_argument("system_prompt", "").strip()

        if not name:
            self.write({"code": 1, "msg": "对话记录名称不能为空"})
            return
        if not content:
            self.write({"code": 1, "msg": "对话记录内容不能为空"})
            return

        username = self.current_user
        user = self.get_current_user_info()
        created_by = user.get("id", 0) if user else 0

        dialogue_id = DialogueRepository.create(name, content, description, model_id, system_prompt, created_by)
        self.write({"code": 0, "msg": "新增成功", "id": dialogue_id})


class DialogueEditHandler(BaseHandler):
    """编辑对话记录"""
    @tornado.web.authenticated
    def post(self):
        dialogue_id = int(self.get_argument("id", 0))
        name = self.get_argument("name", "").strip()
        content = self.get_argument("content", "").strip()
        description = self.get_argument("description", "").strip()
        model_id = int(self.get_argument("model_id", 0))
        system_prompt = self.get_argument("system_prompt", "").strip()
        is_active = int(self.get_argument("is_active", 1))

        if not dialogue_id:
            self.write({"code": 1, "msg": "参数错误"})
            return

        DialogueRepository.update(dialogue_id, name, content, description, model_id, system_prompt, is_active)
        self.write({"code": 0, "msg": "更新成功"})


class DialogueDeleteHandler(BaseHandler):
    """删除对话记录"""
    @tornado.web.authenticated
    def post(self):
        dialogue_id = int(self.get_argument("id", 0))
        DialogueRepository.delete(dialogue_id)
        self.write({"code": 0, "msg": "删除成功"})


class DialogueDetailHandler(BaseHandler):
    """对话详情页面"""
    @tornado.web.authenticated
    def get(self):
        dialogue_id = self.get_argument("id", 0)
        username = self.current_user if self.current_user else ""
        self.render("dialogue_detail.html", title="对话详情", username=username, dialogue_id=dialogue_id)


class DialogueModelsHandler(BaseHandler):
    """获取所有可用AI模型"""
    @tornado.web.authenticated
    def get(self):
        models = AiModelRepository.get_all()
        self.write({"code": 0, "data": models})


class DialogueCallHandler(BaseHandler):
    """执行对话调用（测试/调用）"""
    @tornado.web.authenticated
    def post(self):
        dialogue_id = int(self.get_argument("dialogue_id", 0))
        input_text = self.get_argument("input_text", "").strip()

        d = DialogueRepository.get_by_id(dialogue_id)
        if not d:
            self.write({"code": 1, "msg": "对话记录不存在"})
            return

        model_id = d.get("model_id", 0)
        if not model_id:
            # 没有指定模型，使用默认模型
            models = AiModelRepository.get_all()
            model = next((m for m in models if m["is_default"]), models[0] if models else None)
        else:
            model = AiModelRepository.get_by_id(model_id)

        if not model:
            self.write({"code": 1, "msg": "没有可用的AI模型，请先在模型引擎中配置"})
            return

        if not OPENAI_AVAILABLE or OpenAI is None:
            self.write({"code": 1, "msg": "OpenAI SDK未安装"})
            return

        # 构建消息
        system_prompt = d.get("system_prompt", "").strip()
        dialogue_content = d.get("content", "")
        user_input = input_text if input_text else f"请根据以下对话内容回应：\n{dialogue_content}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})

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

            output_data = {"reply": reply, "model": model["name"]}
            DialogueCallLogRepository.create(dialogue_id, {"input": user_input}, output_data, "success", duration)
            self.write({"code": 0, "msg": "调用成功", "data": output_data})

        except Exception as e:
            duration = int((time.time() - start) * 1000)
            err_msg = str(e)
            logger.error(f"对话调用异常: dialogue_id={dialogue_id}, error={traceback.format_exc()}")
            DialogueCallLogRepository.create(dialogue_id, {"input": user_input}, err_msg, "failed", duration, err_msg)
            self.write({"code": 1, "msg": f"调用失败: {err_msg}"})


class DialogueCallLogHandler(BaseHandler):
    """调用记录API"""
    @tornado.web.authenticated
    def get(self):
        dialogue_id = self.get_argument("dialogue_id", "")
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 20))
        did = int(dialogue_id) if dialogue_id else None
        data = DialogueCallLogRepository.get_page(page, page_size, did)
        self.write(data)
