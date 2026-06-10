# 数智大屏控制层
import json
import csv
import io
import logging
import tornado.web
from app.controllers.base import BaseHandler
from app.models.datascreen import DatascreenRepository, DatascreenCallLogRepository

logger = logging.getLogger(__name__)


class DatascreenHandler(BaseHandler):
    """数智大屏管理页面"""
    @tornado.web.authenticated
    def get(self):
        username = self.current_user if self.current_user else ""
        self.render("datascreen_list.html", title="数智大屏", username=username)


class DatascreenListHandler(BaseHandler):
    """列表API"""
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 10))
        keyword = self.get_argument("keyword", "")
        data = DatascreenRepository.get_page(page, page_size, keyword)
        self.write(data)


class DatascreenGetHandler(BaseHandler):
    """获取详情"""
    @tornado.web.authenticated
    def get(self):
        ds_id = int(self.get_argument("id", 0))
        d = DatascreenRepository.get_by_id(ds_id)
        if not d:
            self.write({"code": 1, "msg": "不存在"})
            return
        # 解析JSON字段
        for f in ["chart_config", "raw_data", "layout_config"]:
            if isinstance(d.get(f), str):
                try:
                    d[f] = json.loads(d[f])
                except:
                    pass
        self.write({"code": 0, "data": d})


class DatascreenAddHandler(BaseHandler):
    """新增"""
    @tornado.web.authenticated
    def post(self):
        name = self.get_argument("name", "").strip()
        description = self.get_argument("description", "").strip()
        screen_type = self.get_argument("screen_type", "chart").strip()
        raw_data_raw = self.get_argument("raw_data", "[]").strip()
        chart_config_raw = self.get_argument("chart_config", "{}").strip()
        layout_config_raw = self.get_argument("layout_config", "{}").strip()

        if not name:
            self.write({"code": 1, "msg": "名称不能为空"})
            return

        try:
            raw_data = json.loads(raw_data_raw) if raw_data_raw else []
        except:
            raw_data = []
        try:
            chart_config = json.loads(chart_config_raw) if chart_config_raw else {}
        except:
            chart_config = {}
        try:
            layout_config = json.loads(layout_config_raw) if layout_config_raw else {}
        except:
            layout_config = {}

        username = self.current_user
        user = self.get_current_user_info()
        created_by = user.get("id", 0) if user else 0

        ds_id = DatascreenRepository.create(name, description, screen_type, chart_config, raw_data, layout_config, created_by)
        self.write({"code": 0, "msg": "新增成功", "id": ds_id})


class DatascreenEditHandler(BaseHandler):
    """编辑"""
    @tornado.web.authenticated
    def post(self):
        ds_id = int(self.get_argument("id", 0))
        name = self.get_argument("name", "").strip()
        description = self.get_argument("description", "").strip()
        screen_type = self.get_argument("screen_type", "chart").strip()
        raw_data_raw = self.get_argument("raw_data", "[]").strip()
        chart_config_raw = self.get_argument("chart_config", "{}").strip()
        layout_config_raw = self.get_argument("layout_config", "{}").strip()
        is_active = int(self.get_argument("is_active", 1))

        if not ds_id or not name:
            self.write({"code": 1, "msg": "参数错误"})
            return

        try:
            raw_data = json.loads(raw_data_raw) if raw_data_raw else []
        except:
            raw_data = []
        try:
            chart_config = json.loads(chart_config_raw) if chart_config_raw else {}
        except:
            chart_config = {}
        try:
            layout_config = json.loads(layout_config_raw) if layout_config_raw else {}
        except:
            layout_config = {}

        DatascreenRepository.update(ds_id, name, description, screen_type, chart_config, raw_data, layout_config, is_active)
        self.write({"code": 0, "msg": "更新成功"})


class DatascreenDeleteHandler(BaseHandler):
    """删除"""
    @tornado.web.authenticated
    def post(self):
        ds_id = int(self.get_argument("id", 0))
        DatascreenRepository.delete(ds_id)
        self.write({"code": 0, "msg": "删除成功"})


