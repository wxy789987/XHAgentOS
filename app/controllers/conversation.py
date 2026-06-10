# 会话管理控制层
import json
import logging
import traceback
import re
import tornado.web
from app.controllers.base import BaseHandler
from app.models.conversation import ConversationRepository, MessageRepository, ViolationLogRepository
from app.models.ai_model import AiModelRepository

logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = True
try:
    from openai import OpenAI
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None


# ==================== 违规关键词配置 ====================
# 可扩展的违规关键词库
BANNED_KEYWORDS = {
    "high": ["赌博", "毒品", "枪支", "暴力", "色情", "诈骗", "赌博平台", "违禁品",
             "走私", "洗钱", "恐怖", "枪支弹药", "毒品交易", "儿童色情"],
    "medium": ["代考", "代写", "刷单", "刷分", "作弊", "外挂", "破解", "私服",
               "盗版", "翻墙", "VPN", "假证"],
    "low": ["广告", "推广", "加微信", "加QQ", "私聊", "垃圾信息"],
}

# 违规技能调用模式
BANNED_SKILL_PATTERNS = [
    r"(?:调用|执行|运行)\s*(?:非法|违规|禁止|敏感)",
    r"攻击.*服务器",
    r"获取.*他人.*隐私",
    r"非法.*(?:接口|api|API)",
]


# ==================== AI分析函数 ====================

def ai_analyze_message(content):
    """调用AI模型分析消息：情感分析、主题分析、实体识别"""
    models = AiModelRepository.get_all()
    model = next((m for m in models if m["is_default"]), models[0] if models else None)
    if not model or not OPENAI_AVAILABLE or OpenAI is None:
        return {"sentiment": "neutral", "topic": "general", "entities": []}

    prompt = f"""请分析以下消息，返回JSON格式的分析结果（不要包含markdown标记，只返回纯JSON）：

消息内容：{content}

返回格式：
{{
    "sentiment": "positive/negative/neutral",  // 情感倾向
    "topic": "简短的主题分类（如：技术讨论、日常闲聊、业务咨询等）",
    "entities": ["实体1", "实体2"]  // 识别出的关键实体（人名、地名、产品名等）
}}"""

    try:
        import httpx
        client = OpenAI(
            api_key=model["api_key"],
            base_url=model["base_url"],
            http_client=httpx.Client(timeout=30.0),
        )
        response = client.chat.completions.create(
            model=model["model_name"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=model.get("max_tokens", 4096),
            temperature=0.3,
        )
        reply = response.choices[0].message.content.strip()
        # 清理markdown标记
        if reply.startswith("```"):
            reply = reply.split("\n", 1)[1] if "\n" in reply else reply[3:]
        if reply.endswith("```"):
            reply = reply.rsplit("```", 1)[0]
        reply = reply.strip()
        result = json.loads(reply)
        return {
            "sentiment": result.get("sentiment", "neutral"),
            "topic": result.get("topic", "general"),
            "entities": result.get("entities", []),
        }
    except Exception as e:
        logger.warning(f"AI分析消息失败: {e}")
        return {"sentiment": "neutral", "topic": "general", "entities": []}


# ==================== 违规检测函数 ====================

def check_violations(content):
    """检查消息是否包含违规内容，返回违规列表"""
    violations = []

    # 1. 检查违规关键词
    for severity, keywords in BANNED_KEYWORDS.items():
        for keyword in keywords:
            if keyword in content:
                violations.append({
                    "type": "keyword",
                    "matched_keyword": keyword,
                    "severity": severity,
                    "violation_content": content[:200],
                })

    # 2. 检查违规技能调用模式
    for pattern in BANNED_SKILL_PATTERNS:
        if re.search(pattern, content):
            violations.append({
                "type": "skill_call",
                "matched_keyword": pattern,
                "severity": "high",
                "violation_content": content[:200],
            })

    return violations


# ==================== Handlers ====================

class ConversationHandler(BaseHandler):
    """会话管理页面"""
    @tornado.web.authenticated
    def get(self):
        username = self.current_user if self.current_user else ""
        self.render("conversation_list.html", title="会话管理", username=username)


class ConversationListHandler(BaseHandler):
    """会话列表API"""
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 10))
        keyword = self.get_argument("keyword", "")
        status = self.get_argument("status", "")
        data = ConversationRepository.get_page(page, page_size, keyword, status)
        self.write(data)


