from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from pydantic import BaseModel
import logging

from app.services.llm_service import llm_service
from app.core.config import settings
from app.models.schemas import Model, ApiConfig

logger = logging.getLogger(__name__)

# 添加调试日志，确认模块已加载
logger.info("🚀 加载models.py模块，创建API路由")

router = APIRouter()

@router.get("/available", response_model=List[Model])
async def get_available_models():
    """
    获取可用的模型列表
    
    从API获取模型列表，使用环境变量中配置的API设置
    """
    logger.info("📝 接收到获取可用模型的请求")
    try:
        models = await llm_service.get_available_models()
        logger.info(f"✅ 获取到 {len(models)} 个可用模型")
        return models
    except Exception as e:
        logger.error(f"❌ 获取可用模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取可用模型失败: {str(e)}")

@router.get("/config", response_model=ApiConfig)
async def get_api_config():
    """
    获取当前API配置
    
    返回环境变量中的API配置信息
    """
    logger.info("📝 接收到获取API配置的请求")
    # 始终从环境变量读取API配置
    return ApiConfig(
        enabled=settings.CUSTOM_API_ENABLED,
        api_key="*******" if settings.CUSTOM_API_KEY else None,  # 隐藏实际API密钥
        base_url=settings.CUSTOM_API_BASE_URL,
        api_version=settings.CUSTOM_API_VERSION
    ) 