class DatascreenViewHandler(BaseHandler):
    """大屏展示页面"""
    @tornado.web.authenticated
    def get(self):
        ds_id = self.get_argument("id", 0)
        username = self.current_user if self.current_user else ""
        self.render("datascreen_view.html", title="数智大屏", username=username, datascreen_id=ds_id)


class DatascreenRenderHandler(BaseHandler):
    """渲染大屏数据API"""
    @tornado.web.authenticated
    def get(self):
        ds_id = int(self.get_argument("id", 0))
        d = DatascreenRepository.get_by_id(ds_id)
        if not d:
            self.write({"code": 1, "msg": "不存在"})
            return
        for f in ["chart_config", "raw_data", "layout_config"]:
            if isinstance(d.get(f), str):
                try:
                    d[f] = json.loads(d[f])
                except:
                    pass
        # 记录查看日志
        DatascreenCallLogRepository.create(ds_id, "view", {"screen_type": d.get("screen_type")})
        self.write({"code": 0, "data": d})


class DatascreenExportHandler(BaseHandler):
    """数据导出（CSV格式）"""
    @tornado.web.authenticated
    def get(self):
        ds_id = int(self.get_argument("id", 0))
        fmt = self.get_argument("format", "csv")
        d = DatascreenRepository.get_by_id(ds_id)
        if not d:
            self.write({"code": 1, "msg": "不存在"})
            return

        raw_data_str = d.get("raw_data", "[]")
        try:
            raw_data = json.loads(raw_data_str) if isinstance(raw_data_str, str) else raw_data_str
        except:
            raw_data = []
        chart_config_str = d.get("chart_config", "{}")
        try:
            chart_config = json.loads(chart_config_str) if isinstance(chart_config_str, str) else chart_config_str
        except:
            chart_config = {}

        # 构建CSV
        output = io.StringIO()
        writer = csv.writer(output)
        # 写入基本信息
        writer.writerow(["数智大屏导出", d.get("name", "")])
        writer.writerow(["描述", d.get("description", "")])
        writer.writerow(["类型", d.get("screen_type", "")])
        writer.writerow([])

        # 写入图表配置
        if chart_config:
            writer.writerow(["图表配置"])
            for k, v in chart_config.items():
                if isinstance(v, (dict, list)):
                    writer.writerow([k, json.dumps(v, ensure_ascii=False)])
                else:
                    writer.writerow([k, v])
            writer.writerow([])

        # 写入原始数据
        if raw_data and isinstance(raw_data, list) and len(raw_data) > 0:
            if isinstance(raw_data[0], dict):
                headers = list(raw_data[0].keys())
                writer.writerow(headers)
                for row in raw_data:
                    writer.writerow([row.get(h, "") for h in headers])
            else:
                writer.writerow(["data"])
                for item in raw_data:
                    writer.writerow([item])

        csv_content = output.getvalue()
        output.close()

        self.set_header("Content-Type", "text/csv; charset=utf-8-sig")
        self.set_header("Content-Disposition", f'attachment; filename="{d.get("name", "export")}.csv"')
        self.write(csv_content.encode("utf-8-sig"))


class DatascreenCallLogHandler(BaseHandler):
    """调用记录"""
    @tornado.web.authenticated
    def get(self):
        ds_id = self.get_argument("datascreen_id", "")
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 20))
        did = int(ds_id) if ds_id else None
        data = DatascreenCallLogRepository.get_page(page, page_size, did)
        self.write(data)


class DatascreenPreviewHandler(BaseHandler):
    """预览（模拟渲染）"""
    @tornado.web.authenticated
    def post(self):
        screen_type = self.get_argument("screen_type", "chart")
        raw_data_raw = self.get_argument("raw_data", "[]")
        try:
            raw_data = json.loads(raw_data_raw)
        except:
            raw_data = []
        # 返回预览数据供前端渲染
        self.write({"code": 0, "data": {"screen_type": screen_type, "raw_data": raw_data}})
