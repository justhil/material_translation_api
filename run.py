import os
import sys
import logging
import uvicorn

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def ensure_directories():
    """确保必要的目录存在"""
    logger.info("检查数据目录...")
    
    # 获取项目根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 确保数据目录存在
    data_dir = os.path.join(base_dir, "app", "data")
    terminology_dir = os.path.join(data_dir, "terminology")
    examples_dir = os.path.join(data_dir, "examples")
    references_dir = os.path.join(data_dir, "references")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(terminology_dir, exist_ok=True)
    os.makedirs(examples_dir, exist_ok=True)
    os.makedirs(references_dir, exist_ok=True)
    
    logger.info("数据目录检查完成")

def check_database():
    """检查并初始化数据库"""
    logger.info("检查数据库...")
    from app.db.database import db
    
    # 初始化数据库（创建表等）
    if db.init_db():
        logger.info("数据库初始化成功")
    else:
        logger.error("数据库初始化失败")
        sys.exit(1)

def main():
    """主函数"""
    logger.info("启动应用...")
    
    # 确保目录存在
    ensure_directories()
    
    # 检查并初始化数据库
    check_database()
    
    # 启动应用
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        access_log=True
    )

if __name__ == "__main__":
    main() 