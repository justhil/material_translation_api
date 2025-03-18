import os
import json
import logging
from typing import Dict, List, Optional

from app.core.config import settings
from app.models.schemas import TerminologyEntry, TranslationExample


logger = logging.getLogger(__name__)


class DataService:
    """数据服务，负责从本地文件加载和管理术语库和翻译示例"""
    
    def __init__(self):
        self.terminology_cache = {}  # 缓存已加载的术语
        self.examples_cache = {}  # 缓存已加载的翻译示例
    
    def load_terminology(self, domain: str = "materials_science", 
                        source_lang: str = "zh", target_lang: str = "en") -> List[TerminologyEntry]:
        """
        从本地文件加载特定领域和语言的术语库
        
        Args:
            domain: 领域名称
            source_lang: 源语言代码
            target_lang: 目标语言代码
            
        Returns:
            术语条目列表
        """
        cache_key = f"{domain}_{source_lang}_{target_lang}"
        
        # 如果已缓存，直接返回
        if cache_key in self.terminology_cache:
            return self.terminology_cache[cache_key]
        
        # 构建文件路径，格式为 {domain}_{source_lang}_{target_lang}.json
        file_name = f"{domain}_{source_lang}_{target_lang}.json"
        file_path = os.path.join(settings.TERMINOLOGY_DIR, file_name)
        
        terminology_entries = []
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for item in data:
                    try:
                        entry = TerminologyEntry(**item)
                        terminology_entries.append(entry)
                    except Exception as e:
                        logger.warning(f"跳过无效的术语条目: {str(e)}")
            else:
                logger.warning(f"术语库文件不存在: {file_path}")
        except Exception as e:
            logger.error(f"加载术语库时出错: {str(e)}")
        
        # 缓存结果
        self.terminology_cache[cache_key] = terminology_entries
        return terminology_entries
    
    def load_translation_examples(self, domain: str = "materials_science",
                                 text_type: Optional[str] = None,
                                 source_lang: str = "zh",
                                 target_lang: str = "en") -> List[TranslationExample]:
        """
        从本地文件加载翻译示例
        
        Args:
            domain: 领域名称
            text_type: 文本类型（可选），如academic, technical等
            source_lang: 源语言代码
            target_lang: 目标语言代码
            
        Returns:
            翻译示例列表
        """
        cache_key = f"{domain}_{text_type or 'all'}_{source_lang}_{target_lang}"
        
        # 如果已缓存，直接返回
        if cache_key in self.examples_cache:
            return self.examples_cache[cache_key]
        
        # 构建文件路径
        # 如果指定了text_type，则文件格式为 {domain}_{text_type}_{source_lang}_{target_lang}.json
        # 否则为 {domain}_{source_lang}_{target_lang}.json
        if text_type:
            file_name = f"{domain}_{text_type}_{source_lang}_{target_lang}.json"
        else:
            file_name = f"{domain}_{source_lang}_{target_lang}.json"
            
        file_path = os.path.join(settings.TRANSLATION_EXAMPLES_DIR, file_name)
        
        examples = []
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for item in data:
                    try:
                        example = TranslationExample(**item)
                        examples.append(example)
                    except Exception as e:
                        logger.warning(f"跳过无效的翻译示例: {str(e)}")
            else:
                logger.warning(f"翻译示例文件不存在: {file_path}")
        except Exception as e:
            logger.error(f"加载翻译示例时出错: {str(e)}")
        
        # 缓存结果
        self.examples_cache[cache_key] = examples
        return examples
    
    def get_terminology_match(self, text: str, domain: str = "materials_science",
                             source_lang: str = "zh", target_lang: str = "en") -> Dict[str, str]:
        """
        在文本中查找匹配的术语，并返回对应的译文
        
        Args:
            text: 要搜索的文本
            domain: 领域名称
            source_lang: 源语言代码
            target_lang: 目标语言代码
            
        Returns:
            匹配到的术语及其译文的字典
        """
        terminology_entries = self.load_terminology(domain, source_lang, target_lang)
        
        matches = {}
        for entry in terminology_entries:
            if entry.source_term in text:
                matches[entry.source_term] = entry.target_term
                
        return matches
    
    def get_simplified_terminology(self, domain: str = "materials_science",
                                   source_lang: str = "zh", target_lang: str = "en") -> Dict[str, str]:
        """
        获取简化的术语对照表，格式为{source_term: target_term}
        
        Args:
            domain: 领域名称
            source_lang: 源语言代码
            target_lang: 目标语言代码
            
        Returns:
            术语及其译文的字典
        """
        terminology_entries = self.load_terminology(domain, source_lang, target_lang)
        
        simplified_terms = {}
        for entry in terminology_entries:
            simplified_terms[entry.source_term] = entry.target_term
                
        return simplified_terms
    
    def add_terminology_entry(self, source_term: str, target_term: str, 
                             domain: str = "materials_science",
                             source_lang: str = "zh", target_lang: str = "en", 
                             definition: str = "") -> bool:
        """
        添加新的术语
        
        Args:
            source_term: 源语言术语
            target_term: 目标语言术语
            domain: 领域名称
            source_lang: 源语言代码
            target_lang: 目标语言代码
            definition: 术语定义(可选)
            
        Returns:
            添加是否成功
        """
        try:
            # 构建文件路径
            file_name = f"{domain}_{source_lang}_{target_lang}.json"
            file_path = os.path.join(settings.TERMINOLOGY_DIR, file_name)
            
            # 载入现有术语库
            terminology_entries = []
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                terminology_entries = data
            
            # 生成新ID
            term_id = str(len(terminology_entries) + 1)
            
            # 检查是否已存在相同的术语
            for entry in terminology_entries:
                if entry.get("source_term") == source_term:
                    # 更新已有术语
                    entry["target_term"] = target_term
                    if definition:
                        entry["definition"] = definition
                    break
            else:
                # 添加新术语
                new_entry = {
                    "term_id": term_id,
                    "source_term": source_term,
                    "target_term": target_term,
                    "domain": domain,
                    "definition": definition or f"{source_term}的译文是{target_term}",
                    "context_examples": []
                }
                terminology_entries.append(new_entry)
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(terminology_entries, f, ensure_ascii=False, indent=2)
            
            # 清除缓存
            cache_key = f"{domain}_{source_lang}_{target_lang}"
            if cache_key in self.terminology_cache:
                del self.terminology_cache[cache_key]
                
            return True
        except Exception as e:
            logger.error(f"添加术语失败: {str(e)}")
            return False
            
    def save_terminology_batch(self, terminology_dict: Dict[str, str], 
                              domain: str = "materials_science",
                              source_lang: str = "zh", target_lang: str = "en") -> bool:
        """
        批量保存术语
        
        Args:
            terminology_dict: 术语字典，格式为{source_term: target_term}
            domain: 领域名称
            source_lang: 源语言代码
            target_lang: 目标语言代码
            
        Returns:
            保存是否成功
        """
        try:
            # 构建文件路径
            file_name = f"{domain}_{source_lang}_{target_lang}.json"
            file_path = os.path.join(settings.TERMINOLOGY_DIR, file_name)
            
            # 载入现有术语库
            terminology_entries = []
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                terminology_entries = data
            
            # 术语ID计数
            next_id = len(terminology_entries) + 1
            
            # 现有术语索引
            existing_terms = {entry.get("source_term"): entry for entry in terminology_entries}
            
            # 更新或添加术语
            for source_term, target_term in terminology_dict.items():
                if source_term in existing_terms:
                    # 更新已有术语
                    existing_terms[source_term]["target_term"] = target_term
                else:
                    # 添加新术语
                    new_entry = {
                        "term_id": str(next_id),
                        "source_term": source_term,
                        "target_term": target_term,
                        "domain": domain,
                        "definition": f"{source_term}的译文是{target_term}",
                        "context_examples": []
                    }
                    terminology_entries.append(new_entry)
                    next_id += 1
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(terminology_entries, f, ensure_ascii=False, indent=2)
            
            # 清除缓存
            cache_key = f"{domain}_{source_lang}_{target_lang}"
            if cache_key in self.terminology_cache:
                del self.terminology_cache[cache_key]
                
            return True
        except Exception as e:
            logger.error(f"批量保存术语失败: {str(e)}")
            return False
    
    def create_example_data(self):
        """创建示例数据，用于测试"""
        # 创建示例术语库
        terminology_data = [
            {
                "term_id": "1",
                "source_term": "材料科学",
                "target_term": "materials science",
                "domain": "materials_science",
                "definition": "研究材料结构、性质、加工和性能的科学",
                "context_examples": [
                    {
                        "source": "材料科学是一门多学科交叉的领域。",
                        "target": "Materials science is an interdisciplinary field."
                    }
                ]
            },
            {
                "term_id": "2",
                "source_term": "纳米材料",
                "target_term": "nanomaterials",
                "domain": "materials_science",
                "definition": "至少一个维度在1-100纳米范围内的材料",
                "context_examples": [
                    {
                        "source": "纳米材料具有独特的物理和化学性质。",
                        "target": "Nanomaterials possess unique physical and chemical properties."
                    }
                ]
            }
        ]
        
        # 创建示例翻译范本
        examples_data = [
            {
                "example_id": "1",
                "source_text": "本研究探讨了碳纳米管的机械性能。",
                "target_text": "The mechanical properties of carbon nanotubes were investigated in this study.",
                "domain": "materials_science",
                "text_type": "academic",
                "notes": "注意英文中使用了被动语态"
            },
            {
                "example_id": "2",
                "source_text": "我们合成了一种新型高强度复合材料。",
                "target_text": "A novel high-strength composite material was synthesized by us.",
                "domain": "materials_science",
                "text_type": "academic",
                "notes": "主动句转被动句示例"
            }
        ]
        
        # 保存示例术语库
        terminology_file = os.path.join(settings.TERMINOLOGY_DIR, "materials_science_zh_en.json")
        os.makedirs(os.path.dirname(terminology_file), exist_ok=True)
        with open(terminology_file, 'w', encoding='utf-8') as f:
            json.dump(terminology_data, f, ensure_ascii=False, indent=2)
            
        # 保存示例翻译范本
        examples_file = os.path.join(settings.TRANSLATION_EXAMPLES_DIR, "materials_science_academic_zh_en.json")
        os.makedirs(os.path.dirname(examples_file), exist_ok=True)
        with open(examples_file, 'w', encoding='utf-8') as f:
            json.dump(examples_data, f, ensure_ascii=False, indent=2)
            
        logger.info("示例数据创建完成")
    
    
    def init_sample_data(self):
        """初始化示例数据，包括术语库和参考文本"""
        try:
            # 创建示例术语库
            terminology_data = [
                {
                    "term_id": "1",
                    "source_term": "材料科学",
                    "target_term": "materials science",
                    "domain": "materials_science",
                    "definition": "研究材料结构、性质、加工和性能的科学",
                    "source_language": "zh",
                    "target_language": "en"
                },
                {
                    "term_id": "2",
                    "source_term": "纳米材料",
                    "target_term": "nanomaterials",
                    "domain": "materials_science",
                    "definition": "至少一个维度在1-100纳米范围内的材料",
                    "source_language": "zh",
                    "target_language": "en"
                },
                {
                    "term_id": "3",
                    "source_term": "复合材料",
                    "target_term": "composite materials",
                    "domain": "materials_science",
                    "definition": "由两种或两种以上不同性质的材料组成的材料",
                    "source_language": "zh",
                    "target_language": "en"
                },
                {
                    "term_id": "4",
                    "source_term": "晶格常数",
                    "target_term": "lattice constant",
                    "domain": "materials_science",
                    "definition": "晶体结构中单位晶胞的边长",
                    "source_language": "zh",
                    "target_language": "en"
                },
                {
                    "term_id": "5",
                    "source_term": "热导率",
                    "target_term": "thermal conductivity",
                    "domain": "materials_science",
                    "definition": "材料传导热量的能力",
                    "source_language": "zh",
                    "target_language": "en"
                }
            ]
            
            # 创建示例参考文本
            reference_texts = [
                {
                    "id": "ref_01",
                    "name": "材料科学简介.txt",
                    "content": "材料科学是研究材料的结构、性质、加工和性能的科学。在工程应用中，纳米材料和复合材料越来越受到关注。这些材料具有独特的物理和化学性质。研究人员常常测量晶格常数和热导率来表征这些材料。",
                    "source_language": "zh",
                    "target_language": "en"
                },
                {
                    "id": "ref_02",
                    "name": "Introduction to Materials Science.txt",
                    "content": "Materials science is the study of the structure, properties, processing, and performance of materials. In engineering applications, nanomaterials and composite materials are receiving increasing attention. These materials have unique physical and chemical properties. Researchers often measure lattice constants and thermal conductivity to characterize these materials.",
                    "source_language": "en",
                    "target_language": "zh"
                }
            ]
            
            # 保存示例术语库
            terminology_file = os.path.join(settings.TERMINOLOGY_DIR, "materials_science_zh_en.json")
            os.makedirs(os.path.dirname(terminology_file), exist_ok=True)
            with open(terminology_file, 'w', encoding='utf-8') as f:
                json.dump(terminology_data, f, ensure_ascii=False, indent=2)
            
            # 保存示例参考文本
            for ref in reference_texts:
                file_path = os.path.join(settings.REFERENCE_TEXTS_DIR, f"{ref['id']}_{ref['source_language']}_{ref['target_language']}.json")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(ref, f, ensure_ascii=False, indent=2)
            
            # 清除缓存
            self.terminology_cache = {}
            self.examples_cache = {}
            
            logger.info("示例数据初始化完成")
            
            return {
                "terminology_count": len(terminology_data),
                "reference_count": len(reference_texts)
            }
        except Exception as e:
            logger.error(f"初始化示例数据失败: {str(e)}")
            raise

    def edit_terminology_file(self, source_term: str, target_term: str, 
                              file_path: str, source_lang: str = "zh", 
                              target_lang: str = "en", domain: str = "materials_science") -> bool:
        """
        编辑术语库文件，添加或更新术语
        
        Args:
            source_term: 源语言术语
            target_term: 目标语言术语
            file_path: 术语库文件路径，相对于术语库目录
            source_lang: 源语言代码
            target_lang: 目标语言代码
            domain: 领域名称
            
        Returns:
            编辑是否成功
        """
        try:
            # 构建完整文件路径
            full_file_path = os.path.join(settings.TERMINOLOGY_DIR, file_path)
            
            # 检查文件是否存在
            file_exists = os.path.exists(full_file_path)
            
            # 初始化术语列表
            terminology_entries = []
            
            # 如果文件存在且不为空，加载现有内容
            if file_exists:
                try:
                    with open(full_file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                        if file_content:  # 文件不为空
                            terminology_entries = json.loads(file_content)
                except json.JSONDecodeError:
                    # 文件可能为空或格式不正确，使用空列表
                    logger.warning(f"术语库文件 {file_path} 格式不正确或为空，将创建新的术语库")
                    terminology_entries = []
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
            
            # 检查是否已存在相同的术语
            term_exists = False
            for entry in terminology_entries:
                if entry.get("source_term") == source_term and entry.get("source_language") == source_lang and entry.get("target_language") == target_lang:
                    # 更新已有术语
                    entry["target_term"] = target_term
                    term_exists = True
                    break
            
            # 如果不存在，添加新术语
            if not term_exists:
                # 生成新的术语ID
                term_id = str(len(terminology_entries) + 1)
                
                # 创建新的术语条目
                new_entry = {
                    "term_id": term_id,
                    "source_term": source_term,
                    "target_term": target_term,
                    "domain": domain,
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "definition": f"{source_term}的译文是{target_term}"
                }
                terminology_entries.append(new_entry)
            
            # 保存到文件
            with open(full_file_path, 'w', encoding='utf-8') as f:
                json.dump(terminology_entries, f, ensure_ascii=False, indent=2)
            
            # 清除缓存
            cache_key = f"{domain}_{source_lang}_{target_lang}"
            if cache_key in self.terminology_cache:
                del self.terminology_cache[cache_key]
            
            return True
        except Exception as e:
            logger.error(f"编辑术语库文件失败: {str(e)}")
            return False


# 单例实例
data_service = DataService() 