from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Optional

from app.models.schemas import EvaluationRequest, EvaluationResponse, ScoringCriteria
from app.services.evaluation_service import evaluation_service
from app.core.config import settings

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_translation(request: EvaluationRequest):
    """
    评估翻译质量，支持BLEU评分、术语准确性评估、句式转换和语篇连贯性分析。
    需要提供源文本、译文和至少一个参考文本才能进行完整评估。
    如果未提供参考文本，某些指标将无法准确计算。
    """
    try:
        # 确保有至少一个参考文本
        if not request.reference_texts:
            raise HTTPException(status_code=400, detail="至少需要提供一个参考文本进行评估")
        
        # 调用评估服务评估翻译质量
        evaluation_result = evaluation_service.evaluate_translation(
            source_text=request.source_text,
            translated_text=request.translated_text,
            reference_texts=request.reference_texts,
            source_language=request.source_language,
            target_language=request.target_language,
            domain=request.domain
        )
        return evaluation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估翻译时出错: {str(e)}")


@router.get("/scoring-criteria", response_model=Dict[str, ScoringCriteria])
async def get_scoring_criteria():
    """
    获取评分标准说明，包括每项指标的计算方法、权重和分数解释
    """
    return {
        "overall_score": ScoringCriteria(
            name="综合得分",
            description="综合评估翻译质量的总体得分，基于BLEU分数、术语准确性、句式转换和语篇连贯性加权计算得到。",
            calculation="各项指标的加权平均值，权重可在系统配置中调整。",
            weight="100%",
            interpretation={
                "0.8-1.0": "优秀",
                "0.6-0.8": "良好",
                "0.4-0.6": "一般",
                "0.0-0.4": "较差"
            }
        ),
        "bleu_score": ScoringCriteria(
            name="BLEU分数",
            description="衡量翻译与参考译文之间的相似度，是最常用的机器翻译自动评估指标之一。",
            calculation="基于n-gram精确度计算，结合了句子级BLEU和语料级BLEU，针对短文本进行了优化。",
            weight="30%",
            interpretation={
                "0.8-1.0": "译文与参考译文高度匹配",
                "0.6-0.8": "译文与参考译文匹配度良好",
                "0.4-0.6": "译文与参考译文匹配度一般",
                "0.0-0.4": "译文与参考译文差异较大"
            }
        ),
        "terminology_accuracy": ScoringCriteria(
            name="术语准确性",
            description="评估专业术语翻译的准确程度，对于专业领域翻译尤为重要。",
            calculation="根据术语库或从参考文本中提取的术语对照，计算正确翻译的术语比例。",
            weight="30%",
            interpretation={
                "0.8-1.0": "术语翻译准确性高",
                "0.6-0.8": "术语翻译准确性良好",
                "0.4-0.6": "术语翻译准确性一般",
                "0.0-0.4": "术语翻译准确性较低"
            }
        ),
        "sentence_structure": ScoringCriteria(
            name="句式转换",
            description="评估译文是否恰当地进行了句式转换，特别是中译英时主动句转被动句的情况。",
            calculation="检测源文本中的主动句和译文中的被动句，计算转换的合理性。",
            weight="20%",
            interpretation={
                "0.8-1.0": "句式转换恰当",
                "0.6-0.8": "句式转换基本合理",
                "0.4-0.6": "句式转换存在问题",
                "0.0-0.4": "句式转换不恰当"
            }
        ),
        "discourse_coherence": ScoringCriteria(
            name="语篇连贯性",
            description="评估译文的逻辑连贯性、句子间过渡和整体流畅度。",
            calculation="基于连接词使用、句长变化、词语重复和指代一致性等因素综合评分。",
            weight="20%",
            interpretation={
                "0.8-1.0": "语篇连贯性优秀",
                "0.6-0.8": "语篇连贯性良好",
                "0.4-0.6": "语篇连贯性一般",
                "0.0-0.4": "语篇连贯性较差"
            }
        )
    }


@router.post("/extract-terms")
async def extract_terms(
    source_text: str = Body(..., description="源文本"),
    translated_text: str = Body(..., description="译文"),
    source_language: str = Body("zh", description="源语言代码"),
    target_language: str = Body("en", description="目标语言代码"),
    domain: str = Body("materials_science", description="领域"),
    mode: str = Body("ai_extraction", description="提取模式: ai_extraction, reference或database"),
    reference_text: Optional[str] = Body(None, description="参考译文，仅在mode=reference时需要")
):
    """
    从文本中提取术语对照表
    支持三种模式：AI提取、从参考文本提取、从术语库提取
    """
    try:
        if mode == "reference" and not reference_text:
            raise HTTPException(status_code=400, detail="参考文本模式需要提供参考译文")
        
        extracted_terms = {}
        
        if mode == "ai_extraction":
            # 使用AI提取术语
            _, _, extracted_terms = evaluation_service._evaluate_terminology_with_ai(
                source_text=source_text,
                translated_text=translated_text,
                domain=domain,
                source_language=source_language,
                target_language=target_language
            )
        elif mode == "reference":
            # 从参考文本提取术语
            _, _, extracted_terms = evaluation_service._evaluate_terminology_from_reference(
                source_text=source_text,
                translated_text=translated_text,
                reference_text=reference_text,
                source_language=source_language,
                target_language=target_language
            )
        
        return {"extracted_terms": extracted_terms or {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取术语时出错: {str(e)}") 