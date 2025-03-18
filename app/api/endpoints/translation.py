from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import logging

from app.models.schemas import TranslationRequest, TranslationResponse
from app.services.llm_service import llm_service
from app.services.data_service import data_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/translate", response_model=TranslationResponse, summary="翻译文本")
async def translate_text(request: TranslationRequest):
    """
    翻译文本API端点
    
    将源语言的文本翻译成目标语言，支持术语匹配和领域特定翻译。
    
    - **source_text**: 源文本内容
    - **source_language**: 源语言代码，例如'zh'表示中文
    - **target_language**: 目标语言代码，例如'en'表示英语
    - **domain**: 领域类型，默认为materials_science
    - **model**: 可选的模型ID
    - **reference_texts**: 可选的参考译文，用于评估
    
    返回翻译后的文本和使用的模型信息。
    """
    try:
        # 记录请求信息
        logger.info(f"收到翻译请求: source_lang={request.source_language}, target_lang={request.target_language}, model={request.model}")
        
        # 获取术语匹配
        terminology = data_service.get_terminology_match(
            request.source_text, 
            request.domain, 
            request.source_language, 
            request.target_language
        )
        
        logger.info(f"调用LLM服务进行翻译，使用模型: {request.model}")
        
        # 调用LLM服务进行翻译
        translation_result = await llm_service.translate_text(
            request.source_text,
            request.source_language,
            request.target_language,
            request.model
        )
        
        logger.info(f"翻译完成，使用模型: {translation_result['model_used']}")
        
        # 构建响应
        return TranslationResponse(
            source_text=request.source_text,
            translated_text=translation_result["translated_text"],
            model=translation_result["model_used"],
            source_language=request.source_language,
            target_language=request.target_language,
            domain=request.domain
        )
    except Exception as e:
        logger.error(f"翻译服务出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"翻译服务出错: {str(e)}") 