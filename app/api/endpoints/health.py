from fastapi import APIRouter
import time

from app.models.schemas import SystemHealth
from app.core.config import settings

router = APIRouter()

# 记录应用启动时间
start_time = time.time()


@router.get("/health", response_model=SystemHealth, summary="健康检查")
async def health_check():
    """
    健康检查API端点
    
    返回API服务的当前状态、版本和运行时间。
    """
    return SystemHealth(
        status="healthy",
        version=settings.API_VERSION,
        uptime=time.time() - start_time
    ) 