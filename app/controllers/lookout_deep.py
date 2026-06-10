# 深度采集控制器
import json
import tornado.web
from app.controllers.base import BaseHandler
from app.models.lookout import LookoutRecordRepository
from app.models.lookout_deep import (
    LookoutDeepRecordRepository,
    LookoutDeepCrawler,
    LookoutDeepAIProcessor,
)


class LookoutDeepHandler(BaseHandler):
    """深度采集页面"""
    @tornado.web.authenticated
    def get(self):
        self.render("lookout_deep.html", title="AI深度采集")


class LookoutDeepStartHandler(BaseHandler):
    """开始深度采集（单条或多条）"""
    @tornado.web.authenticated
    def post(self):
        record_ids = self.get_body_argument("record_ids", "").strip()
        if not record_ids:
            return self.write(json.dumps({"code": 1, "msg": "请选择要采集的记录"}))
        
        ids = [int(x) for x in record_ids.split(",") if x.strip()]
        records = LookoutRecordRepository.get_by_ids(ids)
        
        logs = []
        success_count = 0
        fail_count = 0
        
        for record in records:
            try:
                logs.append(f"开始处理: {record['title']}")
                
                deep_record = LookoutDeepRecordRepository.get_by_record_id(record['id'])
                if not deep_record:
                    LookoutDeepRecordRepository.create(
                        record['id'], record['source_id'], record['url']
                    )
                    logs.append(f"  ✅ 创建深度采集记录")
                
                logs.append(f"  🕷️ 开始爬取网页...")
                html_content, error = LookoutDeepCrawler.crawl_url(record['url'])
                if error:
                    LookoutDeepRecordRepository.update_crawl(record['id'], '', error_message=error)
                    logs.append(f"  ❌ 爬取失败: {error}")
                    fail_count += 1
                    continue
                
                logs.append(f"  ✅ 爬取成功，提取内容...")
                main_content = LookoutDeepCrawler.extract_main_content(html_content)
                LookoutDeepRecordRepository.update_crawl(record['id'], main_content)
                
                logs.append(f"  🤖 开始AI深度分析...")
                summary, keywords, analysis, features, anomalies, relations, distribution, ai_error = LookoutDeepAIProcessor.analyze_content(
                    main_content, record['title']
                )
                
                if ai_error:
                    LookoutDeepRecordRepository.update_ai(record['id'], '', '', '', error_message=ai_error)
                    logs.append(f"  ❌ AI分析失败: {ai_error}")
                    fail_count += 1
                else:
                    LookoutDeepRecordRepository.update_ai(
                        record['id'], summary, keywords, analysis,
                        features, anomalies, relations, distribution
                    )
                    
                    from app.models.db import get_connection
                    with get_connection() as conn:
                        conn.execute(
                            "UPDATE lookout_records SET deep_status='completed', deep_record_id=(SELECT id FROM lookout_deep_records WHERE record_id=?) WHERE id=?",
                            (record['id'], record['id'])
                        )
                    
                    logs.append(f"  ✅ AI分析完成")
                    logs.append(f"    - 摘要生成成功")
                    logs.append(f"    - 关键词提取: {len(keywords.split('，')) if keywords else 0} 个")
                    logs.append(f"    - 特征分析完成")
                    logs.append(f"    - 异常检测完成")
                    logs.append(f"    - 关联分析完成")
                    logs.append(f"    - 分布分析完成")
                    success_count += 1
                    
            except Exception as e:
                logs.append(f"  ❌ 处理异常: {str(e)}")
                fail_count += 1
        
        summary = {
            "total": len(ids),
            "success": success_count,
            "failed": fail_count,
            "logs": logs,
        }
        self.write(json.dumps({"code": 0, "msg": "采集完成", "data": summary}))


class LookoutDeepStatusHandler(BaseHandler):
    """获取深度采集统计"""
    @tornado.web.authenticated
    def get(self):
        stats = LookoutDeepRecordRepository.get_statistics()
        keyword_stats = LookoutDeepRecordRepository.get_keyword_statistics()
        self.write(json.dumps({"code": 0, "data": {**stats, "top_keywords": keyword_stats}}))


class LookoutDeepGetHandler(BaseHandler):
    """获取深度采集详情"""
    @tornado.web.authenticated
    def get(self):
        record_id = int(self.get_argument("record_id", 0))
        if not record_id:
            return self.write(json.dumps({"code": 1, "msg": "缺少参数"}))
        
        deep_record = LookoutDeepRecordRepository.get_by_record_id(record_id)
        if not deep_record:
            return self.write(json.dumps({"code": 1, "msg": "未找到深度采集记录"}))
        
        self.write(json.dumps({"code": 0, "data": deep_record}))


