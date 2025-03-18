import logging
import httpx
import json
import traceback
from typing import Dict, Any, Optional, List

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """大语言模型服务，负责调用语言模型API进行翻译"""
    
    @staticmethod
    async def translate_text(
        text: str, 
        source_lang: str, 
        target_lang: str, 
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用大语言模型翻译文本
        
        Args:
            text: 要翻译的文本
            source_lang: 源语言代码
            target_lang: 目标语言代码
            model: 可选的模型名称，如果提供则使用该模型而不是默认模型
            
        Returns:
            包含翻译结果的字典
        """
        if settings.CUSTOM_API_ENABLED:
            return await LLMService._translate_with_custom_api(text, source_lang, target_lang, model)
        else:
            return await LLMService._translate_with_default_api(text, source_lang, target_lang, model)
    
    @staticmethod
    async def _translate_with_default_api(
        text: str, 
        source_lang: str, 
        target_lang: str, 
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用默认API进行翻译"""
        # 使用实际的API调用
        model_name = model or settings.LLM_MODEL_NAME
        
        logger.info(f"使用默认API进行翻译，模型: {model_name}")
        
        try:
            # 构建系统指令和用户指令
            system_instruction = f"你是一个专业的翻译系统，专门从{source_lang}语言翻译到{target_lang}语言。请只返回翻译后的文本，不要添加任何解释或备注。"
            user_instruction = f"请将以下文本从{source_lang}翻译成{target_lang}：\n\n{text}"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # 尝试使用 chat/completions 端点（优先）
                try:
                    response = await client.post(
                        f"{settings.LLM_API_BASE_URL}/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                        json={
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": user_instruction}
                            ],
                            "temperature": 0.3
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        translated_text = result["choices"][0]["message"]["content"].strip()
                    else:
                        # 如果 chat/completions 失败，尝试 completions 端点
                        logger.warning(f"Chat API调用失败，尝试使用Completions API: {response.status_code}")
                        response = await client.post(
                            f"{settings.LLM_API_BASE_URL}/v1/completions",
                            headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                            json={
                                "model": model_name,
                                "prompt": f"将以下{source_lang}文本翻译成{target_lang}:\n\n{text}",
                                "max_tokens": 2000,
                                "temperature": 0.3
                            }
                        )
                        
                        if response.status_code != 200:
                            logger.error(f"API调用失败: {response.status_code} - {response.text}")
                            return await LLMService._simulate_translation(text, source_lang, target_lang, model_name)
                        
                        result = response.json()
                        translated_text = result["choices"][0]["text"].strip()
                except Exception as api_error:
                    # 如果 chat/completions 端点不可用，回退到 completions 端点
                    logger.warning(f"Chat API异常，尝试使用Completions API: {str(api_error)}")
                    response = await client.post(
                        f"{settings.LLM_API_BASE_URL}/v1/completions",
                        headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                        json={
                            "model": model_name,
                            "prompt": f"将以下{source_lang}文本翻译成{target_lang}:\n\n{text}",
                            "max_tokens": 2000,
                            "temperature": 0.3
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"API调用失败: {response.status_code} - {response.text}")
                        return await LLMService._simulate_translation(text, source_lang, target_lang, model_name)
                    
                    result = response.json()
                    translated_text = result["choices"][0]["text"].strip()
                
                return {
                    "source_text": text,
                    "translated_text": translated_text,
                    "model_used": model_name
                }
        except Exception as e:
            logger.error(f"默认API调用异常: {str(e)}")
            # 异常时使用模拟翻译作为后备方案
            return await LLMService._simulate_translation(text, source_lang, target_lang, model_name)
    
    @staticmethod
    async def _simulate_translation(
        text: str, 
        source_lang: str, 
        target_lang: str, 
        model_name: str
    ) -> Dict[str, Any]:
        """模拟翻译结果（仅作为后备方案）"""
        logger.warning("使用模拟翻译作为后备方案")
        
        if source_lang == 'zh' and target_lang == 'en':
            translated_text = f"[Translated to English]: {text}"
        elif source_lang == 'en' and target_lang == 'zh':
            translated_text = f"[翻译成中文]: {text}"
        else:
            translated_text = f"[Translated from {source_lang} to {target_lang}]: {text}"
        
        return {
            "source_text": text,
            "translated_text": translated_text,
            "model_used": model_name
        }
    
    @staticmethod
    async def _translate_with_custom_api(
        text: str, 
        source_lang: str, 
        target_lang: str, 
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用自定义API（与OpenAI兼容）进行翻译"""
        model_name = model or "gpt-3.5-turbo"
        base_url = settings.CUSTOM_API_BASE_URL.rstrip('/')
        api_version = settings.CUSTOM_API_VERSION.lstrip('/')
        
        # 构建系统指令和用户指令
        system_instruction = f"你是一个专业的翻译系统，专门从{source_lang}语言翻译到{target_lang}语言。请只返回翻译后的文本，不要添加任何解释或备注。"
        user_instruction = f"请将以下文本从{source_lang}翻译成{target_lang}：\n\n{text}"
        
        logger.info(f"使用自定义API进行翻译，模型: {model_name}, API基础URL: {base_url}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # 尝试使用 chat/completions 端点（优先）
                try:
                    response = await client.post(
                        f"{base_url}/{api_version}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.CUSTOM_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": user_instruction}
                            ],
                            "temperature": 0.3
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        translated_text = result["choices"][0]["message"]["content"].strip()
                    else:
                        # 如果 chat/completions 失败，尝试 completions 端点
                        logger.warning(f"自定义Chat API调用失败，尝试使用Completions API: {response.status_code}")
                        response = await client.post(
                            f"{base_url}/{api_version}/completions",
                            headers={
                                "Authorization": f"Bearer {settings.CUSTOM_API_KEY}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": model_name,
                                "prompt": f"将以下{source_lang}文本翻译成{target_lang}:\n\n{text}",
                                "max_tokens": 2000,
                                "temperature": 0.3
                            }
                        )
                        
                        if response.status_code != 200:
                            logger.error(f"自定义API调用失败: {response.status_code} - {response.text}")
                            # 失败时使用默认API作为后备方案
                            logger.info("尝试使用默认API作为后备")
                            return await LLMService._translate_with_default_api(text, source_lang, target_lang, model)
                        
                        result = response.json()
                        translated_text = result["choices"][0]["text"].strip()
                except Exception as api_error:
                    # 如果 chat/completions 端点不可用，回退到 completions 端点
                    logger.warning(f"自定义Chat API异常，尝试使用Completions API: {str(api_error)}")
                    response = await client.post(
                        f"{base_url}/{api_version}/completions",
                        headers={
                            "Authorization": f"Bearer {settings.CUSTOM_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_name,
                            "prompt": f"将以下{source_lang}文本翻译成{target_lang}:\n\n{text}",
                            "max_tokens": 2000,
                            "temperature": 0.3
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"自定义API调用失败: {response.status_code} - {response.text}")
                        # 失败时使用默认API作为后备方案
                        logger.info("尝试使用默认API作为后备")
                        return await LLMService._translate_with_default_api(text, source_lang, target_lang, model)
                    
                    result = response.json()
                    translated_text = result["choices"][0]["text"].strip()
                
                return {
                    "source_text": text,
                    "translated_text": translated_text,
                    "model_used": model_name
                }
        except Exception as e:
            logger.error(f"自定义API调用异常: {str(e)}")
            # 发生异常时使用默认API作为后备方案
            logger.info("尝试使用默认API作为后备")
            return await LLMService._translate_with_default_api(text, source_lang, target_lang, model)
    
    @staticmethod
    async def get_available_models() -> List[Dict[str, str]]:
        """
        获取可用的模型列表
        
        从API获取可用的语言模型列表，始终使用环境变量中的API配置
        
        Returns:
            可用模型的列表
        """
        logger.info(f"获取可用模型列表，API配置: 启用自定义API={settings.CUSTOM_API_ENABLED}")
        
        if settings.CUSTOM_API_ENABLED and settings.CUSTOM_API_KEY:
            # 使用自定义API获取模型列表
            try:
                models = await LLMService._fetch_custom_api_models()
                if models:
                    logger.info(f"成功从自定义API获取模型列表: {len(models)}")
                    return models
                else:
                    logger.warning("从自定义API获取模型列表失败")
                    # 返回空列表而不是默认列表
                    return []
            except Exception as e:
                logger.error(f"获取自定义API模型列表异常: {str(e)}")
                # 出现异常也返回空列表
                return []
        else:
            # API未启用，返回空列表
            logger.warning("自定义API未启用或API密钥未设置，无法获取模型列表")
            return []
    
    @staticmethod
    async def _fetch_custom_api_models() -> List[Dict[str, str]]:
        """从自定义API获取可用的模型列表"""
        base_url = settings.CUSTOM_API_BASE_URL.rstrip('/')
        api_version = settings.CUSTOM_API_VERSION.lstrip('/')
        api_url = f"{base_url}/{api_version}/models"
        
        logger.info(f"🌐 正在从 {api_url} 获取模型列表")
        
        try:
            headers = {"Authorization": f"Bearer {settings.CUSTOM_API_KEY}"}
            logger.info(f"请求头: {headers}")
            
            timeout = httpx.Timeout(30.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(api_url, headers=headers)
                
                # 记录原始响应
                logger.info(f"API响应状态码: {response.status_code}")
                logger.info(f"API响应头: {response.headers}")
                
                if response.status_code != 200:
                    logger.error(f"❌ 获取模型列表失败: {response.status_code} - {response.text}")
                    return []
                
                # 解析响应内容
                try:
                    result = response.json()
                    logger.info(f"API响应内容: {json.dumps(result, ensure_ascii=False)[:200]}...")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ 解析API响应JSON失败: {str(e)}")
                    logger.error(f"响应内容: {response.text[:200]}...")
                    return []
                
                models = []
                
                # 检查API响应格式
                if "data" not in result:
                    logger.warning("⚠️ API响应中未找到'data'字段")
                    if isinstance(result, list):
                        logger.info("API响应是列表格式，尝试直接处理")
                        model_list = result
                    else:
                        logger.error("API响应格式不符合预期")
                        return []
                else:
                    model_list = result.get("data", [])
                
                # 处理模型列表
                for model_data in model_list:
                    # 日志记录该模型的原始数据
                    logger.info(f"处理模型数据: {json.dumps(model_data, ensure_ascii=False)}")
                    
                    # 如果是字符串，则直接作为ID使用
                    if isinstance(model_data, str):
                        model_id = model_data
                    # 否则，尝试从对象中提取ID
                    else:
                        model_id = model_data.get("id", "")
                        if not model_id and "name" in model_data:
                            model_id = model_data.get("name", "")
                    
                    if not model_id:
                        logger.warning(f"⚠️ 无法从数据中提取模型ID: {model_data}")
                        continue
                    
                    # 筛选常见的LLM模型
                    if (model_id and (
                            "gpt" in model_id.lower() or 
                            "llama" in model_id.lower() or 
                            "claude" in model_id.lower() or 
                            "text-embedding" in model_id.lower() or
                            "gemini" in model_id.lower() or
                            "deepseek" in model_id.lower())):
                        models.append({
                            "id": model_id,
                            "name": model_id,
                            "type": "custom"
                        })
                
                logger.info(f"✅ 成功获取到 {len(models)} 个模型")
                return models
        except httpx.RequestError as e:
            logger.error(f"❌ HTTP请求异常: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"❌ 获取模型列表异常: {str(e)}")
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            return []
    
    @staticmethod
    async def get_ai_completion(prompt: str) -> str:
        """
        使用AI生成文本补全
        
        Args:
            prompt: 提示语
            
        Returns:
            AI生成的文本
        """
        logger.info("调用AI进行文本补全")
        
        try:
            if settings.CUSTOM_API_ENABLED and settings.CUSTOM_API_KEY:
                # 使用自定义API
                base_url = settings.CUSTOM_API_BASE_URL.rstrip('/')
                api_version = settings.CUSTOM_API_VERSION.lstrip('/')
                model_name = "gpt-3.5-turbo"  # 默认使用较快的模型
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{base_url}/{api_version}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.CUSTOM_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model_name,
                            "messages": [
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.3
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"API调用失败: {response.status_code} - {response.text}")
                        return "{}"  # 返回空JSON
                    
                    result = response.json()
                    completion = result["choices"][0]["message"]["content"].strip()
                    return completion
            else:
                # 简单模拟返回
                logger.warning("未启用自定义API，无法进行AI术语提取")
                return "{}"  # 返回空JSON
                
        except Exception as e:
            logger.error(f"AI补全异常: {str(e)}")
            return "{}"  # 返回空JSON
        
llm_service = LLMService() 