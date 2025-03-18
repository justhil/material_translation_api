from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Any


class TranslationRequest(BaseModel):
    """翻译请求模型"""
    source_text: str = Field(..., description="源文本")
    source_language: str = Field("zh", description="源语言代码")
    target_language: str = Field("en", description="目标语言代码")
    domain: str = Field("materials_science", description="领域")
    model: Optional[str] = Field(None, description="翻译模型")
    reference_texts: List[str] = Field([], description="参考译文列表")


class TranslationResponse(BaseModel):
    """翻译响应模型"""
    source_text: str = Field(..., description="源文本")
    translated_text: str = Field(..., description="翻译后的文本")
    source_language: str = Field(..., description="源语言代码")
    target_language: str = Field(..., description="目标语言代码")
    domain: str = Field(..., description="领域")
    model: Optional[str] = Field(None, description="使用的翻译模型")


class EvaluationRequest(BaseModel):
    """评估请求模型"""
    source_text: str = Field(..., description="源文本内容")
    translated_text: str = Field(..., description="待评估的翻译文本")
    reference_texts: List[str] = Field(..., description="参考译文列表，至少提供一个")
    source_language: str = Field(..., description="源语言代码")
    target_language: str = Field(..., description="目标语言代码")
    domain: str = Field(default="materials_science", description="领域类型，默认为材料科学")


class EvaluationScore(BaseModel):
    """评分模型"""
    score: float = Field(..., description="得分值 (0-1)")
    max_score: float = Field(1.0, description="最高分值")
    description: str = Field(..., description="得分说明")


class EvaluationResponse(BaseModel):
    """评估响应模型"""
    overall_score: EvaluationScore = Field(..., description="综合得分")
    bleu_score: EvaluationScore = Field(..., description="BLEU分数")
    terminology_score: EvaluationScore = Field(..., description="术语准确性得分")
    sentence_structure_score: EvaluationScore = Field(..., description="句式转换得分")
    discourse_score: EvaluationScore = Field(..., description="语篇连贯性得分")
    detailed_feedback: Dict[str, str] = Field(..., description="详细反馈")
    suggestions: List[str] = Field(..., description="改进建议")
    extracted_terms: Optional[Dict[str, str]] = Field(None, description="从文本中提取的术语对照表")


class ScoringCriteria(BaseModel):
    """评分标准模型"""
    name: str = Field(..., description="标准名称")
    description: str = Field(..., description="标准描述")
    calculation: str = Field(..., description="计算方法")
    weight: str = Field(..., description="权重")
    interpretation: Dict[str, str] = Field(..., description="分数解释")


class TerminologyEntry(BaseModel):
    """术语模型"""
    source_term: str = Field(..., description="源语言术语")
    target_term: str = Field(..., description="目标语言术语")
    definition: Optional[str] = Field(None, description="术语定义")
    source_language: str = Field(..., description="源语言代码")
    target_language: str = Field(..., description="目标语言代码")
    domain: str = Field(..., description="所属领域")


class TranslationExample(BaseModel):
    """翻译示例模型"""
    example_id: str = Field(..., description="示例ID")
    source_text: str = Field(..., description="源文本")
    target_text: str = Field(..., description="目标文本/译文")
    domain: str = Field(..., description="所属领域")
    text_type: str = Field(..., description="文本类型，如'academic'、'technical'等")
    notes: Optional[str] = Field(None, description="注释说明")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="API版本")


class ReferenceFile(BaseModel):
    """参考文本文件模型"""
    id: str = Field(..., description="文件ID")
    name: str = Field(..., description="文件名")
    source_language: str = Field(..., description="源语言代码")
    target_language: str = Field(..., description="目标语言代码")
    language_pair: str = Field(..., description="语言对")
    created_at: str = Field(..., description="创建时间")


class ReferenceContent(BaseModel):
    """参考文本内容模型"""
    id: str = Field(..., description="文件ID")
    name: str = Field(..., description="文件名")
    content: str = Field(..., description="文件内容")
    source_language: str = Field(..., description="源语言代码")
    target_language: str = Field(..., description="目标语言代码")


class ApiConfig(BaseModel):
    """API配置模型"""
    enabled: bool = Field(..., description="是否启用自定义API")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    api_version: Optional[str] = Field(None, description="API版本")


class Model(BaseModel):
    """模型信息"""
    id: str = Field(..., description="模型ID")
    name: Optional[str] = Field(None, description="模型名称")
    description: Optional[str] = Field(None, description="模型描述")


class SystemHealth(BaseModel):
    """系统健康状态"""
    status: str = Field(..., description="状态")
    version: str = Field(..., description="版本")
    uptime: float = Field(..., description="运行时间(秒)") 