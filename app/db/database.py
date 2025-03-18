import os
import sqlite3
import logging
from typing import Dict, List, Tuple, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class Database:
    """SQLite数据库连接管理类"""
    
    def __init__(self):
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
        self.db_path = settings.DATABASE_PATH
        self.connection = None
        
    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            # 启用外键约束
            self.connection.execute("PRAGMA foreign_keys = ON")
            # 设置行工厂为字典
            self.connection.row_factory = sqlite3.Row
            return self.connection
        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
    
    def get_connection(self):
        """获取数据库连接，如果未连接则先建立连接"""
        if self.connection is None:
            return self.connect()
        return self.connection
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute(self, query: str, params: tuple = ()):
        """执行SQL语句"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"SQL执行失败: {str(e)}, 查询: {query}, 参数: {params}")
            raise
    
    def fetch_all(self, query: str, params: tuple = ()):
        """执行查询并返回所有结果"""
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query: str, params: tuple = ()):
        """执行查询并返回一个结果"""
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def init_db(self):
        """初始化数据库，创建必要的表"""
        try:
            # 术语表
            self.execute('''
            CREATE TABLE IF NOT EXISTS terminology (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_term TEXT NOT NULL,
                target_term TEXT NOT NULL,
                domain TEXT NOT NULL,
                source_language TEXT NOT NULL,
                target_language TEXT NOT NULL,
                definition TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_term, domain, source_language, target_language)
            )
            ''')
            
            logger.info("数据库初始化成功")
            return True
        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            return False


# 单例模式
db = Database() 