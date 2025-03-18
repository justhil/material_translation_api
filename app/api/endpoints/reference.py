from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import os
import shutil

from app.services.reference_service import reference_service

router = APIRouter()

@router.get("/files", response_model=List[Dict[str, str]])
async def get_reference_files():
    """获取所有参考文本文件列表"""
    return reference_service.get_reference_files()

@router.get("/file/{file_id}")
async def get_reference_file(file_id: str):
    """获取指定参考文本文件的内容"""
    file_data = reference_service.get_reference_content(file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail=f"参考文本文件 {file_id} 不存在")
    return file_data

@router.post("/file")
async def upload_reference_file(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...)
):
    """上传参考文本文件"""
    try:
        # 确保文件名是安全的
        filename = file.filename
        # 添加语言信息到文件名
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{source_lang}-{target_lang}{ext}"
        
        # 读取文件内容
        contents = await file.read()
        
        # 保存文件
        success = reference_service.save_reference_file(filename, contents.decode('utf-8'))
        
        if success:
            return {"status": "success", "filename": filename}
        else:
            raise HTTPException(status_code=500, detail="保存文件时出错")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传文件失败: {str(e)}")

@router.delete("/file/{file_id}")
async def delete_reference_file(file_id: str):
    """删除参考文本文件"""
    success = reference_service.delete_reference_file(file_id)
    if success:
        return {"status": "success", "message": f"文件 {file_id} 已删除"}
    else:
        raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在或删除失败") 