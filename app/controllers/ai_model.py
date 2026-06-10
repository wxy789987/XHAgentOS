# AI模型管理控制层
import json
import logging
import traceback
import tornado.web
import tornado.gen
from app.controllers.base import BaseHandler
from app.models.ai_model import AiModelRepository

logger = logging.getLogger(__name__)

# 提前检测 openai 包是否可用
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

class AiModelHandler(BaseHandler):
    """模型管理页面"""
    @tornado.web.authenticated
    def get(self):
        username = self.current_user if self.current_user else ""
        self.render("ai_model_list.html", title="模型引擎", username=username)

class AiModelListHandler(BaseHandler):
    """模型列表JSON API（分页）"""
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 6))
        data = AiModelRepository.get_page(page, page_size)
        self.write(data)

class AiModelAddHandler(BaseHandler):
    """新增模型"""
    @tornado.web.authenticated
    def post(self):
        name = self.get_argument("name", "")
        model_name = self.get_argument("model_name", "")
        base_url = self.get_argument("base_url", "")
        api_key = self.get_argument("api_key", "")
        max_tokens = int(self.get_argument("max_tokens", 4096))
        temperature = float(self.get_argument("temperature", 0.7))
        if not name or not model_name:
            self.write({"code": 1, "msg": "名称和模型名不能为空"})
            return
        model_id = AiModelRepository.create(name, model_name, base_url, api_key, max_tokens, temperature)
        self.write({"code": 0, "msg": "新增成功", "id": model_id})

class AiModelEditHandler(BaseHandler):
    """编辑模型"""
    @tornado.web.authenticated
    def post(self):
        model_id = int(self.get_argument("id", 0))
        name = self.get_argument("name", "")
        model_name = self.get_argument("model_name", "")
        base_url = self.get_argument("base_url", "")
        api_key = self.get_argument("api_key", "")
        max_tokens = int(self.get_argument("max_tokens", 4096))
        temperature = float(self.get_argument("temperature", 0.7))
        is_active = int(self.get_argument("is_active", 1))
        if not name or not model_name:
            self.write({"code": 1, "msg": "名称和模型名不能为空"})
            return
        AiModelRepository.update(model_id, name, model_name, base_url, api_key, max_tokens, temperature, is_active)
        self.write({"code": 0, "msg": "更新成功"})

class AiModelDeleteHandler(BaseHandler):
    """删除模型"""
    @tornado.web.authenticated
    def post(self):
        model_id = int(self.get_argument("id", 0))
        AiModelRepository.delete(model_id)
        self.write({"code": 0, "msg": "删除成功"})

class AiModelSetDefaultHandler(BaseHandler):
    """设置默认模型"""
    @tornado.web.authenticated
    def post(self):
        model_id = int(self.get_argument("id", 0))
        AiModelRepository.set_default(model_id)
        self.write({"code": 0, "msg": "设置成功"})

class AiModelBatchHandler(BaseHandler):
    """批量操作"""
    @tornado.web.authenticated
    def post(self):
        action = self.get_argument("action", "")
        ids_json = self.get_argument("ids", "[]")
        ids = json.loads(ids_json)
        if not ids:
            self.write({"code": 1, "msg": "请选择模型"})
            return
        if action == "delete":
            AiModelRepository.batch_delete(ids)
            self.write({"code": 0, "msg": "批量删除成功"})
        elif action == "enable":
            AiModelRepository.batch_toggle_active(ids, 1)
            self.write({"code": 0, "msg": "批量启用成功"})
        elif action == "disable":
            AiModelRepository.batch_toggle_active(ids, 0)
            self.write({"code": 0, "msg": "批量禁用成功"})
        else:
            self.write({"code": 1, "msg": "未知操作"})

