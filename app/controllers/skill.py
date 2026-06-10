# 技能管理控制层
import json
import logging
import traceback
import tornado.web
from app.controllers.base import BaseHandler
from app.models.skill import SkillRepository, SkillCallLogRepository
from app.models.ai_model import AiModelRepository

logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = True
try:
    from openai import OpenAI
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

import httpx


class SkillHandler(BaseHandler):
    """技能管理页面"""
    @tornado.web.authenticated
    def get(self):
        username = self.current_user if self.current_user else ""
        self.render("skill_list.html", title="技能管理", username=username)


class SkillListHandler(BaseHandler):
    """技能列表API"""
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 10))
        keyword = self.get_argument("keyword", "")
        skill_type = self.get_argument("skill_type", "")
        category = self.get_argument("category", "")
        data = SkillRepository.get_page(page, page_size, keyword, skill_type, category)
        self.write(data)


class SkillAddHandler(BaseHandler):
    """新增技能"""
    @tornado.web.authenticated
    def post(self):
        name = self.get_argument("name", "").strip()
        description = self.get_argument("description", "").strip()
        skill_type = self.get_argument("skill_type", "api")
        category = self.get_argument("category", "").strip()
        config_raw = self.get_argument("config", "{}")
        parameters_raw = self.get_argument("parameters", "[]")

        if not name:
            self.write({"code": 1, "msg": "技能名称不能为空"})
            return

        try:
            config = json.loads(config_raw) if isinstance(config_raw, str) else config_raw
        except json.JSONDecodeError:
            config = {}
        try:
            parameters = json.loads(parameters_raw) if isinstance(parameters_raw, str) else parameters_raw
        except json.JSONDecodeError:
            parameters = []

        username = self.current_user
        user = self.get_current_user_info()
        created_by = user.get("id", 0) if user else 0

        skill_id = SkillRepository.create(name, description, skill_type, category, config, parameters, created_by)
        self.write({"code": 0, "msg": "新增成功", "id": skill_id})


class SkillEditHandler(BaseHandler):
    """编辑技能"""
    @tornado.web.authenticated
    def post(self):
        skill_id = int(self.get_argument("id", 0))
        name = self.get_argument("name", "").strip()
        description = self.get_argument("description", "").strip()
        skill_type = self.get_argument("skill_type", "api")
        category = self.get_argument("category", "").strip()
        config_raw = self.get_argument("config", "{}")
        parameters_raw = self.get_argument("parameters", "[]")
        is_active = int(self.get_argument("is_active", 1))

        if not skill_id:
            self.write({"code": 1, "msg": "参数错误"})
            return

        try:
            config = json.loads(config_raw) if isinstance(config_raw, str) else config_raw
        except json.JSONDecodeError:
            config = {}
        try:
            parameters = json.loads(parameters_raw) if isinstance(parameters_raw, str) else parameters_raw
        except json.JSONDecodeError:
            parameters = []

        SkillRepository.update(skill_id, name, description, skill_type, category, config, parameters, is_active)
        self.write({"code": 0, "msg": "更新成功"})


class SkillDeleteHandler(BaseHandler):
    """删除技能"""
    @tornado.web.authenticated
    def post(self):
        skill_id = int(self.get_argument("id", 0))
        SkillRepository.delete(skill_id)
        self.write({"code": 0, "msg": "删除成功"})


class SkillGetHandler(BaseHandler):
    """获取单个技能详情"""
    @tornado.web.authenticated
    def get(self):
        skill_id = int(self.get_argument("id", 0))
        if not skill_id:
            self.write({"code": 1, "msg": "参数错误"})
            return
        skill = SkillRepository.get_by_id(skill_id)
        if not skill:
            self.write({"code": 1, "msg": "技能不存在"})
            return
        self.write({"code": 0, "data": skill})


class SkillDetailHandler(BaseHandler):
    """技能详情页面"""
    @tornado.web.authenticated
    def get(self):
        skill_id = self.get_argument("id", 0)
        username = self.current_user if self.current_user else ""
        self.render("skill_detail.html", title="技能详情", username=username, skill_id=skill_id)


