// API 基础URL
const API_BASE_URL = 'http://localhost:8000/api';

// DOM 元素
const initDataBtn = document.getElementById('init-data');
const statusValue = document.getElementById('status-value');
const translateBtn = document.getElementById('translate-btn');
const evaluateBtn = document.getElementById('evaluate-btn');
const loadTerminologyBtn = document.getElementById('load-terminology-btn');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingMessage = document.getElementById('loading-message');
const viewCriteriaBtn = document.getElementById('view-criteria-btn');
const criteriaModal = document.getElementById('criteria-modal');
const criteriaContent = document.getElementById('criteria-content');

// 模型相关元素
const fetchModelsBtn = document.getElementById('fetch-models');
const modelSelect = document.getElementById('model-select');

// 参考文本相关元素
const referenceSelect = document.getElementById('reference-select');
const loadReferenceBtn = document.getElementById('load-reference');
const uploadReferenceBtn = document.getElementById('upload-reference-btn');
const uploadForm = document.getElementById('upload-form');
const referenceFileInput = document.getElementById('reference-file');
const refSourceLangSelect = document.getElementById('ref-source-lang');
const refTargetLangSelect = document.getElementById('ref-target-lang');
const submitReferenceFileBtn = document.getElementById('submit-reference-file');
const cancelUploadBtn = document.getElementById('cancel-upload');
const referenceText = document.getElementById('reference-text');

// 参考文本来源选项
const referenceFileOption = document.getElementById('reference-file-option');
const referenceManualOption = document.getElementById('reference-manual-option');

// 术语管理相关元素
const terminologyModeSelect = document.getElementById('terminology-mode');
const applyTermModeBtn = document.getElementById('apply-term-button');

// 页面加载时检查API状态
document.addEventListener('DOMContentLoaded', async () => {
    // 添加全局调试函数
    window.debugButtonIssue = function() {
        console.log("开始调试按钮问题...");
        
        // 检查按钮是否存在
        const batchAddBtn = document.getElementById('batch-add-btn');
        console.log("批量添加按钮元素:", batchAddBtn);
        
        if (batchAddBtn) {
            // 尝试手动触发点击事件
            console.log("尝试触发批量添加按钮点击事件");
            batchAddBtn.click();
        } else {
            console.error("找不到批量添加按钮元素!");
        }
        
        // 检查其他按钮作为参照
        const addTermBtn = document.getElementById('add-term-btn');
        console.log("普通添加按钮元素:", addTermBtn);
        
        return "调试信息已输出到控制台";
    };
    
    console.log("DOM已加载完成，可在控制台执行window.debugButtonIssue()进行调试");
    
    // 初始化UI元素
    initializeUI();
    
    // 绑定事件监听器
    bindEventListeners();
    
    // 初始化语言和领域选择
    initializeLanguageAndDomain();
    
    // API和系统初始化
    await checkApiStatus();
    await loadApiConfig();
    await loadReferenceFiles();
    
    // 添加评分标准查看按钮事件
    if (viewCriteriaBtn) {
        viewCriteriaBtn.addEventListener('click', viewScoringCriteria);
    }
    
    // 添加关闭评分标准模态框按钮事件
    if (document.querySelector('.close-btn')) {
        document.querySelector('.close-btn').addEventListener('click', () => {
            criteriaModal.style.display = 'none';
        });
    }
    
    // 点击模态框外部关闭
    window.addEventListener('click', (event) => {
        if (event.target === criteriaModal) {
            criteriaModal.style.display = 'none';
        }
    });
    
    // 设置参考文本来源选项事件监听
    setupReferenceSourceOptions();
});

// 设置参考文本来源选项事件监听
function setupReferenceSourceOptions() {
    // 参考文本来源单选按钮事件
    referenceFileOption.addEventListener('change', updateReferenceSourceUI);
    referenceManualOption.addEventListener('change', updateReferenceSourceUI);
    
    // 初始设置
    updateReferenceSourceUI();
}

// 根据参考文本来源选项更新界面
function updateReferenceSourceUI() {
    const useFile = referenceFileOption.checked;
    
    // 更新参考文本选择和按钮的可用状态
    referenceSelect.disabled = !useFile;
    loadReferenceBtn.disabled = !useFile;
    uploadReferenceBtn.disabled = !useFile;
    
    // 更新文本框的提示文本
    if (useFile) {
        referenceText.placeholder = "加载的参考译文将显示在这里...";
        referenceText.readOnly = true;
        referenceText.style.backgroundColor = "#f8f9fa";
    } else {
        referenceText.placeholder = "请直接输入参考译文...";
        referenceText.readOnly = false;
        referenceText.style.backgroundColor = "#ffffff";
        
        // 清空文本框，如果之前有加载的内容
        if (referenceFileOption.getAttribute('data-loaded') === 'true') {
            referenceText.value = '';
            referenceFileOption.setAttribute('data-loaded', 'false');
        }
    }
}

// 检查API状态
async function checkApiStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        
        if (response.ok) {
            statusValue.textContent = '正常';
            statusValue.style.color = 'green';
        } else {
            statusValue.textContent = '异常';
            statusValue.style.color = 'red';
        }
    } catch (error) {
        console.error('API状态检查失败:', error);
        statusValue.textContent = '无法连接';
        statusValue.style.color = 'red';
    }
}