class AiModelChatHandler(BaseHandler):
    """模型对话测试（非流式）"""
    @tornado.web.authenticated
    def post(self):
        model_id = int(self.get_argument("model_id", 0))
        messages_json = self.get_argument("messages", "[]")
        messages = json.loads(messages_json)

        model = AiModelRepository.get_by_id(model_id)
        if not model:
            self.write({"code": 1, "msg": "模型不存在"})
            return

        if not OPENAI_AVAILABLE:
            self.write({"code": 1, "msg": "OpenAI SDK 未安装，请执行: pip install openai"})
            return

        try:
            import httpx
            client = OpenAI(
                api_key=model["api_key"],
                base_url=model["base_url"],
                http_client=httpx.Client(timeout=60.0),
            )
            response = client.chat.completions.create(
                model=model["model_name"],
                messages=messages,
                max_tokens=model["max_tokens"],
                temperature=model["temperature"],
            )
            reply = response.choices[0].message.content
            prompt_tk = response.usage.prompt_tokens if response.usage else 0
            completion_tk = response.usage.completion_tokens if response.usage else 0
            AiModelRepository.log_chat(model_id, prompt_tk, completion_tk)
            self.write({
                "code": 0,
                "reply": reply,
                "usage": {
                    "prompt_tokens": prompt_tk,
                    "completion_tokens": completion_tk,
                    "total_tokens": prompt_tk + completion_tk,
                }
            })
        except ImportError:
            self.write({"code": 1, "msg": "httpx 库未安装，请执行: pip install httpx"})
        except httpx.TimeoutException:
            logger.warning("模型对话超时: model_id=%s", model_id)
            self.write({"code": 1, "msg": "请求超时，请检查网络连接或 API 地址是否正确"})
        except Exception as e:
            err_msg = str(e)
            logger.error("模型对话异常: model_id=%s, error=%s", model_id, traceback.format_exc())
            if "not valid JSON" in err_msg or "JSONDecodeError" in err_msg:
                self.write({"code": 1, "msg": "API 返回了非 JSON 响应，请检查 base_url 是否正确或 API 服务是否正常"})
            elif "401" in err_msg or "Unauthorized" in err_msg:
                self.write({"code": 1, "msg": "API Key 无效或未授权"})
            elif "404" in err_msg:
                self.write({"code": 1, "msg": "模型名称不存在，请检查 model_name 是否正确"})
            elif "timeout" in err_msg.lower() or "timed out" in err_msg.lower():
                self.write({"code": 1, "msg": "请求超时，请检查网络连接"})
            else:
                self.write({"code": 1, "msg": f"请求失败: {err_msg}"})

