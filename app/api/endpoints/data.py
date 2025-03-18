from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File, Form
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json

from app.models.schemas import TerminologyEntry, TranslationExample
from app.services.data_service import data_service
from app.services.terminology_service import terminology_service

router = APIRouter()


class TerminologyEntry(BaseModel):
    source_term: str
    target_term: str
    definition: Optional[str] = None


class TerminologyBatchSave(BaseModel):
    terminology_dict: Dict[str, str]
    domain: str = "materials_science"
    source_lang: str = "zh"
    target_lang: str = "en"


@router.get("/terminology", summary="获取术语库")
async def get_terminology(
    domain: str = Query("materials_science", description="领域名称"),
    source_lang: str = Query("zh", description="源语言代码"),
    target_lang: str = Query("en", description="目标语言代码"),
    simplified: bool = Query(False, description="是否返回简化格式 {源术语: 目标术语}")
):
    """
    获取指定领域和语言的术语库
    
    - **domain**: 领域名称，默认为materials_science
    - **source_lang**: 源语言代码，默认为zh
    - **target_lang**: 目标语言代码，默认为en
    - **simplified**: 是否返回简化格式，如果为true则返回{源术语: 目标术语}格式
    """
    try:
        if simplified:
            # 返回简化格式的术语库
            terminology = terminology_service.get_simplified_terminology(domain, source_lang, target_lang)
            return terminology
        else:
            # 返回完整格式的术语库
            terminology = terminology_service.get_all_terminology(domain, source_lang, target_lang)
            return terminology
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取术语库失败: {str(e)}")


@router.post("/terminology", summary="添加单个术语")
async def add_terminology(
    entry: TerminologyEntry,
    domain: str = Query("materials_science", description="领域名称"),
    source_lang: str = Query("zh", description="源语言代码"),
    target_lang: str = Query("en", description="目标语言代码")
):
    """
    添加新的术语或更新已有术语
    
    - **entry**: 术语条目，包含source_term和target_term
    - **domain**: 领域名称，默认为materials_science
    - **source_lang**: 源语言代码，默认为zh
    - **target_lang**: 目标语言代码，默认为en
    """
    success = terminology_service.add_terminology(
        entry.source_term,
        entry.target_term,
        domain,
        source_lang,
        target_lang,
        entry.definition or ""
    )
    
    if success:
        return {"status": "success", "message": "术语添加成功"}
    else:
        raise HTTPException(status_code=500, detail="添加术语失败")


@router.post("/terminology/batch", summary="批量保存术语")
async def batch_save_terminology(
    batch: TerminologyBatchSave
):
    """
    批量添加术语到术语库
    
    - **terminology_dict**: 术语字典，格式为{源术语: 目标术语}
    - **domain**: 领域名称，默认为materials_science
    - **source_lang**: 源语言代码，默认为zh
    - **target_lang**: 目标语言代码，默认为en
    """
    try:
        count = 0
        for source_term, target_term in batch.terminology_dict.items():
            success = terminology_service.add_terminology(
                source_term,
                target_term,
                batch.domain,
                batch.source_lang,
                batch.target_lang
            )
            if success:
                count += 1
        
        return {
            "status": "success", 
            "message": f"成功添加{count}个术语", 
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量添加术语时出错: {str(e)}")


@router.get("/examples", response_model=List[TranslationExample], summary="获取翻译示例")
async def get_translation_examples(
    domain: str = Query("materials_science", description="领域名称"),
    text_type: Optional[str] = Query(None, description="文本类型，如academic, technical等"),
    source_lang: str = Query("zh", description="源语言代码"),
    target_lang: str = Query("en", description="目标语言代码")
):
    """
    获取翻译示例
    
    - **domain**: 领域名称，默认为materials_science
    - **text_type**: 文本类型（可选），如academic, technical等
    - **source_lang**: 源语言代码，默认为zh
    - **target_lang**: 目标语言代码，默认为en
    
    返回翻译示例列表。
    """
    try:
        examples = data_service.load_translation_examples(domain, text_type, source_lang, target_lang)
        return examples
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取翻译示例出错: {str(e)}")


@router.post("/init-sample-data", summary="初始化示例数据")
async def init_sample_data():
    """初始化示例数据，包括术语库和翻译示例"""
    try:
        result = data_service.init_sample_data()
        return {"status": "success", "message": "示例数据初始化成功", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化示例数据时出错: {str(e)}")


@router.put("/terminology/{term_id}", summary="更新术语库中的术语")
async def update_terminology(term_id: int, term: TerminologyEntry):
    """
    更新术语库中的术语
    """
    try:
        # 获取现有术语以获取领域和语言信息
        # 这里需要先查询现有术语详情，但SQLite实现暂时不支持，后续改进
        # 临时使用默认值
        success = terminology_service.add_terminology(
            term.source_term,
            term.target_term,
            "materials_science",  # 默认领域
            "zh",                 # 默认源语言
            "en",                 # 默认目标语言
            term.definition
        )
        
        if success:
            return {"status": "success", "message": "术语更新成功"}
        else:
            raise HTTPException(status_code=404, detail=f"未找到术语ID: {term_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新术语时出错: {str(e)}")


@router.delete("/terminology/{term_id}", summary="删除术语库中的术语")
async def delete_terminology(term_id: int):
    """
    删除术语库中的术语
    """
    try:
        result = terminology_service.delete_terminology(term_id)
        if result:
            return {"status": "success", "message": "术语删除成功"}
        else:
            raise HTTPException(status_code=404, detail=f"未找到术语ID: {term_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除术语时出错: {str(e)}")


@router.get("/domains", summary="获取所有可用的领域列表")
async def get_domains():
    """
    获取所有可用的领域列表
    """
    try:
        domains = data_service.get_domains()
        return domains
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取领域列表时出错: {str(e)}")


@router.get("/reference-files", summary="获取所有可用的参考文本文件")
async def get_reference_files():
    """
    获取所有可用的参考文本文件
    """
    try:
        files = data_service.get_reference_files()
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取参考文本文件列表时出错: {str(e)}")


@router.get("/reference-file/{file_id}", summary="获取指定参考文本文件的内容")
async def get_reference_file(file_id: str):
    """
    获取指定参考文本文件的内容
    """
    try:
        file_content = data_service.get_reference_file(file_id)
        if file_content:
            return file_content
        else:
            raise HTTPException(status_code=404, detail=f"未找到参考文本文件: {file_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取参考文本文件内容时出错: {str(e)}")


@router.post("/reference-file", summary="上传新的参考文本文件")
async def upload_reference_file(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...)
):
    """
    上传新的参考文本文件
    """
    try:
        content = await file.read()
        file_content = content.decode("utf-8")
        
        result = data_service.add_reference_file(
            file.filename,
            file_content,
            source_lang,
            target_lang
        )
        
        return {"status": "success", "message": "参考文本文件上传成功", "file_id": result}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="无法解码文件内容，请确保文件是UTF-8编码的文本文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传参考文本文件时出错: {str(e)}")


