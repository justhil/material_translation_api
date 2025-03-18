from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """
    健康检查API端点
    
    返回API服务的当前状态和版本。
    """
    return HealthResponse(
        status="healthy",
        version=settings.API_VERSION
    )

@router.get("/info", summary="系统信息")
async def system_info():
    """
    获取系统信息
    
    返回系统的基本配置信息。
    """
    return {
        "name": "材料科学翻译质量评估系统",
        "version": settings.API_VERSION,
        "description": "用于评估材料科学领域翻译质量的API服务",
        "environment": settings.ENVIRONMENT,
        "features": [
            "翻译API集成",
            "BLEU评分",
            "术语准确性评估",
            "句式结构评估",
            "语篇连贯性评估",
            "参考文本管理",
            "术语提取与管理"
        ]
    } 