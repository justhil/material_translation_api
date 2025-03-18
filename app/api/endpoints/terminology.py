from fastapi import APIRouter, HTTPException, Depends, Body, UploadFile, File, Form
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from app.services.llm_service import LLMService
from app.services.terminology_service import terminology_service
from app.models.schemas import TranslationRequest
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

class TerminologyExtractionRequest(BaseModel):
    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    domain: str = "general"

class TerminologyExtractionResponse(BaseModel):
    terms: Dict[str, str]
    message: str

class BatchTerminologyEntry(BaseModel):
    source_term: str
    target_term: str
    
class BatchTerminologyRequest(BaseModel):
    entries: List[BatchTerminologyEntry]
    domain: str = "materials_science"
    source_lang: str = "zh"
    target_lang: str = "en"

class BatchTerminologyResponse(BaseModel):
    count: int
    message: str

@router.post("/extract", response_model=TerminologyExtractionResponse)
async def extract_terminology(
    request: TerminologyExtractionRequest,
    llm_service: LLMService = Depends(LLMService)
):
    """
    从源文本和翻译文本中提取术语对照表
    """
    try:
        logger.info(f"开始从文本中提取术语，领域: {request.domain}, 语言对: {request.source_language}-{request.target_language}")
        
        # 构建提示词
        prompt = f"""
        请从以下材料科学领域的文本中提取专业术语，并给出对应的翻译。
        
        源语言({request.source_language})文本:
        {request.source_text}
        
        目标语言({request.target_language})文本:
        {request.translated_text}
        
        领域: {request.domain}
        
        请以JSON格式返回提取的术语对照表，格式为:
        {{
            "源语言术语1": "目标语言术语1",
            "源语言术语2": "目标语言术语2",
            ...
        }}
        
        只返回JSON格式的结果，不要有其他文字说明。
        """
        
        # 调用LLM服务提取术语
        completion_result = llm_service.get_ai_completion(prompt)
        
        if not completion_result or not completion_result.get("content"):
            logger.warning("LLM服务返回空结果")
            return TerminologyExtractionResponse(
                terms={},
                message="无法从文本中提取术语"
            )
        
        # 尝试解析JSON结果
        import re
        
        content = completion_result.get("content", "")
        
        # 尝试从内容中提取JSON部分
        json_match = re.search(r'({[\s\S]*})', content)
        if json_match:
            content = json_match.group(1)
        
        try:
            terms = json.loads(content)
            if not isinstance(terms, dict):
                logger.warning(f"解析的术语不是字典格式: {type(terms)}")
                terms = {}
        except json.JSONDecodeError as e:
            logger.error(f"解析术语JSON失败: {e}, 内容: {content}")
            terms = {}
        
        return TerminologyExtractionResponse(
            terms=terms,
            message=f"成功从文本中提取了 {len(terms)} 个术语"
        )
        
    except Exception as e:
        logger.error(f"提取术语时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提取术语失败: {str(e)}")

@router.get("/database", response_model=List[Dict[str, str]])
async def get_terminology_database(
    domain: str = "general",
    source_lang: str = "en",
    target_lang: str = "zh"
):
    """
    获取术语库数据
    """
    try:
        # 使用术语服务从数据库获取术语
        terminology_entries = terminology_service.get_all_terminology(domain, source_lang, target_lang)
        return terminology_entries
    except Exception as e:
        logger.error(f"获取术语库时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取术语库失败: {str(e)}")

@router.post("/batch", response_model=BatchTerminologyResponse)
async def batch_add_terminology(
    request: BatchTerminologyRequest
):
    """
    批量添加术语到术语库
    """
    try:
        logger.info(f"开始批量添加术语，领域: {request.domain}, 语言对: {request.source_lang}-{request.target_lang}")
        
        success_count = 0
        
        for entry in request.entries:
            result = terminology_service.add_terminology(
                source_term=entry.source_term,
                target_term=entry.target_term,
                domain=request.domain,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                definition=None
            )
            
            if result:
                success_count += 1
        
        logger.info(f"批量添加术语完成，共添加 {success_count}/{len(request.entries)} 个术语")
        
        return BatchTerminologyResponse(
            count=success_count,
            message=f"成功添加 {success_count}/{len(request.entries)} 个术语"
        )
    except Exception as e:
        logger.error(f"批量添加术语时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量添加术语失败: {str(e)}") 