class ConversationAddHandler(BaseHandler):
    """新增会话"""
    @tornado.web.authenticated
    def post(self):
        title = self.get_argument("title", "").strip()
        description = self.get_argument("description", "").strip()
        if not title:
            self.write({"code": 1, "msg": "会话名称不能为空"})
            return
        username = self.current_user
        user = self.get_current_user_info()
        created_by = user.get("id", 0) if user else 0
        conv_id = ConversationRepository.create(title, description, created_by)
        self.write({"code": 0, "msg": "新增成功", "id": conv_id})


class ConversationEditHandler(BaseHandler):
    """编辑会话"""
    @tornado.web.authenticated
    def post(self):
        conv_id = int(self.get_argument("id", 0))
        title = self.get_argument("title", "").strip()
        description = self.get_argument("description", "").strip()
        status = self.get_argument("status", "active")
        if not conv_id or not title:
            self.write({"code": 1, "msg": "参数错误"})
            return
        ConversationRepository.update(conv_id, title, description, status)
        self.write({"code": 0, "msg": "更新成功"})


class ConversationDeleteHandler(BaseHandler):
    """删除会话"""
    @tornado.web.authenticated
    def post(self):
        conv_id = int(self.get_argument("id", 0))
        ConversationRepository.delete(conv_id)
        self.write({"code": 0, "msg": "删除成功"})


class ConversationGetHandler(BaseHandler):
    """获取单个会话详情"""
    @tornado.web.authenticated
    def get(self):
        conv_id = int(self.get_argument("id", 0))
        conv = ConversationRepository.get_by_id(conv_id)
        if not conv:
            self.write({"code": 1, "msg": "会话不存在"})
            return
        self.write({"code": 0, "data": conv})


class ConversationDetailHandler(BaseHandler):
    """会话详情页面"""
    @tornado.web.authenticated
    def get(self):
        conv_id = self.get_argument("id", 0)
        username = self.current_user if self.current_user else ""
        self.render("conversation_detail.html", title="会话详情", username=username, conv_id=conv_id)


# ==================== 消息管理 ====================

class MessageListHandler(BaseHandler):
    """消息列表API"""
    @tornado.web.authenticated
    def get(self):
        conv_id = int(self.get_argument("conversation_id", 0))
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 50))
        data = MessageRepository.get_page(conv_id, page, page_size)
        self.write(data)


class MessageAddHandler(BaseHandler):
    """新增消息（并自动进行AI分析和违规检测）"""
    @tornado.web.authenticated
    def post(self):
        conv_id = int(self.get_argument("conversation_id", 0))
        role = self.get_argument("role", "user")
        content = self.get_argument("content", "").strip()

        if not conv_id or not content:
            self.write({"code": 1, "msg": "参数错误"})
            return

        # 创建消息
        msg_id = MessageRepository.create(conv_id, role, content)

        # 异步触发AI分析和违规检测（同步执行，但记录结果）
        analysis = ai_analyze_message(content)
        MessageRepository.update_analysis(msg_id, analysis["sentiment"], analysis["topic"], analysis["entities"])

        # 违规检测
        violations = check_violations(content)
        is_violation = len(violations) > 0
        if is_violation:
            MessageRepository.set_violation_flag(msg_id, 1)
            for v in violations:
                ViolationLogRepository.create(
                    conversation_id=conv_id,
                    message_id=msg_id,
                    violation_type=v["type"],
                    violation_content=v["violation_content"],
                    matched_keyword=v["matched_keyword"],
                    severity=v["severity"],
                )

        # 更新会话消息计数
        ConversationRepository.update_message_count(conv_id)

        result = {
            "code": 0,
            "msg": "新增成功",
            "id": msg_id,
            "analysis": analysis,
            "violations": violations if is_violation else [],
        }
        if is_violation:
            result["warning"] = f"检测到 {len(violations)} 条违规内容"

        self.write(result)