class AiModelChatStreamHandler(BaseHandler):
    """模型对话测试（流式输出 - SSE）"""
    @tornado.web.authenticated
    async def post(self):
        import httpx
        import tornado.ioloop
        from concurrent.futures import ThreadPoolExecutor

        model_id = int(self.get_argument("model_id", 0))
        messages_json = self.get_argument("messages", "[]")
        messages = json.loads(messages_json)

        model = AiModelRepository.get_by_id(model_id)
        if not model:
            self.set_header("Content-Type", "text/event-stream; charset=utf-8")
            self.set_header("Cache-Control", "no-cache")
            self.write(f"data: {json.dumps({'type': 'error', 'msg': '模型不存在'})}\n\n")
            await self.flush()
            return

        if not OPENAI_AVAILABLE:
            self.set_header("Content-Type", "text/event-stream; charset=utf-8")
            self.set_header("Cache-Control", "no-cache")
            self.write(f"data: {json.dumps({'type': 'error', 'msg': 'OpenAI SDK 未安装，请执行: pip install openai'})}\n\n")
            await self.flush()
            return

        # 设置 SSE 响应头
        self.set_header("Content-Type", "text/event-stream; charset=utf-8")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        self.set_header("X-Accel-Buffering", "no")

        loop = tornado.ioloop.IOLoop.current()
        write_queue = []
        write_done = False
        write_error = None

        def do_stream():
            nonlocal write_done, write_error
            try:
                client = OpenAI(
                    api_key=model["api_key"],
                    base_url=model["base_url"],
                    http_client=httpx.Client(timeout=120.0),
                )
                full_content = ""
                response = client.chat.completions.create(
                    model=model["model_name"],
                    messages=messages,
                    max_tokens=model["max_tokens"],
                    temperature=model["temperature"],
                    stream=True,
                )
                for chunk in response:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        token_text = delta.content
                        full_content += token_text
                        data = json.dumps({"type": "chunk", "content": token_text})
                        write_queue.append(f"data: {data}\n\n")

                # token 统计
                prompt_tk = 0
                completion_tk = 0
                try:
                    if hasattr(chunk, 'usage') and chunk.usage:
                        prompt_tk = chunk.usage.prompt_tokens or 0
                        completion_tk = chunk.usage.completion_tokens or 0
                except Exception:
                    pass

                if completion_tk == 0:
                    try:
                        import tiktoken
                        enc = tiktoken.get_encoding("cl100k_base")
                        completion_tk = len(enc.encode(full_content))
                        prompt_tk = sum(len(enc.encode(m.get("content", ""))) for m in messages)
                    except Exception:
                        completion_tk = max(1, len(full_content) // 4)
                        prompt_tk = sum(len(m.get("content", "")) for m in messages) // 4

                prompt_tk = max(1, prompt_tk)
                completion_tk = max(1, completion_tk)
                AiModelRepository.log_chat(model_id, prompt_tk, completion_tk)

                done_data = json.dumps({
                    "type": "done",
                    "usage": {
                        "prompt_tokens": prompt_tk,
                        "completion_tokens": completion_tk,
                        "total_tokens": prompt_tk + completion_tk,
                    }
                })
                write_queue.append(f"data: {done_data}\n\n")

            except httpx.TimeoutException:
                write_queue.append(f"data: {json.dumps({'type': 'error', 'msg': '请求超时，请检查网络连接或 API 地址是否正确'})}\n\n")
            except Exception as e:
                err_msg = str(e)
                logger.error("模型对话流式异常: model_id=%s, error=%s", model_id, traceback.format_exc())
                if "not valid JSON" in err_msg or "JSONDecodeError" in err_msg:
                    msg = "API 返回了非 JSON 响应，请检查 base_url 是否正确或 API 服务是否正常"
                elif "401" in err_msg or "Unauthorized" in err_msg:
                    msg = "API Key 无效或未授权"
                elif "404" in err_msg:
                    msg = "模型名称不存在，请检查 model_name 是否正确"
                elif "timeout" in err_msg.lower() or "timed out" in err_msg.lower():
                    msg = "请求超时，请检查网络连接"
                else:
                    msg = f"请求失败: {err_msg}"
                write_queue.append(f"data: {json.dumps({'type': 'error', 'msg': msg})}\n\n")
            finally:
                write_done = True

        # 在线程池中执行阻塞的流式请求
        executor = ThreadPoolExecutor(max_workers=1)
        loop.run_in_executor(executor, do_stream)

        # 主协程持续消费 write_queue 并 flush
        while not write_done or write_queue:
            if write_queue:
                msg = write_queue.pop(0)
                self.write(msg)
                try:
                    await self.flush()
                except Exception:
                    break
            else:
                await tornado.gen.sleep(0.02)  # 20ms 轮询间隔

        # 处理剩余的队列
        while write_queue:
            self.write(write_queue.pop(0))
            try:
                await self.flush()
            except Exception:
                break

        executor.shutdown(wait=False)

class AiModelTokenStatsHandler(BaseHandler):
    """Token统计API"""
    @tornado.web.authenticated
    def get(self):
        model_id = self.get_argument("model_id", None)
        if model_id:
            model_id = int(model_id)
        data = AiModelRepository.get_token_stats(model_id)
        # 汇总
        total_prompt = sum(d["prompt_tokens"] or 0 for d in data)
        total_completion = sum(d["completion_tokens"] or 0 for d in data)
        total_all = sum(d["total_tokens"] or 0 for d in data)
        self.write({
            "code": 0,
            "items": data,
            "summary": {
                "prompt_tokens": total_prompt,
                "completion_tokens": total_completion,
                "total_tokens": total_all,
            }
        })
