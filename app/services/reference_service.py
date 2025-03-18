import os
import json
from typing import List, Dict, Optional
from app.core.config import settings

class ReferenceService:
    """参考文本服务，负责管理本地参考文本文件"""
    
    @staticmethod
    def get_reference_files() -> List[Dict[str, str]]:
        """获取参考文本文件列表"""
        reference_files = []
        
        # 扫描参考文本目录
        for filename in os.listdir(settings.REFERENCE_TEXTS_DIR):
            if filename.endswith('.txt'):
                file_path = os.path.join(settings.REFERENCE_TEXTS_DIR, filename)
                
                # 尝试从文件名获取语言信息（假设格式为：name_zh-en.txt 或 name_en-zh.txt）
                lang_pair = "未知"
                if '_' in filename:
                    parts = filename.split('_')
                    if len(parts) > 1:
                        lang_code = parts[-1].split('.')[0]
                        if '-' in lang_code:
                            lang_pair = lang_code
                
                reference_files.append({
                    "id": filename,
                    "name": os.path.splitext(filename)[0],
                    "path": file_path,
                    "language_pair": lang_pair
                })
        
        return reference_files
    
    @staticmethod
    def get_reference_content(file_id: str) -> Optional[Dict[str, str]]:
        """获取指定参考文本文件的内容"""
        file_path = os.path.join(settings.REFERENCE_TEXTS_DIR, file_id)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 尝试确定源语言和目标语言
            source_lang = "未知"
            target_lang = "未知"
            
            if '_' in file_id:
                parts = file_id.split('_')
                if len(parts) > 1:
                    lang_code = parts[-1].split('.')[0]
                    if '-' in lang_code:
                        source_lang, target_lang = lang_code.split('-')
            
            return {
                "id": file_id,
                "name": os.path.splitext(file_id)[0],
                "content": content,
                "source_language": source_lang,
                "target_language": target_lang
            }
        except Exception as e:
            print(f"读取参考文本文件错误: {str(e)}")
            return None
    
    @staticmethod
    def save_reference_file(filename: str, content: str) -> bool:
        """保存新的参考文本文件"""
        try:
            file_path = os.path.join(settings.REFERENCE_TEXTS_DIR, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"保存参考文本文件错误: {str(e)}")
            return False
    
    @staticmethod
    def delete_reference_file(file_id: str) -> bool:
        """删除参考文本文件"""
        try:
            file_path = os.path.join(settings.REFERENCE_TEXTS_DIR, file_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"删除参考文本文件错误: {str(e)}")
            return False

reference_service = ReferenceService() 