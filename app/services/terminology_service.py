import json
import logging
from typing import Dict, List, Optional, Tuple, Any

from app.db.database import db
from app.models.schemas import TerminologyEntry

logger = logging.getLogger(__name__)

class TerminologyService:
    """术语库服务，专门处理术语库相关操作"""
    
    def __init__(self):
        # 初始化数据库
        db.init_db()
    
    def get_all_terminology(self, domain: str, source_lang: str, target_lang: str) -> List[Dict[str, Any]]:
        """
        获取特定领域和语言的所有术语
        
        Args:
            domain: 领域名称
            source_lang: 源语言代码
            target_lang: 目标语言代码
            
        Returns:
            术语条目列表
        """
        try:
            query = """
            SELECT * FROM terminology 
            WHERE domain = ? AND source_language = ? AND target_language = ?
            ORDER BY source_term
            """
            result = db.fetch_all(query, (domain, source_lang, target_lang))
            
            # 将sqlite3.Row对象转换为字典列表
            terminology_entries = [dict(row) for row in result]
            return terminology_entries
        except Exception as e:
            logger.error(f"获取术语列表失败: {str(e)}")
            return []
    
    def get_simplified_terminology(self, domain: str, source_lang: str, target_lang: str) -> Dict[str, str]:
        """
        获取简化的术语对照表，格式为{source_term: target_term}
        
        Args:
            domain: 领域名称
            source_lang: 源语言代码
            target_lang: 目标语言代码
            
        Returns:
            术语及其译文的字典
        """
        try:
            query = """
            SELECT source_term, target_term FROM terminology 
            WHERE domain = ? AND source_language = ? AND target_language = ?
            """
            result = db.fetch_all(query, (domain, source_lang, target_lang))
            
            # 构建简化术语字典
            simplified_terms = {}
            for row in result:
                simplified_terms[row['source_term']] = row['target_term']
                
            return simplified_terms
        except Exception as e:
            logger.error(f"获取简化术语列表失败: {str(e)}")
            return {}
    
    def add_terminology(self, source_term: str, target_term: str, 
                      domain: str, source_lang: str, target_lang: str, 
                      definition: Optional[str] = None) -> bool:
        """
        添加或更新术语
        
        Args:
            source_term: 源语言术语
            target_term: 目标语言术语
            domain: 领域名称
            source_lang: 源语言代码
            target_lang: 目标语言代码
            definition: 术语定义
            
        Returns:
            是否成功
        """
        try:
            # 检查术语是否已存在
            query = """
            SELECT id FROM terminology 
            WHERE source_term = ? AND domain = ? AND source_language = ? AND target_language = ?
            """
            existing = db.fetch_one(query, (source_term, domain, source_lang, target_lang))
            
            if existing:
                # 更新已存在的术语
                update_query = """
                UPDATE terminology 
                SET target_term = ?, definition = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """
                db.execute(update_query, (target_term, definition, existing['id']))
                logger.info(f"更新术语: {source_term} -> {target_term}")
            else:
                # 添加新术语
                insert_query = """
                INSERT INTO terminology 
                (source_term, target_term, domain, source_language, target_language, definition)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                db.execute(insert_query, (source_term, target_term, domain, source_lang, target_lang, definition))
                logger.info(f"添加新术语: {source_term} -> {target_term}")
            
            return True
        except Exception as e:
            logger.error(f"添加/更新术语失败: {str(e)}")
            return False
    
    def delete_terminology(self, term_id: int) -> bool:
        """
        删除术语
        
        Args:
            term_id: 术语ID
            
        Returns:
            是否成功
        """
        try:
            query = "DELETE FROM terminology WHERE id = ?"
            db.execute(query, (term_id,))
            logger.info(f"删除术语ID: {term_id}")
            return True
        except Exception as e:
            logger.error(f"删除术语失败: {str(e)}")
            return False
    
    def import_from_json(self, json_data: Any, domain: str = 'materials_science', 
                       source_lang: str = 'zh', target_lang: str = 'en') -> int:
        """
        从JSON数据导入术语库，支持两种格式：
        1. 简化格式: {"源术语1": "目标术语1", "源术语2": "目标术语2"}
        2. 完整格式: [{"source_term": "源术语1", "target_term": "目标术语1", ...}, ...]
        
        Args:
            json_data: 包含术语数据的JSON对象或列表
            domain: 默认领域名称（简化格式使用）
            source_lang: 默认源语言代码（简化格式使用）
            target_lang: 默认目标语言代码（简化格式使用）
            
        Returns:
            导入的术语数量
        """
        try:
            count = 0
            
            # 检查数据类型并处理
            if isinstance(json_data, dict):
                # 简化格式: {"源术语": "目标术语"}
                for source_term, target_term in json_data.items():
                    if source_term and target_term:
                        success = self.add_terminology(
                            source_term, target_term, domain, source_lang, target_lang, None
                        )
                        if success:
                            count += 1
            elif isinstance(json_data, list):
                # 完整格式: [{"source_term": "...", ...}]
                for item in json_data:
                    # 提取术语信息
                    source_term = item.get('source_term')
                    target_term = item.get('target_term')
                    item_domain = item.get('domain', domain)
                    item_source_lang = item.get('source_language', source_lang)
                    item_target_lang = item.get('target_language', target_lang)
                    definition = item.get('definition')
                    
                    if not (source_term and target_term):
                        logger.warning(f"跳过无效术语数据: {item}")
                        continue
                    
                    # 添加术语
                    success = self.add_terminology(
                        source_term, target_term, item_domain, item_source_lang, item_target_lang, definition
                    )
                    
                    if success:
                        count += 1
            
            logger.info(f"成功导入{count}个术语")
            return count
        except Exception as e:
            logger.error(f"导入术语库失败: {str(e)}")
            return 0
    
    def export_to_json(self, domain: str, source_lang: str, target_lang: str) -> List[Dict[str, Any]]:
        """
        导出术语库到JSON格式
        
        Args:
            domain: 领域名称
            source_lang: 源语言代码
            target_lang: 目标语言代码
            
        Returns:
            术语库JSON数据
        """
        try:
            terminology = self.get_all_terminology(domain, source_lang, target_lang)
            return terminology
        except Exception as e:
            logger.error(f"导出术语库失败: {str(e)}")
            return []


# 单例实例
terminology_service = TerminologyService() 