class SkillCategoriesHandler(BaseHandler):
    """获取所有分类"""
    @tornado.web.authenticated
    def get(self):
        categories = SkillRepository.get_categories()
        self.write({"code": 0, "data": categories})


class SkillCallHandler(BaseHandler):
    """执行技能调用"""
    @tornado.web.authenticated
    def post(self):
        skill_id = int(self.get_argument("skill_id", 0))
        input_raw = self.get_argument("input_data", "{}")

        skill = SkillRepository.get_by_id(skill_id)
        if not skill:
            self.write({"code": 1, "msg": "技能不存在"})
            return

        try:
            input_data = json.loads(input_raw) if isinstance(input_raw, str) else input_raw
        except json.JSONDecodeError:
            input_data = {"text": input_raw}

        import time
        start_time = time.time()

        try:
            if skill["skill_type"] == "api":
                result = self._call_api_skill(skill, input_data)
            elif skill["skill_type"] == "ai":
                result = self._call_ai_skill(skill, input_data)
            else:
                result = {"code": 1, "msg": f"不支持的技能类型: {skill['skill_type']}"}

            duration = int((time.time() - start_time) * 1000)
            if result.get("code") == 0:
                SkillCallLogRepository.create(skill_id, input_data, result.get("data", {}), "success", duration)
                self.write(result)
            else:
                SkillCallLogRepository.create(skill_id, input_data, result.get("msg", ""), "failed", duration, result.get("msg", ""))
                self.write(result)

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            err_msg = str(e)
            logger.error(f"技能调用异常: skill_id={skill_id}, error={traceback.format_exc()}")
            SkillCallLogRepository.create(skill_id, input_data, err_msg, "failed", duration, err_msg)
            self.write({"code": 1, "msg": f"调用失败: {err_msg}"})

    def _call_api_skill(self, skill, input_data):
        """调用API类型技能"""
        config = skill.get("config", {})
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = {}

        url = config.get("url", "")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        body_template = config.get("body_template", "")
        prompt_template = config.get("prompt_template", "")

        if not url:
            return {"code": 1, "msg": "API技能配置中缺少 url 字段，请在配置中添加 url 字段"}

        # 替换模板变量
        url_final = url
        for k, v in input_data.items():
            url_final = url_final.replace(f"{{{k}}}", str(v))

        try:
            if method == "GET":
                resp = httpx.get(url_final, headers=headers, timeout=30.0)
            elif method == "POST":
                body = body_template
                for k, v in input_data.items():
                    body = body.replace(f"{{{k}}}", str(v))
                try:
                    body_json = json.loads(body)
                    resp = httpx.post(url_final, headers=headers, json=body_json, timeout=30.0)
                except (json.JSONDecodeError, TypeError):
                    resp = httpx.post(url_final, headers=headers, data=body, timeout=30.0)
            else:
                return {"code": 1, "msg": f"不支持的HTTP方法: {method}"}

            resp.raise_for_status()
            try:
                data = resp.json()
            except json.JSONDecodeError:
                data = resp.text
            return {"code": 0, "msg": "调用成功", "data": data}

        except httpx.TimeoutException:
            return {"code": 1, "msg": "请求超时"}
        except Exception as e:
            return {"code": 1, "msg": f"请求失败: {str(e)}"}

    def _call_ai_skill(self, skill, input_data):
        """调用AI类型技能（使用默认模型）"""
        config = skill.get("config", {})
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = {}

        prompt_template = config.get("prompt_template", "请回答：{text}")
        model_id = config.get("model_id", 0)

        # 获取用户输入文本
        text = input_data.get("text", "") or input_data.get("input", "") or json.dumps(input_data, ensure_ascii=False)
        prompt = prompt_template.replace("{text}", text).replace("{input}", text)
        for k, v in input_data.items():
            prompt = prompt.replace(f"{{{k}}}", str(v))

        # 获取AI模型
        if model_id:
            model = AiModelRepository.get_by_id(model_id)
        else:
            models = AiModelRepository.get_all()
            model = next((m for m in models if m["is_default"]), models[0] if models else None)

        if not model:
            return {"code": 1, "msg": "没有可用的AI模型，请先在模型引擎中配置"}

        if not OPENAI_AVAILABLE or OpenAI is None:
            return {"code": 1, "msg": "OpenAI SDK未安装"}

        try:
            import httpx as _httpx
            client = OpenAI(
                api_key=model["api_key"],
                base_url=model["base_url"],
                http_client=_httpx.Client(timeout=60.0),
            )
            response = client.chat.completions.create(
                model=model["model_name"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=model["max_tokens"],
                temperature=model["temperature"],
            )
            reply = response.choices[0].message.content
            return {"code": 0, "msg": "调用成功", "data": {"reply": reply, "model": model["name"]}}

        except Exception as e:
            return {"code": 1, "msg": f"AI调用失败: {str(e)}"}


class SkillAICreateHandler(BaseHandler):
    """AI自动创建技能"""
    @tornado.web.authenticated
    def post(self):
        description = self.get_argument("description", "").strip()
        if not description:
            self.write({"code": 1, "msg": "请描述要创建的技能"})
            return

        # 检测描述中是否包含 HTTP/HTTPS URL，如果有则直接创建 API 技能，不走 AI
        import re as _re
        url_pattern = _re.compile(r'https?://[^\s,，。、\'"]+')
        url_match = url_pattern.search(description)
        if url_match:
            detected_url = url_match.group().rstrip('/').rstrip('?')
            # 从描述中提取请求方法
            method = "GET"  # 默认GET
            if _re.search(r'POST|post|提交|发送', description):
                method = "POST"

            # 从描述中提取技能名称（取 URL 最后一段或有意义的描述词）
            name = "API技能"
            name_match = _re.search(r'(?:创建|新建|做一个?个?|写一个?个?|开发)(?:一个?个?)?(?:技能|接口|api)?[：: ]*([^\s，。]{2,20})', description)
            if name_match:
                name = name_match.group(1).strip()
            else:
                # 从URL提取
                url_parts = detected_url.rstrip('/').split('/')
                if url_parts:
                    last_part = url_parts[-1].split('?')[0]
                    if last_part and len(last_part) < 15:
                        name = last_part

            # 从 URL 中提取花括号参数或 query 参数
            params = []
            # 检查 URL 中已有的 query 参数
            if '?' in detected_url:
                query_part = detected_url.split('?', 1)[1]
                for qp in query_part.split('&'):
                    if '=' in qp:
                        param_name = qp.split('=')[0].rstrip('-').strip()
                        if param_name:
                            params.append({"name": param_name, "type": "string", "required": True, "description": param_name})

            # 如果 URL 包含花括号参数
            brace_params = _re.findall(r'\{(\w+)\}', detected_url)
            for p in brace_params:
                if not any(existing["name"] == p for existing in params):
                    params.append({"name": p, "type": "string", "required": True, "description": p})

            # 如果没提取到任何参数，加一个 text 参数
            if not params:
                params.append({"name": "text", "type": "string", "required": False, "description": "输入数据"})

            skill_type = "api"
            skill_config = {"url": detected_url, "method": method}
            category = "信息查询" if method == "GET" else "数据处理"
            desc = description

            username = self.current_user
            user_info = self.get_current_user_info()
            created_by = user_info.get("id", 0) if user_info else 0
            skill_id = SkillRepository.create(name, desc, skill_type, category, skill_config, params, created_by)
            self.write({
                "code": 0,
                "msg": f"检测到API URL，已自动创建API技能（{detected_url}）",
                "id": skill_id,
                "fix_messages": [f"从描述中提取到API URL，已直接创建为API技能"],
                "skill": {
                    "id": skill_id,
                    "name": name,
                    "description": desc,
                    "skill_type": skill_type,
                    "category": category,
                    "config": skill_config,
                    "parameters": params,
                }
            })
            return

        # 获取默认模型
        models = AiModelRepository.get_all()
        model = next((m for m in models if m["is_default"]), models[0] if models else None)
        if not model:
            self.write({"code": 1, "msg": "没有可用的AI模型，请先在模型引擎中配置"})
            return

        if not OPENAI_AVAILABLE or OpenAI is None:
            self.write({"code": 1, "msg": "OpenAI SDK未安装"})
            return

        # 构造AI提示词
        prompt = f"""你是一个专业的技能生成器。根据用户的描述，生成一个结构化的技能配置JSON。

用户描述：{description}

重要规则：
1. 如果用户描述的是调用外部数据接口（如天气、新闻、汇率等），必须设置为 "skill_type": "api"，并且使用真实可用的免费API URL。
2. 已知免费API参考：
   - 天气查询：https://wttr.in/{{city}}?format=%C+%t（返回简短天气，如"Sunny +25°C"）
   - 更多：可以自行搜索其他免费公开API
3. 如果用户描述的是对话、内容生成、分析总结等，才设置为 "skill_type": "ai"。
4. 绝对不要把一个应该是API调用的技能设置为AI类型。

请生成包含以下字段的JSON（不要包含任何markdown格式，只返回纯JSON）：
{{
    "name": "技能名称（简短，如：查询天气、发送邮件）",
    "description": "技能详细描述",
    "skill_type": "api 或 ai（根据描述判断是调用外部API还是AI处理）",
    "category": "技能分类（如：数据处理、信息查询、内容生成、自动化操作等）",
    "config": {{
        "url": "（如果是API类型，填调用URL，可用{{param}}做变量）",
        "method": "GET 或 POST",
        "headers": {{"Content-Type": "application/json"}},
        "body_template": "（如果是POST，填请求体模板）",
        "prompt_template": "（如果是AI类型，填提示词模板，可用{{text}}做输入变量）"
    }},
    "parameters": [
        {{"name": "param1", "type": "string", "required": true, "description": "参数说明"}}
    ]
}}

确保返回的JSON是有效的，可以直接被json.loads解析。"""

        try:
            client = OpenAI(
                api_key=model["api_key"],
                base_url=model["base_url"],
                http_client=httpx.Client(timeout=60.0),
            )
            response = client.chat.completions.create(
                model=model["model_name"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=model["max_tokens"],
                temperature=0.3,
            )
            reply = response.choices[0].message.content

            # 清理可能的markdown标记
            reply = reply.strip()
            if reply.startswith("```"):
                reply = reply.split("\n", 1)[1] if "\n" in reply else reply[3:]
            if reply.endswith("```"):
                reply = reply.rsplit("```", 1)[0]
            reply = reply.strip()

            # 尝试解析JSON，失败时尝试修复
            try:
                config = json.loads(reply)
            except json.JSONDecodeError:
                # 尝试修复常见JSON格式问题：删除注释、修复尾部逗号等
                fixed_reply = _re.sub(r'//.*', '', reply)  # 删除单行注释
                fixed_reply = _re.sub(r',\s*}', '}', fixed_reply)  # 删除对象尾部逗号
                fixed_reply = _re.sub(r',\s*\]', ']', fixed_reply)  # 删除数组尾部逗号
                try:
                    config = json.loads(fixed_reply)
                except json.JSONDecodeError:
                    # 尝试从回复中提取JSON块
                    json_match = _re.search(r'\{[\s\S]*\}', reply)
                    if json_match:
                        try:
                            config = json.loads(json_match.group())
                        except json.JSONDecodeError:
                            self.write({"code": 1, "msg": f"AI返回格式错误，无法解析配置。请检查AI响应或手动创建技能: {reply[:300]}..."})
                            return
                    else:
                        self.write({"code": 1, "msg": f"AI返回格式错误，无法解析配置。请检查AI响应或手动创建技能: {reply[:300]}..."})
                        return

            name = config.pop("name", "AI生成技能")
            desc = config.pop("description", description)
            skill_type = config.pop("skill_type", "ai")
            category = config.pop("category", "通用")
            params = config.pop("parameters", [])
            skill_config = config
            fix_messages = []

            # 自动修复配置逻辑
            # 情况1: API类型但没有URL，但有prompt_template → 修正为AI类型
            if skill_type == "api" and not skill_config.get("url") and skill_config.get("prompt_template"):
                skill_type = "ai"
                fix_messages.append("检测到技能标记为API类型但未提供URL，已自动修正为AI类型")

            # 情况2: API类型但config为空或没有有效字段 → 修正为AI类型
            if skill_type == "api" and not skill_config.get("url") and not skill_config.get("prompt_template"):
                if skill_config.get("method") or skill_config.get("headers"):
                    # 有HTTP相关配置但没URL，无法修复
                    self.write({"code": 1, "msg": f"AI创建的API技能配置缺少 url 字段(当前配置: {json.dumps(skill_config, ensure_ascii=False)})，无法自动修复，请检查配置后重试"})
                    return
                else:
                    # 没有API相关配置，改为AI类型并设置默认prompt_template
                    skill_type = "ai"
                    skill_config["prompt_template"] = skill_config.get("prompt_template", "请回答：{text}")
                    fix_messages.append("检测到技能既不是有效的API类型也不是AI类型，已自动修正为AI类型并设置默认模板")

            # 情况3: AI类型但没有prompt_template → 设置默认模板
            if skill_type == "ai" and not skill_config.get("prompt_template"):
                skill_config["prompt_template"] = "请回答：{text}"
                fix_messages.append("AI技能缺少prompt_template，已自动设置默认模板")

            # 后处理：检测用户是否想要API技能但AI生成了AI类型
            # 常见API意图关键词
            api_intent_keywords = ["天气", "查询", "接口", "api", "API", "获取", "数据", "实时", "预报", "汇率",
                                   "新闻", "股票", "搜索", "爬取", "采集", "请求", "http", "https", "调用"]
            if skill_type == "ai":
                desc_lower = description.lower()
                # 检查是否有免费API可自动替换的已知场景
                known_free_apis = {
                    "天气": {
                        "url": "https://wttr.in/{city}?format=%C+%t",
                        "method": "GET",
                        "params": [{"name": "city", "type": "string", "required": True, "description": "城市名称"}],
                        "name_hint": "查询天气"
                    },
                }
                matched_api = None
                for keyword, api_info in known_free_apis.items():
                    if keyword in description:
                        matched_api = api_info
                        break
                if matched_api:
                    # 检查是否真的是API意图（有对应的关键词）
                    if any(kw in description for kw in api_intent_keywords):
                        skill_type = "api"
                        skill_config = {
                            "url": matched_api["url"],
                            "method": matched_api["method"],
                        }
                        params = matched_api["params"]
                        if not name or name == "AI生成技能":
                            name = matched_api["name_hint"]
                        fix_messages.append(f"检测到[{description}]是调用API的场景，已自动使用免费API({matched_api['url']})创建为API技能")
                    else:
                        fix_messages.append("检测到描述可能涉及API调用，但AI生成了AI类型技能。如果需要调用外部API，请手动创建API技能并提供真实的API地址")
                # 非已知场景但包含API意图关键词，提示用户
                elif any(kw in desc_lower for kw in ["api", "http", "https", "接口", "调用"]):
                    fix_messages.append("检测到描述涉及API调用，但AI生成了AI类型技能。如需创建API技能，请手动提供真实的API地址")

            # 创建技能
            username = self.current_user
            user_info = self.get_current_user_info()
            created_by = user_info.get("id", 0) if user_info else 0

            skill_id = SkillRepository.create(name, desc, skill_type, category, skill_config, params, created_by)
            msg = "AI创建技能成功"
            if fix_messages:
                msg += "（" + "；".join(fix_messages) + "）"
            self.write({
                "code": 0,
                "msg": msg,
                "id": skill_id,
                "fix_messages": fix_messages,
                "skill": {
                    "id": skill_id,
                    "name": name,
                    "description": desc,
                    "skill_type": skill_type,
                    "category": category,
                    "config": skill_config,
                    "parameters": params,
                }
            })
        except Exception as e:
            logger.error(f"AI创建技能失败: {traceback.format_exc()}")
            self.write({"code": 1, "msg": f"AI创建失败: {str(e)}"})


class SkillCallLogHandler(BaseHandler):
    """调用记录页面"""
    @tornado.web.authenticated
    def get(self):
        skill_id = self.get_argument("skill_id", "")
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 20))
        sid = int(skill_id) if skill_id else None
        data = SkillCallLogRepository.get_page(page, page_size, sid)
        self.write(data)
