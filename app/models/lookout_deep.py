# 深度采集数据访问层
import json
import re
from app.models.db import get_connection

class LookoutDeepRecordRepository:
    @staticmethod
    def create(record_id, source_id, url):
        """创建深度采集记录"""
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO lookout_deep_records 
                   (record_id, source_id, url, crawl_status, ai_status)
                   VALUES (?, ?, ?, 'pending', 'pending')""",
                (record_id, source_id, url),
            )

    @staticmethod
    def get_by_record_id(record_id):
        """根据源记录ID获取深度采集记录"""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM lookout_deep_records WHERE record_id=?",
                (record_id,),
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_id(deep_id):
        """根据ID获取深度采集记录"""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM lookout_deep_records WHERE id=?",
                (deep_id,),
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_crawl(record_id, raw_content, crawl_time=None, error_message=None):
        """更新爬取状态"""
        with get_connection() as conn:
            status = 'success' if raw_content else 'failed'
            def safe_str(v):
                if v is None:
                    return ''
                if isinstance(v, (dict, list)):
                    return json.dumps(v, ensure_ascii=False)
                return str(v)
            content_length = len(safe_str(raw_content)) if raw_content else 0
            conn.execute(
                """UPDATE lookout_deep_records 
                   SET raw_content=?, crawl_status=?, crawl_time=?, error_message=?, 
                       content_length=?, update_at=datetime('now')
                   WHERE record_id=?""",
                (safe_str(raw_content), status, safe_str(crawl_time), safe_str(error_message), content_length, record_id),
            )

    @staticmethod
    def update_ai(record_id, ai_summary, ai_keywords, ai_analysis, ai_features=None, 
                  ai_anomalies=None, ai_relations=None, ai_distribution=None, process_time=None):
        """更新AI处理结果"""
        with get_connection() as conn:
            status = 'success' if ai_summary else 'failed'
            # 确保所有字段为字符串（防止AI返回JSON对象导致SQLite绑定错误）
            def safe_str(v):
                if v is None:
                    return ''
                if isinstance(v, (dict, list)):
                    return json.dumps(v, ensure_ascii=False)
                return str(v)
            conn.execute(
                """UPDATE lookout_deep_records 
                   SET ai_summary=?, ai_keywords=?, ai_analysis=?, ai_features=?, 
                       ai_anomalies=?, ai_relations=?, ai_distribution=?, ai_status=?, 
                       ai_process_time=?, update_at=datetime('now')
                   WHERE record_id=?""",
                (safe_str(ai_summary), safe_str(ai_keywords), safe_str(ai_analysis), safe_str(ai_features), 
                 safe_str(ai_anomalies), safe_str(ai_relations), safe_str(ai_distribution), 
                 status, safe_str(process_time), record_id),
            )

    @staticmethod
    def get_batch(limit=50):
        """获取待深度采集的记录（未完成或失败的）"""
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM lookout_deep_records 
                   WHERE crawl_status='pending' OR (crawl_status='success' AND ai_status='pending')
                   ORDER BY id LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_statistics():
        """获取深度采集统计"""
        with get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) AS cnt FROM lookout_deep_records"
            ).fetchone()["cnt"]
            completed = conn.execute(
                "SELECT COUNT(*) AS cnt FROM lookout_deep_records WHERE crawl_status='success' AND ai_status='success'"
            ).fetchone()["cnt"]
            pending = conn.execute(
                "SELECT COUNT(*) AS cnt FROM lookout_deep_records WHERE crawl_status='pending'"
            ).fetchone()["cnt"]
            failed = conn.execute(
                "SELECT COUNT(*) AS cnt FROM lookout_deep_records WHERE crawl_status='failed' OR ai_status='failed'"
            ).fetchone()["cnt"]
            
            avg_length = conn.execute(
                "SELECT AVG(content_length) AS avg FROM lookout_deep_records WHERE content_length > 0"
            ).fetchone()["avg"]
            
            return {
                "total": total,
                "completed": completed,
                "pending": pending,
                "failed": failed,
                "avg_content_length": int(avg_length) if avg_length else 0,
            }

    @staticmethod
    def delete(record_id):
        """删除深度采集记录"""
        with get_connection() as conn:
            conn.execute("DELETE FROM lookout_deep_records WHERE record_id=?", (record_id,))

    @staticmethod
    def get_keyword_statistics(top_n=10):
        """获取关键词统计（从所有已完成采集的记录中提取）"""
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT ai_keywords FROM lookout_deep_records WHERE ai_keywords IS NOT NULL AND ai_keywords != ''"
            ).fetchall()
        
        keyword_counts = {}
        for row in rows:
            keywords = row["ai_keywords"]
            if keywords:
                for kw in re.split(r'[，,、]', keywords):
                    kw = kw.strip()
                    if kw:
                        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [{"keyword": kw, "count": cnt} for kw, cnt in sorted_keywords]

    @staticmethod
    def get_time_trend():
        """获取时间趋势数据（按天统计采集记录数）"""
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT strftime('%Y-%m-%d', create_at) AS date, 
                          COUNT(*) AS total,
                          SUM(CASE WHEN crawl_status='success' AND ai_status='success' THEN 1 ELSE 0 END) AS completed
                   FROM lookout_deep_records 
                   GROUP BY date 
                   ORDER BY date ASC 
                   LIMIT 30"""
            ).fetchall()
            return [{"date": r["date"], "total": r["total"], "completed": r["completed"]} for r in rows]

    @staticmethod
    def get_source_distribution():
        """获取来源分布数据"""
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT COALESCE(s.name, '未知来源') AS source_name, COUNT(*) AS cnt
                   FROM lookout_deep_records dr
                   LEFT JOIN lookout_sources s ON dr.source_id = s.id
                   GROUP BY dr.source_id
                   ORDER BY cnt DESC"""
            ).fetchall()
            return [{"name": r["source_name"], "value": r["cnt"]} for r in rows]

    @staticmethod
    def get_content_length_distribution():
        """获取内容长度分布数据"""
        with get_connection() as conn:
            breaks = [
                (0, 500, "0-500"),
                (500, 1000, "500-1K"),
                (1000, 2000, "1K-2K"),
                (2000, 5000, "2K-5K"),
                (5000, 10000, "5K-10K"),
                (10000, 99999999, "10K+"),
            ]
            result = []
            for lo, hi, label in breaks:
                row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM lookout_deep_records WHERE content_length > ? AND content_length <= ?",
                    (lo, hi),
                ).fetchone()
                result.append({"name": label, "value": row["cnt"]})
            return result

    @staticmethod
    def get_status_trend():
        """获取各状态分布"""
        with get_connection() as conn:
            completed = conn.execute(
                "SELECT COUNT(*) AS cnt FROM lookout_deep_records WHERE crawl_status='success' AND ai_status='success'"
            ).fetchone()["cnt"]
            pending = conn.execute(
                "SELECT COUNT(*) AS cnt FROM lookout_deep_records WHERE crawl_status='pending'"
            ).fetchone()["cnt"]
            crawling = conn.execute(
                "SELECT COUNT(*) AS cnt FROM lookout_deep_records WHERE crawl_status='success' AND ai_status='pending'"
            ).fetchone()["cnt"]
            failed = conn.execute(
                "SELECT COUNT(*) AS cnt FROM lookout_deep_records WHERE crawl_status='failed' OR ai_status='failed'"
            ).fetchone()["cnt"]
            return [
                {"name": "已完成", "value": completed},
                {"name": "待爬取", "value": pending},
                {"name": "待分析", "value": crawling},
                {"name": "失败", "value": failed},
            ]


class LookoutDeepCrawler:
    """深度采集爬虫工具类"""
    
    @staticmethod
    def crawl_url(url, timeout=30):
        """爬取网页内容"""
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.encoding = response.apparent_encoding
            return response.text, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def extract_main_content(html_content):
        """提取网页主要内容"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            
            for script in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                script.decompose()
            
            content_divs = soup.find_all(['article', 'main', 'div', 'section'], 
                                         class_=['article', 'content', 'main-content', 'article-content'])
            
            if content_divs:
                main_content = content_divs[0].get_text(strip=True)
            else:
                body = soup.find('body')
                main_content = body.get_text(strip=True) if body else ''
            
            return main_content.strip()[:10000]
        except Exception as e:
            return f"提取内容失败: {str(e)}"


