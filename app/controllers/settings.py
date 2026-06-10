# 系统设置控制层
import json
import os
import time
import psutil
import tornado.web
from app.controllers.base import BaseHandler
from app.models.db import get_connection
from app.models.ai_model import AiModelRepository


class SettingsHandler(BaseHandler):
    """系统设置主页"""
    @tornado.web.authenticated
    def get(self):
        self.render("settings.html", title="系统设置")


class SettingsConfigHandler(BaseHandler):
    """系统配置页面"""
    @tornado.web.authenticated
    def get(self):
        conn = get_connection()
        # 获取数据库连接信息
        db_info = {
            "database": "SQLite",
            "file_path": "database/app.db",
            "status": "connected"
        }
        
        # 获取模型引擎信息
        models = AiModelRepository.get_all()
        
        self.render("settings_config.html", title="系统配置", db_info=db_info, models=models)


class SettingsLogsHandler(BaseHandler):
    """系统日志查看页面"""
    @tornado.web.authenticated
    def get(self):
        logs = []
        log_file = "app.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-100:]  # 只取最后100行
                for i, line in enumerate(lines, 1):
                    logs.append({"line": len(lines) - i + 1, "content": line.strip()})
                logs.reverse()
        
        self.render("settings_logs.html", title="系统日志", logs=logs)


class SettingsMonitorHandler(BaseHandler):
    """系统性能监控页面"""
    @tornado.web.authenticated
    def get(self):
        # 获取系统性能数据
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime = psutil.boot_time()
        
        # 获取进程信息
        process = psutil.Process()
        process_memory = process.memory_info().rss / (1024 * 1024)
        process_cpu = process.cpu_percent(interval=0.1)
        
        # 获取网络信息
        net_io = psutil.net_io_counters()
        
        monitor_data = {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count()
            },
            "memory": {
                "total": round(memory.total / (1024 ** 3), 2),
                "used": round(memory.used / (1024 ** 3), 2),
                "available": round(memory.available / (1024 ** 3), 2),
                "percent": memory.percent
            },
            "disk": {
                "total": round(disk.total / (1024 ** 3), 2),
                "used": round(disk.used / (1024 ** 3), 2),
                "free": round(disk.free / (1024 ** 3), 2),
                "percent": disk.percent
            },
            "process": {
                "memory": round(process_memory, 2),
                "cpu": process_cpu,
                "pid": process.pid,
                "uptime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(uptime))
            },
            "network": {
                "bytes_sent": round(net_io.bytes_sent / (1024 ** 2), 2),
                "bytes_recv": round(net_io.bytes_recv / (1024 ** 2), 2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        }
        
        self.render("settings_monitor.html", title="性能监控", monitor=monitor_data)


class SettingsAnalysisHandler(BaseHandler):
    """日志分析页面"""
    @tornado.web.authenticated
    def get(self):
        # 简单的日志分析（模拟数据）
        analysis_data = {
            "total_requests": 12580,
            "today_requests": 342,
            "avg_response_time": 125,
            "error_rate": 0.8,
            "top_endpoints": [
                {"endpoint": "/admin/dashboard", "count": 1856},
                {"endpoint": "/admin/user/list", "count": 1234},
                {"endpoint": "/admin/ai_model/list", "count": 987},
                {"endpoint": "/admin/skill/list", "count": 876},
                {"endpoint": "/admin/employee/list", "count": 765}
            ],
            "response_time_dist": [
                {"range": "0-100ms", "count": 8540},
                {"range": "100-500ms", "count": 3250},
                {"range": "500-1000ms", "count": 650},
                {"range": ">1000ms", "count": 140}
            ],
            "hourly_requests": [
                {"hour": "00:00", "count": 23},
                {"hour": "04:00", "count": 15},
                {"hour": "08:00", "count": 156},
                {"hour": "12:00", "count": 289},
                {"hour": "16:00", "count": 342},
                {"hour": "20:00", "count": 198}
            ],
            "error_types": [
                {"type": "404 Not Found", "count": 45},
                {"type": "500 Internal Error", "count": 23},
                {"type": "403 Forbidden", "count": 18},
                {"type": "401 Unauthorized", "count": 12}
            ]
        }
        
        analysis_json = json.dumps(analysis_data, ensure_ascii=False)
        
        self.render("settings_analysis.html", title="日志分析", analysis=analysis_data, analysis_json=analysis_json)


class SettingsMonitorDataHandler(BaseHandler):
    """性能监控数据API"""
    @tornado.web.authenticated
    def get(self):
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        process = psutil.Process()
        
        data = {
            "timestamp": int(time.time()),
            "cpu": cpu_percent,
            "memory": memory.percent,
            "process_memory": round(process.memory_info().rss / (1024 * 1024), 2),
            "process_cpu": process.cpu_percent(interval=0.01)
        }
        
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))
