from fastapi import APIRouter

from app.api.endpoints import system, data, translation, evaluation, reference, models, terminology, health

api_router = APIRouter()

# 包含各模块的路由
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(translation.router, prefix="/translation", tags=["translation"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
api_router.include_router(reference.router, prefix="/reference", tags=["reference"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(terminology.router, prefix="/terminology", tags=["terminology"])
api_router.include_router(health.router, tags=["health"])  # 添加健康检查路由，不带前缀 