class LookoutDeepAIProcessor:
    """AI深度分析处理器"""
    
    @staticmethod
    def analyze_content(raw_content, record_title):
        """使用AI分析内容（增强版：包含特征分析、异常检测、关联关系、分布趋势）"""
        from app.models.ai_model import AiModelRepository
        
        default_model = AiModelRepository.get_default()
        if not default_model:
            return None, None, None, None, None, None, None, "未找到默认模型"
        
        try:
            prompt = f"""请对以下网页内容进行全面深度分析：
            
【标题】{record_title}

【内容】
{raw_content[:3000]}

请输出JSON格式结果，包含以下字段：
{{
    "summary": "内容摘要（100-200字）",
    "keywords": "关键词，逗号分隔，提取最重要的5-10个",
    "analysis": "深度分析（300-500字）",
    "features": "数据特征分析：内容类型、主要结构、核心主题、语言风格",
    "anomalies": "异常值检测：内容中的异常点、矛盾信息、不寻常的数据",
    "relations": "关联关系：内容中提到的实体之间的关系、事件之间的联系",
    "distribution": "分布趋势：内容中数据的分布情况、时间趋势、频率分布"
}}

请确保每个字段都有具体内容，不要留空。
"""
            
            # 直接使用OpenAI客户端调用模型
            try:
                from openai import OpenAI
                import httpx
                
                client = OpenAI(
                    api_key=default_model["api_key"],
                    base_url=default_model["base_url"],
                    http_client=httpx.Client(timeout=120.0),
                )
                
                response = client.chat.completions.create(
                    model=default_model["model_name"],
                    messages=[
                        {"role": "system", "content": "你是一个专业的AI数据分析师，擅长对网页内容进行深度分析和挖掘。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4096,
                    temperature=0.7,
                )
                
                result = response.choices[0].message.content
                
                # 记录token消耗
                if response.usage:
                    AiModelRepository.log_chat(
                        default_model["id"],
                        response.usage.prompt_tokens or 0,
                        response.usage.completion_tokens or 0,
                    )
            except ImportError:
                return None, None, None, None, None, None, None, "OpenAI SDK 未安装，请执行: pip install openai httpx"
            except Exception as e:
                return None, None, None, None, None, None, None, f"模型调用失败: {str(e)}"
            
            if result:
                try:
                    data = json.loads(result)
                    # 确保返回的字段都是字符串（防止AI返回JSON对象）
                    def safe_str(v):
                        if v is None:
                            return ''
                        if isinstance(v, (dict, list)):
                            return json.dumps(v, ensure_ascii=False)
                        return str(v)
                    return (
                        safe_str(data.get('summary')),
                        safe_str(data.get('keywords')),
                        safe_str(data.get('analysis')),
                        safe_str(data.get('features')),
                        safe_str(data.get('anomalies')),
                        safe_str(data.get('relations')),
                        safe_str(data.get('distribution')),
                        None
                    )
                except json.JSONDecodeError:
                    return result[:200], "", "", "", "", "", "", "AI返回格式错误"
            
            return None, None, None, None, None, None, None, "模型返回为空"
        except Exception as e:
            return None, None, None, None, None, None, None, str(e)
