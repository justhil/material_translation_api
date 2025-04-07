import logging
import re
import nltk
import jieba
from typing import Dict, List, Tuple, Any, Set
from sacrebleu.metrics import BLEU
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import stanza
from nltk.tree import Tree
import torch
from transformers import BertModel, BertTokenizer
from scipy.spatial.distance import cosine
import networkx as nx
from zss import simple_distance, Node
from datetime import datetime

from app.core.config import settings
from app.models.schemas import EvaluationScore, EvaluationResponse
from app.services.data_service import data_service
from app.services.llm_service import llm_service

# 确保下载需要的nltk数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


logger = logging.getLogger(__name__)


class EvaluationService:
    """评估服务，负责评估翻译质量"""
    
    def __init__(self):
        self.bleu = BLEU(smooth_method='exp')  # 使用指数平滑
        
    def evaluate_translation(self,
                           source_text: str,
                           translated_text: str,
                           reference_texts: List[str],
                           source_language: str = "zh",
                           target_language: str = "en",
                           domain: str = "materials_science") -> EvaluationResponse:
        """
        评估翻译质量
        
        Args:
            source_text: 源文本
            translated_text: 待评估的翻译文本
            reference_texts: 参考译文列表
            source_language: 源语言代码
            target_language: 目标语言代码
            domain: 领域名称
            
        Returns:
            评估结果对象
        """
        # 1. 计算BLEU分数
        bleu_score, bleu_details = self._calculate_bleu_score(translated_text, reference_texts, source_language, target_language)
        
        # 2. 根据配置选择术语评估方式
        terminology_mode = settings.TERMINOLOGY_EVALUATION_MODE
        if terminology_mode == "reference" and reference_texts:
            # 使用参考文本中的术语
            terminology_score, terminology_feedback, extracted_terms = self._evaluate_terminology_from_reference(
                source_text, translated_text, reference_texts[0] if reference_texts else "", 
                source_language, target_language
            )
        elif terminology_mode == "ai_extraction":
            # 使用AI提取的术语
            terminology_score, terminology_feedback, extracted_terms = self._evaluate_terminology_with_ai(
                source_text, translated_text, domain, source_language, target_language
            )
        else:
            # 默认使用术语库
            terminology_score, terminology_feedback = self._evaluate_terminology(
                source_text, translated_text, domain, source_language, target_language
            )
            extracted_terms = None
        
        # 3. 评估句式转换情况
        sentence_score, sentence_feedback = self._evaluate_sentence_structure(
            source_text, translated_text, source_language, target_language
        )
        
        # 4. 评估语篇连贯性
        discourse_score, discourse_feedback = self._evaluate_discourse(
            translated_text, reference_texts
        )
        
        # 5. 计算综合得分
        weights = settings.EVALUATION_WEIGHTS
        overall_score = (
            weights["bleu"] * bleu_score +
            weights["terminology"] * terminology_score +
            weights["sentence_structure"] * sentence_score +
            weights["discourse"] * discourse_score
        )
        
        # 准备各项评分的描述
        bleu_description = f"BLEU分数为{bleu_score:.2f}，这表示译文与参考译文的匹配程度。{bleu_details}"
        terminology_description = f"术语准确性得分为{terminology_score:.2f}，评估译文中专业术语的使用是否准确。"
        sentence_description = f"句式转换得分为{sentence_score:.2f}，评估汉语主动句与英语被动句的转换是否适当。"
        discourse_description = f"语篇连贯性得分为{discourse_score:.2f}，评估译文的逻辑连贯性和整体流畅度。"
        
        # 生成改进建议
        suggestions = self._generate_suggestions(
            bleu_score, terminology_score, sentence_score, discourse_score,
            terminology_feedback, sentence_feedback, discourse_feedback
        )
        
        # 构建评估响应
        response = EvaluationResponse(
            overall_score=EvaluationScore(
                score=overall_score,
                max_score=1.0,
                description=f"综合得分为{overall_score:.2f}，这是基于BLEU分数、术语准确性、句式转换和语篇连贯性的加权平均值。"
            ),
            bleu_score=EvaluationScore(
                score=bleu_score,
                max_score=1.0,
                description=bleu_description
            ),
            terminology_score=EvaluationScore(
                score=terminology_score,
                max_score=1.0,
                description=terminology_description
            ),
            sentence_structure_score=EvaluationScore(
                score=sentence_score,
                max_score=1.0,
                description=sentence_description
            ),
            discourse_score=EvaluationScore(
                score=discourse_score,
                max_score=1.0,
                description=discourse_description
            ),
            detailed_feedback={
                "bleu": bleu_details,
                "terminology": terminology_feedback,
                "sentence_structure": sentence_feedback,
                "discourse": discourse_feedback
            },
            suggestions=suggestions
        )
        
        # 如果有提取的术语，添加到响应中
        if extracted_terms:
            response.extracted_terms = extracted_terms
            
        return response
    
    def _calculate_bleu_score(self, translated_text: str, reference_texts: List[str], 
                             source_language: str = "zh", target_language: str = "en") -> Tuple[float, str]:
        """
        计算改进的BLEU分数，结合了句子级BLEU和语料级BLEU
        
        Args:
            translated_text: 待评估的翻译文本
            reference_texts: 参考译文列表
            source_language: 源语言代码
            target_language: 目标语言代码
            
        Returns:
            BLEU分数及详细说明
        """
        try:
            # 检查是否有参考文本
            if not reference_texts or not all(reference_texts):
                logger.warning("无参考文本或参考文本为空，无法计算BLEU分数")
                return 0.5, "未提供有效的参考译文，无法准确计算BLEU分数。提供了默认分数0.5。"
                
            # 0. 根据语言选择分词器
            def tokenize_text(text, lang):
                if lang == "zh":
                    # 中文使用jieba分词
                    return list(jieba.cut(text))
                else:
                    # 其他语言使用nltk分词
                    return nltk.word_tokenize(text)
            
            # 1. 使用sacrebleu计算语料级BLEU分数
            corpus_bleu = self.bleu.corpus_score([translated_text], [[ref] for ref in reference_texts])
            corpus_score = corpus_bleu.score / 100.0  # 归一化到0-1范围
            
            # 2. 使用nltk的sentence_bleu计算句子级BLEU分数(考虑短句的情况)
            smoothing = SmoothingFunction()
            
            # 分句
            translated_sentences = nltk.sent_tokenize(translated_text)
            sentence_scores = []
            
            # 平滑函数选择
            smooth_methods = [
                smoothing.method1,  # 为零计数添加one
                smoothing.method2,  # 为零计数添加epsilon
                smoothing.method3,  # 为零计数添加平滑值
                smoothing.method4,  # NIST几何加权平均
            ]
            
            # 使用每种平滑方法并选择得分最合理的
            all_method_scores = []
            
            # 对每个参考翻译，计算句子级别的BLEU
            for ref_text in reference_texts:
                ref_sentences = nltk.sent_tokenize(ref_text)
                
                # 如果句子数量差异太大，尝试基于段落或全文进行对比
                if abs(len(translated_sentences) - len(ref_sentences)) > min(len(translated_sentences), len(ref_sentences)) * 0.5:
                    # 使用整个文本进行比较，而不是逐句比较
                    trans_tokens = tokenize_text(translated_text, target_language)
                    ref_tokens = tokenize_text(ref_text, target_language)
                    
                    # 对于每种平滑方法计算分数
                    for method in smooth_methods:
                        sent_score = sentence_bleu([ref_tokens], trans_tokens, smoothing_function=method)
                        all_method_scores.append(sent_score)
                else:
                    # 句子数量相近，进行逐句比较
                    for i, trans_sent in enumerate(translated_sentences):
                        # 找到最匹配的参考句子
                        best_score = 0
                        
                        for j, ref_sent in enumerate(ref_sentences):
                            # 对句子分词
                            trans_tokens = tokenize_text(trans_sent, target_language)
                            ref_tokens = tokenize_text(ref_sent, target_language)
                            
                            # 对于每种平滑方法计算分数
                            for method in smooth_methods:
                                sent_score = sentence_bleu([ref_tokens], trans_tokens, smoothing_function=method)
                                if sent_score > best_score:
                                    best_score = sent_score
                        
                        sentence_scores.append(best_score)
            
            # 选择得分
            if all_method_scores:
                # 排除极端值后取平均
                all_method_scores.sort()
                trimmed_scores = all_method_scores[1:-1] if len(all_method_scores) > 3 else all_method_scores
                avg_method_score = sum(trimmed_scores) / len(trimmed_scores)
                all_method_scores = [avg_method_score]
            
            # 计算句子级BLEU的平均值
            avg_sentence_score = sum(sentence_scores) / len(sentence_scores) if sentence_scores else (
                sum(all_method_scores) / len(all_method_scores) if all_method_scores else 0.0
            )
            
            # 3. 结合两种分数，给予较短文本更多的句子级BLEU权重
            # 计算文本长度因子
            text_length = len(translated_text.split())
            length_factor = min(1.0, text_length / 100.0)  # 长度因子，最大为1
            
            # 短文本给句子级BLEU更高权重，长文本给语料级BLEU更高权重
            corpus_weight = 0.3 + 0.4 * length_factor  # 0.3到0.7
            sentence_weight = 1.0 - corpus_weight      # 0.7到0.3
            
            final_score = corpus_weight * corpus_score + sentence_weight * avg_sentence_score
            
            # 4. 确保分数在0-1范围内
            final_score = max(0.0, min(1.0, final_score))
            
            # 有时文本非常短且与参考文本差异很大时，分数可能极低，设置一个最低阈值
            if text_length < 20 and final_score < 0.1:
                final_score = max(0.1, final_score)
            
            # 根据分数给出说明
            if final_score >= 0.8:
                detail = "译文与参考译文高度匹配，翻译质量优秀。"
            elif final_score >= 0.6:
                detail = "译文与参考译文匹配度良好，翻译质量不错。"
            elif final_score >= 0.4:
                detail = "译文与参考译文匹配度一般，有提升空间。"
            else:
                detail = "译文与参考译文差异较大，建议检查并修改。"
                
            # 添加技术细节
            detail += f" (语料级BLEU: {corpus_score:.2f}, 句子级BLEU: {avg_sentence_score:.2f}, 文本长度: {text_length}词)"
                
            return final_score, detail
        except Exception as e:
            logger.error(f"计算BLEU分数时出错: {str(e)}")
            return 0.0, "计算BLEU分数时出错，无法评估译文与参考译文的匹配程度。"
    
    def _evaluate_terminology(self, 
                             source_text: str, 
                             translated_text: str,
                             domain: str,
                             source_language: str,
                             target_language: str) -> Tuple[float, str]:
        """
        使用术语库评估术语准确性
        
        Args:
            source_text: 源文本
            translated_text: 待评估的翻译文本
            domain: 领域名称
            source_language: 源语言代码
            target_language: 目标语言代码
            
        Returns:
            术语准确性得分及详细反馈
        """
        # 加载领域术语库
        terminology = data_service.load_terminology(domain, source_language, target_language)
        
        if not terminology:
            logger.warning(f"未找到领域{domain}的术语库，使用默认评分0.5")
            return 0.5, f"未找到相关领域({domain})的术语库，无法评估术语准确性。"
        
        # 在源文本中查找术语
        found_terms = []
        for term_entry in terminology:
            # 使用正则表达式确保匹配完整的词，而不是部分词
            if source_language == "zh":
                # 中文不需要词边界匹配
                pattern = re.compile(re.escape(term_entry.source_term))
            else:
                # 英文需要词边界匹配
                pattern = re.compile(r'\b' + re.escape(term_entry.source_term) + r'\b', re.IGNORECASE)
                
            if pattern.search(source_text):
                found_terms.append(term_entry)
        
        if not found_terms:
            logger.info(f"源文本中未发现术语库中的专业术语，术语库共有{len(terminology)}个术语")
            return 0.8, "源文本中未发现术语库中的专业术语，无需检查术语翻译准确性。"
        
        # 评估术语翻译准确性
        correct_terms = 0
        incorrect_terms = []
        partially_correct_terms = []
        
        for term_entry in found_terms:
            # 检查目标术语是否在译文中
            if target_language == "zh":
                # 中文不需要词边界匹配
                pattern = re.compile(re.escape(term_entry.target_term))
            else:
                # 英文需要词边界匹配，且忽略大小写
                pattern = re.compile(r'\b' + re.escape(term_entry.target_term) + r'\b', re.IGNORECASE)
            
            if pattern.search(translated_text):
                correct_terms += 1
            else:
                # 检查是否部分匹配
                # 将术语拆分为单词，检查是否有部分单词匹配
                if target_language != "zh":
                    words = term_entry.target_term.lower().split()
                    matched_words = 0
                    for word in words:
                        if re.search(r'\b' + re.escape(word) + r'\b', translated_text.lower()):
                            matched_words += 1
                    
                    # 如果有超过半数的单词匹配，认为是部分正确
                    if matched_words > 0 and matched_words / len(words) >= 0.5:
                        partially_correct_terms.append((term_entry, matched_words / len(words)))
                        # 部分正确的术语按50%计入正确数
                        correct_terms += 0.5
                        continue
                
                incorrect_terms.append(term_entry)
        
        # 计算得分
        if len(found_terms) > 0:
            score = correct_terms / len(found_terms)
        else:
            score = 0.5  # 默认中等分数
        
        # 生成反馈
        if score >= 0.8:
            feedback = f"术语翻译准确性高，在{len(found_terms)}个专业术语中，正确使用了{correct_terms:.1f}个术语。"
        elif score >= 0.5:
            feedback = f"部分术语翻译准确，在{len(found_terms)}个专业术语中，正确使用了{correct_terms:.1f}个术语，但仍有改进空间。"
        else:
            feedback = f"术语翻译准确性较低，在{len(found_terms)}个专业术语中，只正确使用了{correct_terms:.1f}个术语，需要注意专业术语的使用。"
        
        # 添加具体错误信息
        if incorrect_terms:
            feedback += "\n以下术语可能翻译不准确："
            for term in incorrect_terms:
                feedback += f"\n- '{term.source_term}'应翻译为'{term.target_term}'，但在译文中未找到。"
        
        # 添加部分正确的术语信息
        if partially_correct_terms:
            feedback += "\n以下术语翻译部分正确，但可能需要完善："
            for term, match_ratio in partially_correct_terms:
                feedback += f"\n- '{term.source_term}'的标准译法是'{term.target_term}'，当前译文中部分匹配。"
        
        return score, feedback
        
    def _evaluate_terminology_from_reference(self,
                                            source_text: str,
                                            translated_text: str,
                                            reference_text: str,
                                            source_language: str,
                                            target_language: str) -> Tuple[float, str, Dict[str, str]]:
        """
        从参考文本中提取术语并评估术语准确性
        
        Args:
            source_text: 源文本
            translated_text: 待评估的翻译文本
            reference_text: 参考译文
            source_language: 源语言代码
            target_language: 目标语言代码
            
        Returns:
            术语准确性得分、详细反馈和提取的术语对照表
        """
        # 从源文本和参考文本中提取术语对照表
        extracted_terms = self._extract_terms_from_texts(source_text, reference_text, source_language, target_language)
        
        if not extracted_terms:
            logger.warning("未能从参考文本中提取出术语对照，使用默认评分0.5")
            return 0.5, "未能从参考文本中提取出术语对照，无法评估术语准确性。", {}
        
        # 评估术语翻译准确性
        correct_terms = 0
        incorrect_terms = []
        partially_correct_terms = []
        
        for source_term, target_term in extracted_terms.items():
            # 检查目标术语是否在译文中
            if target_language == "zh":
                # 中文不需要词边界匹配
                pattern = re.compile(re.escape(target_term))
            else:
                # 英文需要词边界匹配，且忽略大小写
                pattern = re.compile(r'\b' + re.escape(target_term) + r'\b', re.IGNORECASE)
            
            if pattern.search(translated_text):
                correct_terms += 1
            else:
                # 检查是否部分匹配
                # 将术语拆分为单词，检查是否有部分单词匹配
                if target_language != "zh":
                    words = target_term.lower().split()
                    if len(words) > 1:  # 多个单词的术语才检查部分匹配
                        matched_words = 0
                        for word in words:
                            if len(word) > 2 and re.search(r'\b' + re.escape(word) + r'\b', translated_text.lower()):
                                matched_words += 1
                        
                        # 如果有超过半数的单词匹配，认为是部分正确
                        if matched_words > 0 and matched_words / len(words) >= 0.5:
                            partially_correct_terms.append((source_term, target_term, matched_words / len(words)))
                            # 部分正确的术语按比例计入正确数
                            correct_terms += matched_words / len(words)
                            continue
                
                incorrect_terms.append((source_term, target_term))
        
        # 计算得分
        if len(extracted_terms) > 0:
            score = correct_terms / len(extracted_terms)
        else:
            score = 0.5  # 默认中等分数
        
        # 生成反馈
        if score >= 0.8:
            feedback = f"术语翻译准确性高，从参考文本中提取的{len(extracted_terms)}个术语中，正确使用了{correct_terms:.1f}个。"
        elif score >= 0.5:
            feedback = f"部分术语翻译准确，从参考文本中提取的{len(extracted_terms)}个术语中，正确使用了{correct_terms:.1f}个，但仍有改进空间。"
        else:
            feedback = f"术语翻译准确性较低，从参考文本中提取的{len(extracted_terms)}个术语中，只正确使用了{correct_terms:.1f}个，需要注意专业术语的使用。"
        
        # 添加具体错误信息
        if incorrect_terms:
            feedback += "\n以下术语可能翻译不准确："
            for source_term, target_term in incorrect_terms:
                feedback += f"\n- '{source_term}'应翻译为'{target_term}'，但在译文中未找到。"
        
        # 添加部分正确的术语信息
        if partially_correct_terms:
            feedback += "\n以下术语翻译部分正确，但可能需要完善："
            for source_term, target_term, match_ratio in partially_correct_terms:
                feedback += f"\n- '{source_term}'的参考译法是'{target_term}'，当前译文中部分匹配。"
        
        return score, feedback, extracted_terms
        
    def _evaluate_terminology_with_ai(self,
                                    source_text: str,
                                    translated_text: str,
                                    domain: str,
                                    source_language: str,
                                    target_language: str) -> Tuple[float, str, Dict[str, str]]:
        """
        使用AI提取并评估术语准确性
        
        Args:
            source_text: 源文本
            translated_text: 待评估的翻译文本
            domain: 领域名称
            source_language: 源语言代码
            target_language: 目标语言代码
            
        Returns:
            术语准确性得分、详细反馈和提取的术语对照表
        """
        try:
            # 构建AI提示语，提取专业术语
            prompt = f"""
请从以下{source_language}源文本和{target_language}译文中，提取专业术语及其对应的翻译。
输出格式为JSON，格式为：{{"源语言术语": "目标语言术语", ...}}
只返回JSON格式，不要添加其他说明。

源文本（{source_language}）:
{source_text}

译文（{target_language}）:
{translated_text}
            """
            
            # 调用LLM服务提取术语（同步方式）
            logger.info("调用AI提取术语...")
            import httpx
            import json
            
            # 创建同步客户端调用
            client = httpx.Client(timeout=60.0)
            try:
                # 获取llm服务同步获取AI完成结果
                result = client.post(
                    f"{settings.CUSTOM_API_BASE_URL}/{settings.CUSTOM_API_VERSION}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.CUSTOM_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3
                    }
                )
                
                if result.status_code == 200:
                    result_json = result.json()
                    content = result_json["choices"][0]["message"]["content"]
                else:
                    logger.error(f"AI API调用失败: {result.status_code} - {result.text}")
                    return 0.5, "AI提取术语失败，无法评估术语准确性。", {}
            except Exception as e:
                logger.error(f"AI API调用异常: {str(e)}")
                return 0.5, "AI API调用异常，无法提取术语。", {}
            finally:
                client.close()
            
            # 解析AI返回的JSON
            try:
                # 尝试从内容中提取JSON部分
                import re
                json_match = re.search(r'({[\s\S]*})', content)
                if json_match:
                    content = json_match.group(1)
                    
                extracted_terms = json.loads(content)
                logger.info(f"AI提取到{len(extracted_terms)}个术语")
            except Exception as e:
                logger.error(f"解析AI返回的术语JSON失败: {str(e)}")
                logger.error(f"原始响应: {content}")
                return 0.5, "AI提取术语失败，无法评估术语准确性。", {}
            
            # 评估术语翻译准确性 - 与译文比对
            correct_terms = len(extracted_terms)  # 默认所有术语都是正确的，因为是从译文中提取的
            
            # 生成反馈
            feedback = f"AI从文本中提取了{len(extracted_terms)}个术语对照。"
            
            # 根据术语数量给出评分
            if len(extracted_terms) > 0:
                score = min(1.0, len(extracted_terms) / 10)  # 术语越多，分数越高，最高1.0
                if len(extracted_terms) > 5:
                    feedback += f" 文本中包含丰富的专业术语，术语翻译准确性高。"
                else:
                    feedback += f" 文本中包含一些专业术语，术语翻译质量不错。"
            else:
                score = 0.5  # 默认中等分数
                feedback += f" 未能提取到专业术语，可能是文本中不包含专业术语，或提取失败。"
                
            return score, feedback, extracted_terms
            
        except Exception as e:
            logger.error(f"AI评估术语准确性时出错: {str(e)}")
            return 0.5, "AI评估术语准确性时出错，无法评估术语准确性。", {}
    
    def _extract_terms_from_texts(self, 
                               source_text: str, 
                               reference_text: str,
                               source_language: str,
                               target_language: str) -> Dict[str, str]:
        """
        从源文本和参考文本中提取可能的术语对照表
        
        Args:
            source_text: 源文本
            reference_text: 参考译文
            source_language: 源语言代码
            target_language: 目标语言代码
            
        Returns:
            提取的术语对照表 {源术语: 目标术语}
        """
        # 改进的术语提取实现
        extracted_terms = {}
        
        # 使用不同策略根据语言对
        if source_language == "zh" and target_language == "en":
            # 1. 从中文提取可能的术语
            # 使用jieba提取名词短语
            import jieba.posseg as pseg
            words = pseg.cut(source_text)
            
            # 找出所有名词和名词短语
            nouns = []
            current_phrase = []
            
            for word, flag in words:
                # 名词标记为 'n', 'ng', 'nz', 'vn'等
                if flag.startswith('n') or flag == 'vn':
                    current_phrase.append(word)
                elif current_phrase:
                    if len(''.join(current_phrase)) >= 2:  # 至少2个字符
                        nouns.append(''.join(current_phrase))
                    current_phrase = []
            
            # 添加最后一个短语
            if current_phrase and len(''.join(current_phrase)) >= 2:
                nouns.append(''.join(current_phrase))
            
            # 添加更长的名词短语（通过正则匹配连续的2-5个中文字符）
            longer_nouns = re.findall(r'[\u4e00-\u9fa5]{2,5}', source_text)
            nouns.extend([n for n in longer_nouns if n not in nouns])
            
            # 2. 从英文参考文本中提取可能的术语
            # 提取专业术语常见模式（首字母大写的短语、包含连字符的词等）
            capitalized_patterns = re.findall(r'\b[A-Z][a-z]*(?:\s+[a-z]+){0,3}\b', reference_text)
            hyphenated_words = re.findall(r'\b\w+(?:-\w+)+\b', reference_text)
            
            # 合并所有英文候选术语
            english_terms = capitalized_patterns + hyphenated_words
            
            # 3. 尝试匹配
            # 按长度排序中文术语（优先匹配长术语）
            nouns.sort(key=len, reverse=True)
            
            # 尝试建立中英文术语对应关系
            for noun in nouns:
                if len(noun) < 2:  # 跳过太短的词
                    continue
                    
                # 在源文本中查找该名词的位置
                noun_positions = [m.start() for m in re.finditer(re.escape(noun), source_text)]
                if not noun_positions:
                    continue
                    
                # 对每个英文术语尝试匹配
                best_match = None
                max_score = 0
                
                for eng_term in english_terms:
                    if len(eng_term) < 3:  # 跳过太短的英文词
                        continue
                        
                    # 计算相似度得分
                    # 1. 在参考文本中的位置是否接近
                    eng_positions = [m.start() for m in re.finditer(re.escape(eng_term), reference_text)]
                    if not eng_positions:
                        continue
                        
                    # 计算相对位置相似度
                    position_scores = []
                    for zh_pos in noun_positions:
                        zh_rel_pos = zh_pos / len(source_text)
                        for eng_pos in eng_positions:
                            eng_rel_pos = eng_pos / len(reference_text)
                            # 计算相对位置差异
                            pos_diff = abs(zh_rel_pos - eng_rel_pos)
                            # 转换为相似度分数 (0-1)
                            pos_score = max(0, 1 - pos_diff * 2)
                            position_scores.append(pos_score)
                    
                    if not position_scores:
                        continue
                        
                    # 使用最高的位置相似度
                    position_score = max(position_scores)
                    
                    # 2. 单词长度比例
                    length_ratio = min(len(noun) / 2, len(eng_term) / 2) / max(len(noun) / 2, len(eng_term) / 2)
                    
                    # 综合得分
                    score = position_score * 0.7 + length_ratio * 0.3
                    
                    if score > max_score and score > 0.5:  # 设置阈值
                        max_score = score
                        best_match = eng_term
                
                # 如果找到最佳匹配，添加到术语对照表
                if best_match:
                    extracted_terms[noun] = best_match
                    # 从候选列表中移除，避免重复使用
                    if best_match in english_terms:
                        english_terms.remove(best_match)
        
        elif source_language == "en" and target_language == "zh":
            # 英译中的情况，与中译英类似但角色互换
            # 从英文提取术语
            capitalized_patterns = re.findall(r'\b[A-Z][a-z]*(?:\s+[a-z]+){0,3}\b', source_text)
            hyphenated_words = re.findall(r'\b\w+(?:-\w+)+\b', source_text)
            tech_words = re.findall(r'\b[a-z]+(?:ics|ity|tion|sion|ment|logy|graphy|meter)\b', source_text, re.IGNORECASE)
            
            # 合并所有英文术语
            english_terms = capitalized_patterns + hyphenated_words + tech_words
            english_terms = list(set(english_terms))  # 去重
            
            # 从中文提取术语
            import jieba.posseg as pseg
            words = pseg.cut(reference_text)
            
            nouns = []
            current_phrase = []
            
            for word, flag in words:
                if flag.startswith('n') or flag == 'vn':
                    current_phrase.append(word)
                elif current_phrase:
                    if len(''.join(current_phrase)) >= 2:
                        nouns.append(''.join(current_phrase))
                    current_phrase = []
            
            if current_phrase and len(''.join(current_phrase)) >= 2:
                nouns.append(''.join(current_phrase))
            
            # 添加更长的名词短语
            longer_nouns = re.findall(r'[\u4e00-\u9fa5]{2,5}', reference_text)
            nouns.extend([n for n in longer_nouns if n not in nouns])
            
            # 按长度排序英文术语
            english_terms.sort(key=len, reverse=True)
            
            # 尝试匹配
            for eng_term in english_terms:
                if len(eng_term) < 3:  # 跳过太短的词
                    continue
                    
                # 在源文本中查找位置
                eng_positions = [m.start() for m in re.finditer(re.escape(eng_term), source_text, re.IGNORECASE)]
                if not eng_positions:
                    continue
                    
                # 对每个中文名词尝试匹配
                best_match = None
                max_score = 0
                
                for noun in nouns:
                    if len(noun) < 2:
                        continue
                        
                    # 计算位置相似度
                    noun_positions = [m.start() for m in re.finditer(re.escape(noun), reference_text)]
                    if not noun_positions:
                        continue
                        
                    position_scores = []
                    for eng_pos in eng_positions:
                        eng_rel_pos = eng_pos / len(source_text)
                        for zh_pos in noun_positions:
                            zh_rel_pos = zh_pos / len(reference_text)
                            pos_diff = abs(eng_rel_pos - zh_rel_pos)
                            pos_score = max(0, 1 - pos_diff * 2)
                            position_scores.append(pos_score)
                    
                    if not position_scores:
                        continue
                        
                    position_score = max(position_scores)
                    length_ratio = min(len(eng_term) / 3, len(noun) / 2) / max(len(eng_term) / 3, len(noun) / 2)
                    
                    score = position_score * 0.7 + length_ratio * 0.3
                    
                    if score > max_score and score > 0.5:
                        max_score = score
                        best_match = noun
                
                if best_match:
                    extracted_terms[eng_term] = best_match
                    if best_match in nouns:
                        nouns.remove(best_match)
        
        # 如果提取的术语少于2个，尝试更简单的基于位置的匹配
        if len(extracted_terms) < 2:
            # 简单实现：基于位置匹配
            if source_language == "zh" and target_language == "en":
                # 查找中文中较长的词语
                zh_words = list(jieba.cut(source_text))
                for word in zh_words:
                    if len(word) >= 2:
                        # 找出单词在文本中的位置
                        word_pos = source_text.find(word) / len(source_text)
                        
                        # 找出英文中位置相近的大写单词
                        en_matches = re.finditer(r'\b[A-Z][a-z]*(?:\s+[a-z]+)*\b', reference_text)
                        for match in en_matches:
                            en_word = match.group()
                            en_pos = match.start() / len(reference_text)
                            
                            # 如果位置接近，考虑为术语对
                            if abs(word_pos - en_pos) < 0.2 and len(en_word) >= 3:
                                extracted_terms[word] = en_word
                                break
        
        return extracted_terms
        
    def _evaluate_sentence_structure(self,
                                    source_text: str,
                                    translated_text: str,
                                    source_language: str,
                                    target_language: str) -> Tuple[float, str]:
        """
        评估句式结构，特别是主动句转被动句的情况
        
        Args:
            source_text: 源文本
            translated_text: 待评估的翻译文本
            source_language: 源语言代码
            target_language: 目标语言代码
            
        Returns:
            句式转换得分及详细反馈
        """
        # 本方法主要针对中译英时主动句应转为被动句的情况
        if source_language != "zh" or target_language != "en":
            return 0.7, "当前评估仅支持中译英的句式转换评估。"
        
        # 分句
        source_sentences = nltk.sent_tokenize(source_text)
        translated_sentences = nltk.sent_tokenize(translated_text)
        
        # 如果句子数量差异太大，可能分句不准确
        if abs(len(source_sentences) - len(translated_sentences)) > len(source_sentences) * 0.3:
            return 0.5, "源文本与译文的句子数量差异较大，无法准确评估句式转换。"
        
        # 检测英文中的被动句
        passive_pattern = re.compile(r'\b(is|are|was|were|be|been|being)\s+(\w+ed|irregular_past_participle)\b', re.IGNORECASE)
        
        # 主动句指示词（中文）
        active_indicators = ["我们", "作者", "研究者", "科学家", "本文", "本研究", "实验", "分析", "测试", "发现"]
        
        # 统计结果
        active_in_source = 0
        passive_in_target = 0
        
        # 检测源文本中的主动句
        for sentence in source_sentences:
            for indicator in active_indicators:
                if indicator in sentence:
                    active_in_source += 1
                    break
        
        # 检测译文中的被动句
        for sentence in translated_sentences:
            if passive_pattern.search(sentence):
                passive_in_target += 1
        
        # 评估得分
        # 简单情况：如果源文本中主动句较多，而译文中被动句较少，则得分较低
        if active_in_source > 0:
            # 理想情况下，主动句数量和被动句数量应该接近
            score = min(1.0, passive_in_target / active_in_source)
        else:
            # 如果源文本中没有明显的主动句，给予较高得分
            score = 0.8
        
        # 生成反馈
        if score >= 0.8:
            feedback = "句式转换良好，中文主动句在英文中适当地转换为被动句。"
        elif score >= 0.5:
            feedback = "句式转换存在一些问题，部分中文主动句未在英文中转换为被动句。"
        else:
            feedback = "句式转换欠佳，大多数中文主动句在英文中仍保持主动形式，不符合英语学术写作习惯。"
        
        feedback += f"\n源文本中检测到{active_in_source}个主动句，而译文中有{passive_in_target}个被动句。"
        
        return score, feedback
    
    def _evaluate_discourse(self, 
                           translated_text: str, 
                           reference_texts: List[str]) -> Tuple[float, str]:
        """
        评估语篇连贯性
        
        Args:
            translated_text: 待评估的翻译文本
            reference_texts: 参考译文列表
            
        Returns:
            语篇连贯性得分及详细反馈
        """
        try:
            # 1. 检查连接词的使用
            # 分不同类型的连接词，更全面地评估连贯性
            causality_words = ["because", "since", "therefore", "thus", "consequently", "as a result", 
                             "hence", "so", "accordingly", "due to", "owing to", "for this reason"]
            
            contrast_words = ["however", "nevertheless", "yet", "although", "though", "but", "despite", 
                            "in contrast", "on the other hand", "conversely", "whereas", "while", 
                            "on the contrary", "nonetheless"]
            
            addition_words = ["furthermore", "moreover", "in addition", "additionally", "besides", 
                            "also", "what's more", "as well as", "not only...but also", "similarly"]
            
            sequence_words = ["first", "firstly", "second", "secondly", "third", "thirdly", "then", 
                            "next", "finally", "lastly", "subsequently", "afterward", "previously"]
            
            conclusion_words = ["in conclusion", "to conclude", "in summary", "to summarize", "overall", 
                              "ultimately", "in brief", "in short", "to sum up"]
            
            # 所有连接词列表
            all_cohesion_words = (causality_words + contrast_words + 
                                 addition_words + sequence_words + conclusion_words)
            
            # 防止连接词的部分匹配
            def count_whole_word(word, text):
                return len(re.findall(r'\b' + re.escape(word) + r'\b', text.lower()))
            
            # 计算连接词在译文中的出现次数
            causality_count = sum(count_whole_word(word, translated_text) for word in causality_words)
            contrast_count = sum(count_whole_word(word, translated_text) for word in contrast_words)
            addition_count = sum(count_whole_word(word, translated_text) for word in addition_words)
            sequence_count = sum(count_whole_word(word, translated_text) for word in sequence_words)
            conclusion_count = sum(count_whole_word(word, translated_text) for word in conclusion_words)
            
            total_cohesion_count = (causality_count + contrast_count + 
                                   addition_count + sequence_count + conclusion_count)
            
            # 检查连接词的多样性
            used_cohesion_words = set()
            for word in all_cohesion_words:
                if count_whole_word(word, translated_text) > 0:
                    used_cohesion_words.add(word)
            
            cohesion_diversity = len(used_cohesion_words) / max(1, total_cohesion_count)
            
            # 计算参考译文中的连接词使用情况
            ref_total_counts = []
            ref_diversity_scores = []
            
            for ref_text in reference_texts:
                ref_count = sum(count_whole_word(word, ref_text) for word in all_cohesion_words)
                ref_total_counts.append(ref_count)
                
                ref_used_words = set()
                for word in all_cohesion_words:
                    if count_whole_word(word, ref_text) > 0:
                        ref_used_words.add(word)
                
                ref_diversity = len(ref_used_words) / max(1, ref_count)
                ref_diversity_scores.append(ref_diversity)
            
            avg_ref_count = sum(ref_total_counts) / len(ref_total_counts) if ref_total_counts else 0
            avg_ref_diversity = sum(ref_diversity_scores) / len(ref_diversity_scores) if ref_diversity_scores else 0
            
            # 2. 句子长度的变化
            sentences = nltk.sent_tokenize(translated_text)
            sentence_lengths = [len(sent.split()) for sent in sentences]
            
            # 计算句子长度的标准差，过大表示句子长度差异过大
            if len(sentence_lengths) > 1:
                mean_length = sum(sentence_lengths) / len(sentence_lengths)
                variance = sum((length - mean_length) ** 2 for length in sentence_lengths) / len(sentence_lengths)
                std_dev = variance ** 0.5
                
                # 计算变异系数(CV)，标准化标准差，消除句子长度的影响
                cv = std_dev / mean_length if mean_length > 0 else 0
                
                # CV越小表示句子长度越均匀
                length_variation_score = min(1.0, max(0.0, 1.0 - cv))
            else:
                length_variation_score = 0.7  # 单句文本，给予中等分数
            
            # 3. 检查重复词语（除了常用词和停用词外）
            # 常用英文停用词
            stopwords = {"the", "a", "an", "and", "in", "on", "at", "to", "for", "with", "by", "of", 
                       "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", 
                       "do", "does", "did", "can", "could", "will", "would", "should", "may", "might", 
                       "must", "that", "this", "these", "those", "it", "they", "them", "their", "there", 
                       "here", "where", "when", "how", "why", "what", "who", "whom", "which"}
            
            words = re.findall(r'\b\w+\b', translated_text.lower())
            word_counts = {}
            
            for word in words:
                if len(word) > 3 and word not in stopwords:  # 跳过短词和停用词
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # 计算重复系数 (重复次数>=3的词占总词数的比例)
            repeated_words = [word for word, count in word_counts.items() if count >= 3]
            total_words = len(words)
            repetition_ratio = sum(word_counts[word] for word in repeated_words) / total_words if total_words > 0 else 0
            
            # 计算重复词得分
            repetition_score = min(1.0, max(0.0, 1.0 - repetition_ratio * 3))  # 重复率越低，得分越高
            
            # 4. 检查指代一致性
            # 检查人称代词和物主代词的一致性
            pronouns = ["he", "she", "it", "they", "his", "her", "its", "their", "him", "them"]
            
            # 简单检查第一个代词前有无清晰的指代对象
            pronoun_issues = 0
            for pronoun in pronouns:
                pronoun_positions = [m.start() for m in re.finditer(r'\b' + re.escape(pronoun) + r'\b', translated_text.lower())]
                for pos in pronoun_positions:
                    # 检查代词前50个字符内是否有可能的指代对象（简化处理）
                    prefix = translated_text[max(0, pos - 50):pos].lower()
                    if not any(noun in prefix for noun in ["the", "a", "an"]):  # 简单假设：冠词后面跟着名词
                        pronoun_issues += 1
            
            pronoun_score = min(1.0, max(0.0, 1.0 - pronoun_issues / max(10, len(sentences))))
            
            # 5. 计算最终连贯性分数
            # 根据参考文本校准连接词分数
            if avg_ref_count > 0:
                cohesion_count_score = min(1.0, total_cohesion_count / avg_ref_count)
            else:
                # 无参考文本时，基于连接词密度评分
                text_length = len(words)
                expected_cohesion_count = max(1, text_length / 100)  # 假设每100个词有1个连接词
                cohesion_count_score = min(1.0, total_cohesion_count / expected_cohesion_count)
            
            # 连接词多样性得分
            if avg_ref_diversity > 0:
                cohesion_diversity_score = min(1.0, cohesion_diversity / avg_ref_diversity)
            else:
                cohesion_diversity_score = min(1.0, cohesion_diversity)
            
            # 组合连接词得分
            cohesion_score = 0.7 * cohesion_count_score + 0.3 * cohesion_diversity_score
            
            # 最终得分：连接词(40%) + 句长变化(20%) + 重复词(20%) + 指代一致性(20%)
            final_score = (0.4 * cohesion_score + 
                         0.2 * length_variation_score + 
                         0.2 * repetition_score + 
                         0.2 * pronoun_score)
            
            # 确保最终分数在0-1范围内
            final_score = max(0.0, min(1.0, final_score))
            
            # 生成反馈
            feedback = f"语篇连贯性评分为{final_score:.2f}。"
            
            cohesion_feedback = []
            length_feedback = []
            repetition_feedback = []
            pronoun_feedback = []
            
            # 连接词反馈
            if cohesion_score < 0.6:
                if total_cohesion_count < 1:
                    cohesion_feedback.append("文本中几乎没有使用连接词，严重影响逻辑连贯性。")
                elif cohesion_diversity < 0.5:
                    cohesion_feedback.append("连接词使用不够多样化，相同的连接词重复使用。")
                else:
                    cohesion_feedback.append("连接词使用不足，影响逻辑连贯性。")
                
                missing_types = []
                if causality_count == 0:
                    missing_types.append("因果关系(because, therefore等)")
                if contrast_count == 0:
                    missing_types.append("转折关系(however, although等)")
                if addition_count == 0:
                    missing_types.append("补充关系(furthermore, moreover等)")
                if sequence_count == 0:
                    missing_types.append("顺序关系(first, then, finally等)")
                if conclusion_count == 0:
                    missing_types.append("总结关系(in conclusion, overall等)")
                
                if missing_types:
                    cohesion_feedback.append(f"缺少表示{', '.join(missing_types)}的连接词。")
                
                cohesion_feedback.append("建议适当增加过渡词和连接词，使文本逻辑更清晰。")
            elif cohesion_score < 0.8:
                cohesion_feedback.append("连接词使用基本合理，但可以更加丰富多样。")
            else:
                cohesion_feedback.append("连接词使用恰当且多样，有效增强了文本的逻辑连贯性。")
            
            # 句长变化反馈
            if length_variation_score < 0.6:
                length_feedback.append(f"句子长度变化过大(平均长度: {sum(sentence_lengths)/len(sentence_lengths):.1f}词)，阅读流畅度受影响。")
                length_feedback.append("建议平衡长短句的使用，使句子长度更加协调。")
            else:
                length_feedback.append("句子长度分布合理，有助于阅读节奏和流畅度。")
            
            # 重复词反馈
            if repetition_score < 0.7 and repeated_words:
                rep_examples = repeated_words[:3]  # 最多列出3个例子
                repetition_feedback.append(f"部分词语重复过多，例如: {', '.join(rep_examples)}等。")
                repetition_feedback.append("建议使用同义词或改变表达方式，减少不必要的重复。")
            else:
                repetition_feedback.append("文本没有明显的词语重复问题，表达多样且自然。")
            
            # 指代一致性反馈
            if pronoun_score < 0.7 and pronoun_issues > 0:
                pronoun_feedback.append("存在代词指代不明确的情况，可能导致读者困惑。")
                pronoun_feedback.append("建议确保每个代词都有清晰的指代对象，必要时可以重复使用名词。")
            else:
                pronoun_feedback.append("代词使用恰当，指代关系清晰。")
            
            # 组合所有反馈
            section_feedbacks = [
                "连接词: " + " ".join(cohesion_feedback),
                "句子结构: " + " ".join(length_feedback),
                "词语重复: " + " ".join(repetition_feedback),
                "指代一致性: " + " ".join(pronoun_feedback)
            ]
            
            detailed_feedback = "\n- ".join([""] + section_feedbacks)
            feedback += detailed_feedback
            
            # 总结性评价
            if final_score >= 0.8:
                feedback += "\n\n总体而言，译文语篇连贯性优秀，逻辑清晰，表达自然流畅。"
            elif final_score >= 0.6:
                feedback += "\n\n总体而言，译文语篇连贯性良好，有些小问题但不影响整体阅读。"
            elif final_score >= 0.4:
                feedback += "\n\n总体而言，译文语篇连贯性一般，有明显的改进空间。"
            else:
                feedback += "\n\n总体而言，译文语篇连贯性较差，多个方面都需要重点改进。"
            
            return final_score, feedback
            
        except Exception as e:
            logger.error(f"评估语篇连贯性时出错: {str(e)}")
            return 0.5, f"评估语篇连贯性时出错: {str(e)}"
    
    def _generate_suggestions(self,
                             bleu_score: float,
                             terminology_score: float,
                             sentence_score: float,
                             discourse_score: float,
                             terminology_feedback: str,
                             sentence_feedback: str,
                             discourse_feedback: str) -> List[str]:
        """
        根据各项评分生成改进建议
        
        Args:
            bleu_score: BLEU分数
            terminology_score: 术语准确性分数
            sentence_score: 句式转换分数
            discourse_score: 语篇连贯性分数
            terminology_feedback: 术语评估详细反馈
            sentence_feedback: 句式评估详细反馈
            discourse_feedback: 语篇评估详细反馈
            
        Returns:
            改进建议列表
        """
        suggestions = []
        
        # 根据各项分数，生成改进建议
        if terminology_score < 0.7:
            suggestions.append("注意专业术语的准确翻译，参考术语库或领域专业词典。")
            
            # 从详细反馈中提取具体问题术语
            if "以下术语可能翻译不准确" in terminology_feedback:
                for line in terminology_feedback.split("\n"):
                    if line.startswith("- '"):
                        term_suggestion = line.strip()
                        if term_suggestion not in suggestions:
                            suggestions.append(term_suggestion)
        
        if sentence_score < 0.7:
            suggestions.append("在中译英时，注意将中文的主动句适当转换为英文的被动句，符合英语学术写作习惯。")
            suggestions.append("特别关注表达研究过程、方法和结果的句子，这些在英文学术写作中通常使用被动语态。")
        
        if discourse_score < 0.7:
            if "连接词使用不足" in discourse_feedback:
                suggestions.append("增加过渡词和连接词（如however, therefore, furthermore等）以提高文本的逻辑连贯性。")
            
            if "句子长度变化过大" in discourse_feedback:
                suggestions.append("平衡长短句的使用，避免句子长度差异过大，提高阅读流畅度。")
            
            if "部分词语重复过多" in discourse_feedback:
                suggestions.append("避免过度重复相同词语，可使用同义词或改变表达方式。")
        
        if bleu_score < 0.6:
            suggestions.append("整体译文与参考译文差异较大，建议参考高质量翻译范例，学习表达方式和风格。")
        
        # 如果没有明显问题，给予积极反馈
        if not suggestions:
            suggestions.append("译文整体质量良好，继续保持。")
        
        return suggestions


# 单例实例
evaluation_service = EvaluationService() 