// 初始化示例数据
async function initializeData() {
    try {
        showLoading('初始化示例数据...');
        const response = await fetch(`${API_BASE_URL}/data/init-sample-data`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('示例数据初始化成功!');
            // 重新加载参考文本列表
            await loadReferenceFiles();
            // 加载术语库
            const sourceLang = document.getElementById('source-lang').value;
            const targetLang = document.getElementById('target-lang').value;
            const domain = document.getElementById('domain').value;
            await loadTerminologyFromDB(sourceLang, targetLang, domain);
        } else {
            alert(`初始化失败: ${data.detail}`);
        }
    } catch (error) {
        alert('初始化示例数据时出错，请查看控制台了解详情');
        console.error('初始化数据失败:', error);
    } finally {
        hideLoading();
    }
}

// 翻译文本
async function translateText() {
    const sourceText = document.getElementById('source-text').value.trim();
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    const model = document.getElementById('model-select').value;
    
    if (!sourceText) {
        alert('请输入需要翻译的文本');
        return;
    }
    
    showLoading('翻译中...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/translation/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_text: sourceText,
                source_language: sourceLang,
                target_language: targetLang,
                domain: domain,
                model: model // 添加模型选择
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        document.getElementById('translated-text').value = data.translated_text;
    } catch (error) {
        console.error('翻译失败:', error);
        alert('翻译失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 评估翻译质量
async function evaluateTranslation() {
    const sourceText = document.getElementById('source-text').value.trim();
    const translatedText = document.getElementById('translated-text').value.trim();
    const referenceText = document.getElementById('reference-text').value.trim();
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    const terminologyMode = document.getElementById('terminology-mode').value;
    
    // 验证必填项
    if (!sourceText || !translatedText) {
        alert('请确保已提供源文本和译文');
        return;
    }
    
    if (!referenceText) {
        const proceed = confirm('未提供参考译文，评估结果可能不准确。是否继续?');
        if (!proceed) return;
    }
    
    // 清除上一次评估结果
    clearEvaluationResults();
    
    showLoading('评估翻译质量中...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/evaluation/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_text: sourceText,
                translated_text: translatedText,
                reference_texts: referenceText ? [referenceText] : [],
                source_language: sourceLang,
                target_language: targetLang,
                domain: domain,
                terminology_mode: terminologyMode
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        displayEvaluationResults(result);
        
        // 根据当前的术语评估模式显示术语
        if (terminologyMode === 'database') {
            // 使用本地术语库进行评估
            await extractTermsFromLocalTerminology(sourceText, translatedText, sourceLang, targetLang, domain);
        } else if (result.extracted_terms) {
            // 显示API返回的术语
            displayExtractedTerms(result.extracted_terms);
        }
    } catch (error) {
        console.error('评估翻译失败:', error);
        alert('评估翻译失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 显示评估结果
function displayEvaluationResults(data) {
    // 更新分数
    document.getElementById('overall-score').textContent = formatScore(data.overall_score.score);
    document.getElementById('bleu-score').textContent = formatScore(data.bleu_score.score);
    document.getElementById('terminology-score').textContent = formatScore(data.terminology_score.score);
    document.getElementById('sentence-score').textContent = formatScore(data.sentence_structure_score.score);
    document.getElementById('discourse-score').textContent = formatScore(data.discourse_score.score);
    
    // 更新分数卡颜色
    updateScoreCardColor('overall-score', data.overall_score.score);
    updateScoreCardColor('bleu-score', data.bleu_score.score);
    updateScoreCardColor('terminology-score', data.terminology_score.score);
    updateScoreCardColor('sentence-score', data.sentence_structure_score.score);
    updateScoreCardColor('discourse-score', data.discourse_score.score);
    
    // 更新详细反馈
    const feedbackHTML = Object.entries(data.detailed_feedback)
        .map(([key, value]) => `<strong>${getFeedbackTitle(key)}:</strong> ${value}`)
        .join('<br><br>');
    
    document.getElementById('detailed-feedback').innerHTML = feedbackHTML;
    
    // 更新建议列表
    const suggestionsHTML = data.suggestions
        .map(suggestion => `<li>${suggestion}</li>`)
        .join('');
    
    document.getElementById('suggestions').innerHTML = suggestionsHTML;
}

// 查看评分标准
async function viewScoringCriteria() {
    showLoading('获取评分标准中...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/evaluation/scoring-criteria`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const criteria = await response.json();
        displayScoringCriteria(criteria);
    } catch (error) {
        console.error('获取评分标准失败:', error);
        alert('获取评分标准失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 显示评分标准
function displayScoringCriteria(criteria) {
    let html = '';
    
    for (const key in criteria) {
        const item = criteria[key];
        html += `<div class="criteria-section">`;
        html += `<h3>${item.name}</h3>`;
        html += `<p>${item.description}</p>`;
        
        html += `<h4>计算方法</h4>`;
        html += `<p>${item.calculation}</p>`;
        
        if (item.weight) {
            html += `<h4>权重</h4>`;
            html += `<p>${item.weight}</p>`;
        }
        
        if (item.interpretation) {
            html += `<h4>分数解释</h4>`;
            html += `<ul>`;
            for (const range in item.interpretation) {
                html += `<li><strong>${range}:</strong> ${item.interpretation[range]}</li>`;
            }
            html += `</ul>`;
        }
        
        html += `</div>`;
    }
    
    criteriaContent.innerHTML = html;
    criteriaModal.style.display = 'flex';
}

// 加载术语库
async function loadTerminology() {
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    
    // 询问用户是否从数据库加载
    const loadFromDB = confirm('是否从数据库加载术语库？\n选择"确定"从数据库加载，选择"取消"从文件加载');
    
    if (loadFromDB) {
        // 从数据库加载
        await loadTerminologyFromDB(sourceLang, targetLang, domain);
    } else {
        // 从文件加载
        try {
            showLoading('加载术语库文件...');
            
            // 创建文件选择器
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.json,.txt';
            
            // 添加一个标志来跟踪是否已经处理了文件选择
            let fileProcessed = false;
            
            // 设置超时，如果用户没有选择文件，自动关闭加载状态
            const loadingTimeout = setTimeout(() => {
                if (!fileProcessed) {
                    fileProcessed = true;
                    hideLoading();
                    console.log("文件选择超时，自动关闭加载状态");
                }
            }, 60000); // 60秒超时
            
            // 添加窗口焦点事件监听器，当用户从文件选择对话框返回窗口时检查
            window.addEventListener('focus', function focusHandler() {
                // 延迟检查，给onchange事件一个触发的机会
                setTimeout(() => {
                    if (!fileProcessed) {
                        fileProcessed = true;
                        hideLoading();
                        clearTimeout(loadingTimeout);
                        window.removeEventListener('focus', focusHandler);
                        console.log("检测到窗口获得焦点但未选择文件，关闭加载状态");
                    }
                }, 300);
            }, { once: false });
            
            // 监听文件选择
            fileInput.onchange = async function(event) {
                fileProcessed = true;
                clearTimeout(loadingTimeout);
                
                const file = event.target.files[0];
                if (!file) {
                    hideLoading();
                    return;
                }
                
                try {
                    // 创建FormData对象
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('domain', domain);
                    formData.append('source_lang', sourceLang);
                    formData.append('target_lang', targetLang);
                    
                    // 调用导入API
                    const response = await fetch(`${API_BASE_URL}/data/terminology/import`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    alert(`成功导入${result.count}个术语`);
                    
                    // 刷新术语库显示
                    await loadTerminologyFromDB(sourceLang, targetLang, domain);
                } catch (error) {
                    console.error('导入术语库失败:', error);
                    alert('导入术语库失败: ' + error.message);
                    hideLoading();
                }
            };
            
            // 触发文件选择
            fileInput.click();
        } catch (error) {
            console.error('加载术语库文件失败:', error);
            alert('加载术语库文件失败: ' + error.message);
            hideLoading();
        }
    }
}

// 从数据库加载术语库
async function loadTerminologyFromDB(sourceLang, targetLang, domain) {
    try {
        showLoading('加载术语库...');
        
        // 调用API获取术语库
        const response = await fetch(`${API_BASE_URL}/data/terminology?domain=${domain}&source_lang=${sourceLang}&target_lang=${targetLang}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const terminology = await response.json();
        
        // 显示术语库
        displayTerminology(terminology);
        
        // 保存到localStorage以便后续使用
        localStorage.setItem('terminology', JSON.stringify(terminology));
        
        hideLoading();
    } catch (error) {
        console.error('加载术语库失败:', error);
        alert('加载术语库失败: ' + error.message);
        hideLoading();
    }
}

// 显示术语库数据
function displayTerminology(terminology) {
    const terminologyTable = document.getElementById('terminology-table');
    const terminologyContainer = document.getElementById('terminology-container');
    
    // 清空表格内容
    terminologyTable.innerHTML = '';
    
    // 检查术语库是否为空
    if (!terminology || terminology.length === 0) {
        const noTermsRow = document.createElement('tr');
        noTermsRow.innerHTML = `<td colspan="3" class="text-center">暂无术语</td>`;
        terminologyTable.appendChild(noTermsRow);
        terminologyContainer.style.display = 'block';
        return;
    }
    
    // 添加表头
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = `
        <th>中文</th>
        <th>英文</th>
        <th>操作</th>
    `;
    terminologyTable.appendChild(headerRow);
    
    // 添加术语条目
    terminology.forEach(term => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${term.source_term}</td>
            <td>${term.target_term}</td>
            <td>
                <button class="btn btn-sm btn-danger delete-term" data-term-id="${term.id}">删除</button>
                <button class="btn btn-sm btn-primary edit-term" data-term-id="${term.id}" data-source="${term.source_term}" data-target="${term.target_term}">编辑</button>
            </td>
        `;
        terminologyTable.appendChild(row);
    });
    
    // 添加删除术语的事件监听器
    const deleteButtons = document.querySelectorAll('.delete-term');
    deleteButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const termId = this.getAttribute('data-term-id');
            const confirmDelete = confirm('确定要删除这个术语吗？');
            if (confirmDelete) {
                try {
                    showLoading('删除术语中...');
                    
                    // 调用API删除术语
                    const response = await fetch(`${API_BASE_URL}/data/terminology/${termId}`, {
                        method: 'DELETE'
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                    }
                    
                    await response.json();
                    
                    // 刷新术语库显示
                    const sourceLang = document.getElementById('source-lang').value;
                    const targetLang = document.getElementById('target-lang').value;
                    const domain = document.getElementById('domain').value;
                    await loadTerminologyFromDB(sourceLang, targetLang, domain);
                } catch (error) {
                    console.error('删除术语失败:', error);
                    alert('删除术语失败: ' + error.message);
                } finally {
                    hideLoading();
                }
            }
        });
    });
    
    // 添加编辑术语的事件监听器
    const editButtons = document.querySelectorAll('.edit-term');
    editButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const termId = this.getAttribute('data-term-id');
            const sourceTerm = this.getAttribute('data-source');
            const targetTerm = this.getAttribute('data-target');
            
            // 弹出编辑对话框
            const newTargetTerm = prompt('请输入新的英文术语:', targetTerm);
            
            if (newTargetTerm !== null && newTargetTerm.trim() !== '') {
                try {
                    showLoading('更新术语中...');
                    
                    // 调用API更新术语
                    const response = await fetch(`${API_BASE_URL}/data/terminology/${termId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            target_term: newTargetTerm.trim()
                        })
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                    }
                    
                    await response.json();
                    
                    // 刷新术语库显示
                    const sourceLang = document.getElementById('source-lang').value;
                    const targetLang = document.getElementById('target-lang').value;
                    const domain = document.getElementById('domain').value;
                    await loadTerminologyFromDB(sourceLang, targetLang, domain);
                } catch (error) {
                    console.error('更新术语失败:', error);
                    alert('更新术语失败: ' + error.message);
                } finally {
                    hideLoading();
                }
            }
        });
    });
    
    // 显示术语库容器
    terminologyContainer.style.display = 'block';
}

// 加载API配置
async function loadApiConfig() {
    try {
        // 直接加载可用模型，不需要显示API配置
        await fetchAvailableModels();
    } catch (error) {
        console.error('加载API配置失败:', error);
    }
}

// 获取可用模型
async function fetchAvailableModels() {
    try {
        // 禁用按钮，避免重复点击
        if (fetchModelsBtn) {
            fetchModelsBtn.disabled = true;
            fetchModelsBtn.textContent = "获取中...";
        }
        
        // 显示加载指示器
        showLoading('获取可用模型中...');
        
        const response = await fetch(`${API_BASE_URL}/models/available`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const models = await response.json();
        
        // 清空当前选项
        modelSelect.innerHTML = '';
        
        // 添加默认选项
        const defaultOption = document.createElement('option');
        defaultOption.value = "deepseek-api";
        defaultOption.textContent = "DeepSeek API (默认)";
        modelSelect.appendChild(defaultOption);
        
        // 添加从API获取的模型
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name || model.id;
            modelSelect.appendChild(option);
        });
        
        alert('获取可用模型成功');
    } catch (error) {
        console.error('获取可用模型失败:', error);
        alert('获取可用模型失败: ' + error.message);
    } finally {
        // 恢复按钮状态
        if (fetchModelsBtn) {
            fetchModelsBtn.disabled = false;
            fetchModelsBtn.textContent = "获取可用模型";
        }
        // 隐藏加载指示器
        hideLoading();
    }
}

// 加载参考文本文件列表
async function loadReferenceFiles() {
    try {
        const response = await fetch(`${API_BASE_URL}/reference/files`);
        
        if (response.ok) {
            const files = await response.json();
            
            // 清空选择器
            referenceSelect.innerHTML = '<option value="">-- 请选择 --</option>';
            
            // 添加文件选项
            files.forEach(file => {
                const option = document.createElement('option');
                option.value = file.id;
                option.textContent = `${file.name} (${file.language_pair})`;
                referenceSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载参考文本文件列表失败:', error);
    }
}

// 加载选中的参考文本
async function loadSelectedReference() {
    const selectedFile = referenceSelect.value;
    
    if (!selectedFile) {
        alert('请选择要加载的参考文本文件');
        return;
    }
    
    showLoading('加载参考文本中...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/references/${selectedFile}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        referenceText.value = data.content;
        
        // 标记已加载文件
        referenceFileOption.setAttribute('data-loaded', 'true');
        
        alert('参考文本加载成功!');
    } catch (error) {
        console.error('加载参考文本失败:', error);
        alert('加载参考文本失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 上传参考文本文件
async function uploadReferenceFile() {
    const fileInput = document.getElementById('reference-file');
    const sourceLang = refSourceLangSelect.value;
    const targetLang = refTargetLangSelect.value;
    
    if (!fileInput.files || fileInput.files.length === 0) {
        alert('请选择一个文件');
        return;
    }
    
    const file = fileInput.files[0];
    
    try {
        showLoading('上传参考文本...');
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('source_lang', sourceLang);
        formData.append('target_lang', targetLang);
        
        const response = await fetch(`${API_BASE_URL}/reference/file`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('参考文本上传成功');
            uploadForm.style.display = 'none';
            fileInput.value = '';
            
            // 重新加载参考文本列表
            await loadReferenceFiles();
        } else {
            alert(`上传失败: ${data.detail}`);
        }
    } catch (error) {
        alert('上传参考文本时出错，请查看控制台了解详情');
        console.error('上传参考文本失败:', error);
    } finally {
        hideLoading();
    }
}

// 辅助函数
function formatScore(score) {
    return (score * 100).toFixed(0);
}

function updateScoreCardColor(elementId, score) {
    const element = document.getElementById(elementId);
    
    if (score >= 0.8) {
        element.style.color = '#28a745'; // 绿色
    } else if (score >= 0.6) {
        element.style.color = '#17a2b8'; // 蓝色
    } else if (score >= 0.4) {
        element.style.color = '#ffc107'; // 黄色
    } else {
        element.style.color = '#dc3545'; // 红色
    }
}

function getFeedbackTitle(key) {
    const titles = {
        'bleu': 'BLEU分数',
        'terminology': '术语准确性',
        'sentence_structure': '句式转换',
        'discourse': '语篇连贯性'
    };
    
    return titles[key] || key;
}

function showLoading(message) {
    loadingMessage.textContent = message || '处理中...';
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// 事件监听器
if (initDataBtn) initDataBtn.addEventListener('click', initializeData);
if (translateBtn) translateBtn.addEventListener('click', translateText);
if (evaluateBtn) evaluateBtn.addEventListener('click', evaluateTranslation);
if (loadTerminologyBtn) loadTerminologyBtn.addEventListener('click', loadTerminology);
if (fetchModelsBtn) fetchModelsBtn.addEventListener('click', fetchAvailableModels);
if (loadReferenceBtn) loadReferenceBtn.addEventListener('click', loadSelectedReference);
if (uploadReferenceBtn) uploadReferenceBtn.addEventListener('click', () => uploadForm.style.display = 'block');
if (cancelUploadBtn) cancelUploadBtn.addEventListener('click', () => uploadForm.style.display = 'none');
if (submitReferenceFileBtn) submitReferenceFileBtn.addEventListener('click', uploadReferenceFile);
if (applyTermModeBtn) applyTermModeBtn.addEventListener('click', applyTerminologyMode);

// 添加术语事件
const addTermBtn = document.getElementById('add-term-btn');
if (addTermBtn) {
    addTermBtn.addEventListener('click', addTerminology);
}

// 应用术语评估模式
async function applyTerminologyMode() {
    const mode = document.getElementById('terminology-mode').value;
    const sourceText = document.getElementById('source-text').value.trim();
    const translatedText = document.getElementById('translated-text').value.trim();
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    
    // 验证必填项
    if (!sourceText || !translatedText) {
        alert('请确保已提供源文本和译文');
        return;
    }
    
    try {
        // 清空之前的术语匹配结果
        clearExtractedTermsResults();
        
        showLoading('应用术语评估模式...');
        
        if (mode === 'database') {
            // 使用术语库评估
            await extractTermsFromLocalTerminology(sourceText, translatedText, sourceLang, targetLang, domain);
        } else if (mode === 'ai') {
            // 使用AI提取评估
            await extractTermsWithAI(sourceText, translatedText, sourceLang, targetLang, domain);
        } else {
            alert('请选择有效的术语评估模式');
        }
    } catch (error) {
        console.error('应用术语评估模式失败:', error);
        alert('应用术语评估模式失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 使用本地术语库进行评估
async function extractTermsFromLocalTerminology(sourceText, translatedText, sourceLang, targetLang, domain) {
    try {
        // 从数据库获取术语库
        const response = await fetch(`${API_BASE_URL}/data/terminology?domain=${domain}&source_lang=${sourceLang}&target_lang=${targetLang}&simplified=true`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const terminology = await response.json();
        
        if (!terminology || Object.keys(terminology).length === 0) {
            alert('未找到匹配当前语言对和领域的术语');
            return;
        }
        
        // 评估术语翻译准确性
        const matchedTerms = {};
        const matchResults = {}; // 存储匹配结果
        
        for (const [sourceTerm, targetTerm] of Object.entries(terminology)) {
            // 使用正则表达式查找完整单词匹配
            let pattern;
            if (sourceLang === 'zh') {
                // 中文不需要词边界
                pattern = new RegExp(escapeRegExp(sourceTerm), 'g');
            } else {
                // 英文使用词边界
                pattern = new RegExp('\\b' + escapeRegExp(sourceTerm) + '\\b', 'gi');
            }
            
            if (pattern.test(sourceText)) {
                matchedTerms[sourceTerm] = targetTerm;
                
                // 检查术语是否在译文中正确翻译
                let targetPattern;
                if (targetLang === 'zh') {
                    targetPattern = new RegExp(escapeRegExp(targetTerm), 'g');
                } else {
                    targetPattern = new RegExp('\\b' + escapeRegExp(targetTerm) + '\\b', 'gi');
                }
                
                const inTranslation = targetPattern.test(translatedText);
                matchResults[sourceTerm] = {
                    targetTerm: targetTerm,
                    matched: inTranslation,
                    definition: ''
                };
            }
        }
        
        // 计算术语匹配得分
        const totalTerms = Object.keys(matchResults).length;
        let matchedCount = 0;
        
        Object.values(matchResults).forEach(result => {
            if (result.matched) {
                matchedCount++;
            }
        });
        
        const score = totalTerms > 0 ? (matchedCount / totalTerms) : 1.0;
        
        // 显示提取的术语和评估结果
        displayExtractedTermsWithResults(matchResults, score);
    } catch (error) {
        console.error('使用术语库评估失败:', error);
        alert('使用术语库评估失败: ' + error.message);
    }
}

// 使用AI提取术语
async function extractTermsWithAI(sourceText, translatedText, sourceLang, targetLang, domain) {
    try {
        const response = await fetch(`${API_BASE_URL}/evaluation/extract-terms`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_text: sourceText,
                translated_text: translatedText,
                source_language: sourceLang,
                target_language: targetLang,
                domain: domain,
                mode: 'ai_extraction'
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.extracted_terms) {
            displayExtractedTerms(result.extracted_terms);
        } else {
            alert('未能提取到术语');
        }
    } catch (error) {
        console.error('使用AI提取术语失败:', error);
        alert('使用AI提取术语失败: ' + error.message);
    }
}

// 显示提取的术语（带匹配结果）
function displayExtractedTermsWithResults(termResults, score) {
    const tableBody = document.getElementById('extracted-terms-body');
    tableBody.innerHTML = '';
    
    // 显示术语容器
    const extractedTermsContainer = document.getElementById('extracted-terms-container');
    if (extractedTermsContainer) {
        extractedTermsContainer.style.display = 'block';
    }
    
    if (!termResults || Object.keys(termResults).length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" class="text-center">未找到匹配的术语</td></tr>';
        return;
    }
    
    // 显示术语匹配得分
    const scoreElement = document.createElement('tr');
    scoreElement.innerHTML = `<td colspan="4" class="text-center font-weight-bold bg-light">
        术语匹配得分: <span style="color: ${getScoreColor(score)};">${Math.round(score * 100)}%</span>
        (${Object.values(termResults).filter(r => r.matched).length}/${Object.keys(termResults).length})
    </td>`;
    tableBody.appendChild(scoreElement);
    
    // 显示每个术语及其匹配状态
    Object.entries(termResults).forEach(([sourceTerm, result]) => {
        const row = document.createElement('tr');
        
        // 设置行样式
        if (result.matched) {
            row.classList.add('table-success');
        } else {
            row.classList.add('table-danger');
        }
        
        // 中文术语单元格
        const sourceTermCell = document.createElement('td');
        sourceTermCell.textContent = sourceTerm;
        
        // 英文术语单元格
        const targetTermCell = document.createElement('td');
        targetTermCell.textContent = result.targetTerm;
        targetTermCell.style.fontWeight = result.matched ? 'bold' : 'normal';
        
        // 匹配状态单元格
        const statusCell = document.createElement('td');
        const matchStatus = document.createElement('span');
        matchStatus.textContent = result.matched ? '✓ 已匹配' : '✗ 未匹配';
        matchStatus.style.color = result.matched ? '#28a745' : '#dc3545';
        matchStatus.style.fontWeight = 'bold';
        statusCell.appendChild(matchStatus);
        
        // 操作单元格
        const actionCell = document.createElement('td');
        const saveButton = document.createElement('button');
        saveButton.textContent = '保存术语';
        saveButton.className = 'btn btn-sm btn-primary';
        saveButton.onclick = () => saveTermToDatabase(sourceTerm, result.targetTerm);
        actionCell.appendChild(saveButton);
        
        // 添加单元格到行
        row.appendChild(sourceTermCell);
        row.appendChild(targetTermCell);
        row.appendChild(statusCell);
        row.appendChild(actionCell);
        
        // 添加行到表格
        tableBody.appendChild(row);
    });
    
    // 设置术语评估得分显示
    const terminologyScore = document.getElementById('terminology-score');
    if (terminologyScore) {
        terminologyScore.textContent = Math.round(score * 100);
        updateScoreCardColor('terminology-score', score);
    }
}

// 显示提取的术语
function displayExtractedTerms(terms) {
    const tableBody = document.getElementById('extracted-terms-body');
    tableBody.innerHTML = '';
    
    if (!terms || Object.keys(terms).length === 0) {
        tableBody.innerHTML = '<tr><td colspan="3" style="text-align: center;">未找到匹配的术语</td></tr>';
        return;
    }
    
    Object.entries(terms).forEach(([sourceTerm, targetTerm]) => {
        const row = document.createElement('tr');
        
        const sourceTermCell = document.createElement('td');
        sourceTermCell.textContent = sourceTerm;
        
        const targetTermCell = document.createElement('td');
        targetTermCell.textContent = targetTerm;
        
        const actionCell = document.createElement('td');
        const saveButton = document.createElement('button');
        saveButton.textContent = '保存此术语';
        saveButton.className = 'btn btn-sm';
        saveButton.onclick = () => saveTermToDatabase(sourceTerm, targetTerm);
        
        actionCell.appendChild(saveButton);
        
        row.appendChild(sourceTermCell);
        row.appendChild(targetTermCell);
        row.appendChild(actionCell);
        
        tableBody.appendChild(row);
    });
}

// 修改保存单个术语到术语库的函数
async function saveTermToDatabase(sourceTerm, targetTerm) {
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    
    try {
        showLoading('保存术语中...');
        
        // 修改API路径
        const response = await fetch(`${API_BASE_URL}/data/terminology`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_term: sourceTerm,
                target_term: targetTerm,
                domain: domain,
                source_lang: sourceLang,
                target_lang: targetLang
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        await response.json();
        
        // 刷新术语库显示
        await loadTerminologyFromDB(sourceLang, targetLang, domain);
    } catch (error) {
        console.error('保存术语失败:', error);
        alert('保存术语失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 获取分数对应的颜色
function getScoreColor(score) {
    if (score >= 0.8) return '#28a745'; // 绿色
    if (score >= 0.6) return '#17a2b8'; // 蓝色
    if (score >= 0.4) return '#ffc107'; // 黄色
    return '#dc3545'; // 红色
}

// 转义正则表达式中的特殊字符
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// 清除评估结果的函数
function clearEvaluationResults() {
    // 清除分数显示
    document.getElementById('overall-score').textContent = '-';
    document.getElementById('bleu-score').textContent = '-';
    document.getElementById('terminology-score').textContent = '-';
    document.getElementById('sentence-score').textContent = '-';
    document.getElementById('discourse-score').textContent = '-';
    
    // 重置分数卡颜色
    document.querySelectorAll('.score-value').forEach(el => {
        el.style.color = '#333'; // 默认颜色
    });
    
    // 清除详细反馈
    document.getElementById('detailed-feedback').innerHTML = '';
    
    // 清除改进建议
    document.getElementById('suggestions').innerHTML = '';
    
    // 清除提取的术语
    document.getElementById('extracted-terms-body').innerHTML = '<tr><td colspan="3" style="text-align: center;">评估中...</td></tr>';
}

// 添加术语到术语库
async function addTerminology() {
    const sourceTerm = document.getElementById('source-term').value.trim();
    const targetTerm = document.getElementById('target-term').value.trim();
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    
    if (!sourceTerm || !targetTerm) {
        alert('请输入中文和英文术语');
        return;
    }
    
    try {
        showLoading('添加术语中...');
        
        // 修改API路径
        const response = await fetch(`${API_BASE_URL}/data/terminology`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_term: sourceTerm,
                target_term: targetTerm,
                domain: domain,
                source_lang: sourceLang,
                target_lang: targetLang
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        await response.json();
        
        // 清空输入框
        document.getElementById('source-term').value = '';
        document.getElementById('target-term').value = '';
        
        // 刷新术语库显示
        await loadTerminologyFromDB(sourceLang, targetLang, domain);
    } catch (error) {
        console.error('添加术语失败:', error);
        alert('添加术语失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

// 保存术语库到文件
function saveTerminologyToFile(terminology) {
    const content = JSON.stringify(terminology, null, 2);
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'terminology.json';
    document.body.appendChild(a);
    a.click();
    
    // 清理
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 0);
}

// 初始化UI元素
function initializeUI() {
    // 隐藏加载指示器
    hideLoading();
    
    // 隐藏评估结果区域
    document.getElementById('evaluation-results').style.display = 'none';
    
    // 隐藏提取的术语区域
    document.getElementById('extracted-terms-container').style.display = 'none';
    
    // 隐藏术语库容器，等待加载
    document.getElementById('terminology-container').style.display = 'none';
}

// 绑定事件监听器
function bindEventListeners() {
    // 翻译和评估按钮
    document.getElementById('translate-btn').addEventListener('click', translateText);
    document.getElementById('evaluate-btn').addEventListener('click', evaluateTranslation);
    
    // 术语库管理按钮
    document.getElementById('load-terminology-btn').addEventListener('click', loadTerminology);
    document.getElementById('add-term-btn').addEventListener('click', addTerminology);
    document.getElementById('batch-add-btn').addEventListener('click', batchAddTerminology);
    document.getElementById('create-empty-file-btn').addEventListener('click', createEmptyTerminologyFile);
    
    // 模型获取按钮
    if (fetchModelsBtn) {
        fetchModelsBtn.addEventListener('click', fetchAvailableModels);
    }
    
    // 添加术语库导出按钮
    const terminologyBtnContainer = document.querySelector('.col-md-12 .float-end').parentNode;
    if (terminologyBtnContainer) {
        // 创建导出按钮
        const exportBtn = document.createElement('button');
        exportBtn.id = 'export-terminology-btn';
        exportBtn.className = 'btn btn-info';
        exportBtn.style.marginLeft = '10px';
        exportBtn.textContent = '导出术语库';
        exportBtn.addEventListener('click', exportTerminology);
        
        // 将按钮添加到加载按钮旁边
        const loadBtn = document.getElementById('load-terminology-btn');
        if (loadBtn) {
            loadBtn.insertAdjacentElement('afterend', exportBtn);
        }
    }
    
    // 初始化示例数据按钮
    document.getElementById('init-data-btn').addEventListener('click', initializeData);
    
    // 语言和领域选择变化时刷新术语库
    document.getElementById('source-lang').addEventListener('change', updateTerminologyForCurrentLanguage);
    document.getElementById('target-lang').addEventListener('change', updateTerminologyForCurrentLanguage);
    document.getElementById('domain').addEventListener('change', updateTerminologyForCurrentLanguage);
    
    // 术语评估按钮
    document.getElementById('apply-term-button').addEventListener('click', applyTerminologyMode);
    
    // 清除术语结果按钮
    const clearTermsButton = document.getElementById('clear-terms-button');
    if (clearTermsButton) {
        clearTermsButton.addEventListener('click', clearExtractedTermsResults);
    }
}

// 更新当前语言和领域的术语库
async function updateTerminologyForCurrentLanguage() {
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    
    try {
        // 刷新术语库显示
        await loadTerminologyFromDB(sourceLang, targetLang, domain);
    } catch (error) {
        console.error('更新术语库失败:', error);
    }
}

// 初始化语言和领域选择
function initializeLanguageAndDomain() {
    // 设置默认值
    document.getElementById('source-lang').value = 'en';
    document.getElementById('target-lang').value = 'zh';
    document.getElementById('domain').value = 'general';
    
    // 加载对应的术语库
    updateTerminologyForCurrentLanguage();
}

// 清除提取的术语结果
function clearExtractedTermsResults() {
    // 清空术语结果表格
    const extractedTermsBody = document.getElementById('extracted-terms-body');
    if (extractedTermsBody) {
        extractedTermsBody.innerHTML = '<tr><td colspan="4" class="text-center">翻译评估后会显示术语匹配结果</td></tr>';
    }
    
    // 隐藏术语容器
    const extractedTermsContainer = document.getElementById('extracted-terms-container');
    if (extractedTermsContainer) {
        extractedTermsContainer.style.display = 'none';
    }
    
    // 重置状态显示
    const terminologyScore = document.getElementById('terminology-score');
    if (terminologyScore) {
        terminologyScore.textContent = '';
    }
}

// 导出术语库
async function exportTerminology() {
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    
    try {
        showLoading('导出术语库...');
        
        // 从数据库获取术语库
        const response = await fetch(`${API_BASE_URL}/data/terminology?domain=${domain}&source_lang=${sourceLang}&target_lang=${targetLang}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const terminology = await response.json();
        
        if (!terminology || terminology.length === 0) {
            alert('当前没有可导出的术语');
            hideLoading();
            return;
        }
        
        // 创建简化版的术语库JSON（仅包含source_term和target_term）
        const simplifiedTerminology = {};
        terminology.forEach(term => {
            simplifiedTerminology[term.source_term] = term.target_term;
        });
        
        // 创建完整版的术语库JSON（包含所有字段）
        const fullTerminology = terminology.map(term => ({
            source_term: term.source_term,
            target_term: term.target_term,
            domain: term.domain,
            source_language: term.source_language,
            target_language: term.target_language,
            definition: term.definition || ''
        }));
        
        // 询问用户想要导出的格式
        const exportFormat = confirm('选择导出格式：\n确定 - 导出简化格式 {源术语: 目标术语}\n取消 - 导出完整格式');
        
        // 根据用户选择的格式导出
        const dataToExport = exportFormat ? simplifiedTerminology : fullTerminology;
        
        // 创建Blob并触发下载
        const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        a.href = url;
        a.download = `terminology_${sourceLang}_${targetLang}_${domain}_${timestamp}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        hideLoading();
    } catch (error) {
        console.error('导出术语库失败:', error);
        alert('导出术语库失败: ' + error.message);
        hideLoading();
    }
}

// 创建空术语库文件
function createEmptyTerminologyFile() {
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    
    try {
        // 创建一个空的术语库对象
        const emptyTerminology = {};
        
        // 询问用户选择保存格式
        const saveFormat = confirm('选择文件格式：\n确定 - 保存为简化格式 {}\n取消 - 保存为完整格式 []');
        
        let dataToExport;
        if (saveFormat) {
            // 简化格式 - 空对象
            dataToExport = emptyTerminology;
        } else {
            // 完整格式 - 空数组
            dataToExport = [];
        }
        
        // 创建文件名
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const fileName = `terminology_${sourceLang}_${targetLang}_${domain}_${timestamp}.json`;
        
        // 创建Blob并触发下载
        const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        alert(`已创建空术语库文件: ${fileName}`);
    } catch (error) {
        console.error('创建空术语库文件失败:', error);
        alert('创建空术语库文件失败: ' + error.message);
    }
}

// 批量添加术语
async function batchAddTerminology() {
    console.log('批量添加术语函数被触发');
    alert('批量添加术语函数被触发'); // 添加一个可见的提示
    
    const batchTerms = document.getElementById('batch-terms').value.trim();
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    
    console.log('当前输入:', { 
        batchTerms: batchTerms.length > 100 ? batchTerms.substring(0, 100) + '...' : batchTerms,
        sourceLang, 
        targetLang, 
        domain 
    });
    
    if (!batchTerms) {
        alert('请输入术语对');
        return;
    }
    
    // 解析术语对
    const lines = batchTerms.split('\n');
    const entries = [];
    const errors = [];
    
    lines.forEach((line, index) => {
        if (!line.trim()) return; // 跳过空行
        
        // 拆分每行的中文和英文，以第一个空格作为分隔
        const parts = line.trim().split(/\s+/);
        
        if (parts.length < 2) {
            errors.push(`第 ${index + 1} 行格式错误："${line}"`);
            return;
        }
        
        // 第一个部分作为中文，其余所有部分作为英文（合并多个空格后的内容）
        const sourceTerm = parts[0];
        const targetTerm = parts.slice(1).join(' ');
        
        if (!sourceTerm || !targetTerm) {
            errors.push(`第 ${index + 1} 行中文或英文为空："${line}"`);
            return;
        }
        
        entries.push({
            source_term: sourceTerm,
            target_term: targetTerm
        });
    });
    
    console.log('解析结果:', { 
        entries: entries.length, 
        errors: errors.length 
    });
    
    // 如果有格式错误，显示错误信息
    if (errors.length > 0) {
        alert(`发现 ${errors.length} 个格式错误:\n${errors.join('\n')}\n\n请修正后重试。`);
        return;
    }
    
    if (entries.length === 0) {
        alert('没有找到有效的术语对');
        return;
    }
    
    try {
        showLoading(`正在批量添加 ${entries.length} 个术语...`);
        
        // 构建请求数据
        const requestData = {
            entries: entries,
            domain: domain,
            source_lang: sourceLang,
            target_lang: targetLang
        };
        
        // 使用XMLHttpRequest替代fetch
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${API_BASE_URL}/terminology/batch`, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            
            xhr.onload = async function() {
                if (xhr.status >= 200 && xhr.status < 300) {
                    console.log('API调用成功，状态码:', xhr.status);
                    try {
                        const result = JSON.parse(xhr.responseText);
                        console.log('API响应结果:', result);
                        
                        // 清空输入框
                        document.getElementById('batch-terms').value = '';
                        
                        // 刷新术语库显示
                        await loadTerminologyFromDB(sourceLang, targetLang, domain);
                        
                        alert(result.message || '批量添加成功!');
                        resolve(result);
                    } catch (e) {
                        console.error('解析响应JSON失败:', e);
                        alert('解析响应数据失败: ' + e.message);
                        reject(e);
                    }
                } else {
                    console.error('API调用失败，状态码:', xhr.status, '响应:', xhr.responseText);
                    try {
                        const errorData = JSON.parse(xhr.responseText);
                        alert('批量添加术语失败: ' + (errorData.detail || '未知错误'));
                        reject(new Error(errorData.detail || '未知错误'));
                    } catch (e) {
                        alert('批量添加术语失败: HTTP错误 ' + xhr.status);
                        reject(new Error('HTTP错误 ' + xhr.status));
                    }
                }
                hideLoading();
            };
            
            xhr.onerror = function() {
                console.error('网络请求失败');
                alert('网络请求失败，请检查网络连接');
                hideLoading();
                reject(new Error('网络请求失败'));
            };
            
            // 发送请求
            console.log('准备发送API请求，数据:', requestData);
            xhr.send(JSON.stringify(requestData));
            console.log('API请求已发送');
        });
    } catch (error) {
        console.error('批量添加术语失败:', error);
        alert('批量添加术语失败: ' + error.message);
        hideLoading();
    }
    
    console.log('批量添加术语函数执行完成');
    return;
} 