class LookoutDeepListHandler(BaseHandler):
    """获取深度采集列表"""
    @tornado.web.authenticated
    def get(self):
        page = int(self.get_argument("page", 1))
        page_size = int(self.get_argument("page_size", 20))
        
        from app.models.db import get_connection
        with get_connection() as conn:
            offset = (page - 1) * page_size
            rows = conn.execute(
                """SELECT dr.*, lr.title, lr.source_id, lr.url
                   FROM lookout_deep_records dr
                   LEFT JOIN lookout_records lr ON dr.record_id = lr.id
                   ORDER BY dr.id DESC LIMIT ? OFFSET ?""",
                (page_size, offset),
            ).fetchall()
            
            total = conn.execute(
                "SELECT COUNT(*) AS cnt FROM lookout_deep_records"
            ).fetchone()["cnt"]
        
        items = []
        for row in rows:
            item = dict(row)
            item['status_text'] = self._get_status_text(item['crawl_status'], item['ai_status'])
            items.append(item)
        
        self.write(json.dumps({
            "code": 0,
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": items,
            }
        }))
    
    def _get_status_text(self, crawl_status, ai_status):
        if crawl_status == 'failed':
            return '爬取失败'
        if crawl_status == 'pending':
            return '待爬取'
        if ai_status == 'failed':
            return '分析失败'
        if ai_status == 'pending':
            return '待分析'
        return '已完成'


class LookoutDeepDeleteHandler(BaseHandler):
    """删除深度采集记录"""
    @tornado.web.authenticated
    def post(self):
        record_id = int(self.get_body_argument("record_id", 0))
        if not record_id:
            return self.write(json.dumps({"code": 1, "msg": "缺少参数"}))
        
        LookoutDeepRecordRepository.delete(record_id)
        
        from app.models.db import get_connection
        with get_connection() as conn:
            conn.execute(
                "UPDATE lookout_records SET deep_status='pending', deep_record_id=0 WHERE id=?",
                (record_id,)
            )
        
        self.write(json.dumps({"code": 0, "msg": "删除成功"}))


class LookoutDeepSyncHandler(BaseHandler):
    """从数据仓库同步待深度采集的记录"""
    @tornado.web.authenticated
    def post(self):
        from app.models.lookout import LookoutRecordRepository
        
        count_param = self.get_body_argument("count", "0")
        max_count = int(count_param) if count_param and count_param.isdigit() and int(count_param) > 0 else 50
        
        # 获取仓库中未深度采集的记录
        warehouse_data = LookoutRecordRepository.get_page(page=1, page_size=max_count, deep_status='pending')
        items = warehouse_data.get('items', [])
        
        synced = 0
        for item in items:
            deep_record = LookoutDeepRecordRepository.get_by_record_id(item['id'])
            if not deep_record:
                LookoutDeepRecordRepository.create(item['id'], item['source_id'], item['url'])
                synced += 1
        
        self.write(json.dumps({
            "code": 0,
            "msg": f"同步完成，新增 {synced} 条记录",
            "data": {"synced": synced, "total": len(items)}
        }))


class LookoutDeepAnalysisHandler(BaseHandler):
    """获取深度分析报告（汇总统计）"""
    @tornado.web.authenticated
    def get(self):
        stats = LookoutDeepRecordRepository.get_statistics()
        keywords = LookoutDeepRecordRepository.get_keyword_statistics(15)
        time_trend = LookoutDeepRecordRepository.get_time_trend()
        source_dist = LookoutDeepRecordRepository.get_source_distribution()
        length_dist = LookoutDeepRecordRepository.get_content_length_distribution()
        status_dist = LookoutDeepRecordRepository.get_status_trend()
        
        report = {
            "overview": {
                "total_records": stats["total"],
                "completed_records": stats["completed"],
                "pending_records": stats["pending"],
                "failed_records": stats["failed"],
                "completion_rate": round((stats["completed"] / max(stats["total"], 1)) * 100, 2),
                "avg_content_length": stats["avg_content_length"],
            },
            "top_keywords": keywords,
            "charts": {
                "time_trend": time_trend,
                "source_distribution": source_dist,
                "content_length_distribution": length_dist,
                "status_distribution": status_dist,
            },
            "analysis_summary": {
                "description": "基于AI深度分析的综合报告",
                "analysis_types": [
                    {"name": "内容摘要", "description": "提取文章核心内容"},
                    {"name": "关键词提取", "description": "识别重要概念和实体"},
                    {"name": "特征分析", "description": "分析内容类型和结构"},
                    {"name": "异常检测", "description": "发现异常值和矛盾信息"},
                    {"name": "关联分析", "description": "揭示实体间关系"},
                    {"name": "分布趋势", "description": "分析数据分布和趋势"},
                ],
            },
        }
        
        self.write(json.dumps({"code": 0, "data": report}))