class MessageAnalyzeHandler(BaseHandler):
    """手动触发AI分析"""
    @tornado.web.authenticated
    def post(self):
        msg_id = int(self.get_argument("message_id", 0))
        msg = MessageRepository.get_by_id(msg_id)
        if not msg:
            self.write({"code": 1, "msg": "消息不存在"})
            return

        analysis = ai_analyze_message(msg["content"])
        MessageRepository.update_analysis(msg_id, analysis["sentiment"], analysis["topic"], analysis["entities"])

        # 违规检测
        violations = check_violations(msg["content"])
        if violations:
            MessageRepository.set_violation_flag(msg_id, 1)
            for v in violations:
                ViolationLogRepository.create(
                    conversation_id=msg["conversation_id"],
                    message_id=msg_id,
                    violation_type=v["type"],
                    violation_content=v["violation_content"],
                    matched_keyword=v["matched_keyword"],
                    severity=v["severity"],
                )

        self.write({"code": 0, "msg": "分析完成", "analysis": analysis, "violations": violations})


class MessageAnalyzeAllHandler(BaseHandler):
    """分析会话中所有未分析的消息"""
    @tornado.web.authenticated
    def post(self):
        conv_id = int(self.get_argument("conversation_id", 0))
        if not conv_id:
            self.write({"code": 1, "msg": "参数错误"})
            return

        messages = MessageRepository.get_page(conv_id, 1, 1000).get("items", [])
        count = 0
        violation_count = 0
        for msg in messages:
            if not msg.get("sentiment"):
                analysis = ai_analyze_message(msg["content"])
                MessageRepository.update_analysis(msg["id"], analysis["sentiment"], analysis["topic"], analysis["entities"])
                count += 1

                violations = check_violations(msg["content"])
                if violations:
                    MessageRepository.set_violation_flag(msg["id"], 1)
                    for v in violations:
                        ViolationLogRepository.create(
                            conversation_id=conv_id,
                            message_id=msg["id"],
                            violation_type=v["type"],
                            violation_content=v["violation_content"],
                            matched_keyword=v["matched_keyword"],
                            severity=v["severity"],
                        )
                    violation_count += len(violations)

        self.write({"code": 0, "msg": f"分析完成，共分析 {count} 条消息，发现 {violation_count} 条违规"})


# ==================== 违规监控 ====================

class ViolationListHandler(BaseHandler):
    """违规记录列表API"""
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 20))
        conv_id = self.get_argument("conversation_id", "")
        severity = self.get_argument("severity", "")
        cid = int(conv_id) if conv_id else None
        data = ViolationLogRepository.get_page(page, page_size, cid, severity)
        # 补充会话标题
        items = data.get("items", [])
        for item in items:
            conv = ConversationRepository.get_by_id(item["conversation_id"])
            item["conversation_title"] = conv["title"] if conv else "已删除"
        data["items"] = items
        self.write(data)


class ViolationUpdateHandler(BaseHandler):
    """更新违规记录状态"""
    @tornado.web.authenticated
    def post(self):
        vid = int(self.get_argument("id", 0))
        status = self.get_argument("status", "resolved")
        ViolationLogRepository.update_status(vid, status)
        self.write({"code": 0, "msg": "更新成功"})


class ViolationMonitorPageHandler(BaseHandler):
    """违规监控页面"""
    @tornado.web.authenticated
    def get(self):
        username = self.current_user if self.current_user else ""
        self.render("violation_monitor.html", title="违规监控", username=username)


class ConversationCheckAllHandler(BaseHandler):
    """扫描所有会话进行违规检测"""
    @tornado.web.authenticated
    def post(self):
        page = 1
        total_checked = 0
        total_violations = 0
        while True:
            data = ConversationRepository.get_page(page, 50)
            items = data.get("items", [])
            if not items:
                break
            for conv in items:
                msgs = MessageRepository.get_page(conv["id"], 1, 1000).get("items", [])
                for msg in msgs:
                    violations = check_violations(msg["content"])
                    if violations:
                        MessageRepository.set_violation_flag(msg["id"], 1)
                        for v in violations:
                            ViolationLogRepository.create(
                                conversation_id=conv["id"],
                                message_id=msg["id"],
                                violation_type=v["type"],
                                violation_content=v["violation_content"],
                                matched_keyword=v["matched_keyword"],
                                severity=v["severity"],
                            )
                            total_violations += 1
                    total_checked += 1
            page += 1
        self.write({"code": 0, "msg": f"扫描完成，共检查 {total_checked} 条消息，发现 {total_violations} 条违规"})