@router.delete("/reference-file/{file_id}", summary="删除参考文本文件")
async def delete_reference_file(file_id: str):
    """
    删除参考文本文件
    """
    try:
        result = data_service.delete_reference_file(file_id)
        if result:
            return {"status": "success", "message": "参考文本文件删除成功"}
        else:
            raise HTTPException(status_code=404, detail=f"未找到参考文本文件: {file_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除参考文本文件时出错: {str(e)}")


@router.post("/terminology/edit-file", summary="编辑术语库文件")
async def edit_terminology_file(
    source_term: str = Body(..., description="源语言术语"),
    target_term: str = Body(..., description="目标语言术语"),
    file_path: str = Body(..., description="术语库文件路径"),
    source_lang: str = Body("zh", description="源语言代码"),
    target_lang: str = Body("en", description="目标语言代码"),
    domain: str = Body("materials_science", description="领域名称")
):
    """
    编辑术语库文件，添加或更新术语
    
    - **source_term**: 源语言术语
    - **target_term**: 目标语言术语
    - **file_path**: 术语库文件路径，相对于术语库目录
    - **source_lang**: 源语言代码
    - **target_lang**: 目标语言代码
    - **domain**: 领域名称
    """
    try:
        success = data_service.edit_terminology_file(
            source_term=source_term,
            target_term=target_term,
            file_path=file_path,
            source_lang=source_lang,
            target_lang=target_lang,
            domain=domain
        )
        
        if success:
            return {"status": "success", "message": "术语库文件编辑成功"}
        else:
            raise HTTPException(status_code=500, detail="编辑术语库文件失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"编辑术语库文件出错: {str(e)}")


@router.post("/terminology/import", summary="导入术语库")
async def import_terminology(
    file: UploadFile = File(...),
    domain: str = Form("materials_science", description="领域名称"),
    source_lang: str = Form("zh", description="源语言代码"),
    target_lang: str = Form("en", description="目标语言代码")
):
    """
    从JSON文件导入术语库
    """
    try:
        content = await file.read()
        json_data = json.loads(content.decode("utf-8"))
        
        # 如果JSON是字典，尝试转换为列表
        if isinstance(json_data, dict):
            simplified_format = []
            for source_term, target_term in json_data.items():
                simplified_format.append({
                    "source_term": source_term,
                    "target_term": target_term,
                    "domain": domain,
                    "source_language": source_lang,
                    "target_language": target_lang
                })
            json_data = simplified_format
        
        # 导入术语库
        count = terminology_service.import_from_json(json_data)
        
        return {
            "status": "success", 
            "message": f"成功导入{count}个术语", 
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入术语库失败: {str(e)}")


@router.post("/terminology/add-term", summary="添加单个术语到术语库")
async def add_term_to_db(
    source_term: str = Body(..., description="源语言术语"),
    target_term: str = Body(..., description="目标语言术语"),
    domain: str = Body("materials_science", description="领域名称"),
    source_lang: str = Body("zh", description="源语言代码"),
    target_lang: str = Body("en", description="目标语言代码"),
    definition: Optional[str] = Body(None, description="术语定义")
):
    """
    添加单个术语到术语库
    
    - **source_term**: 源语言术语
    - **target_term**: 目标语言术语
    - **domain**: 领域名称
    - **source_lang**: 源语言代码
    - **target_lang**: 目标语言代码
    - **definition**: 术语定义(可选)
    """
    try:
        success = terminology_service.add_terminology(
            source_term, target_term, domain, source_lang, target_lang, definition
        )
        
        if success:
            return {"status": "success", "message": "术语添加成功"}
        else:
            raise HTTPException(status_code=500, detail="添加术语失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加术语失败: {str(e)}") 