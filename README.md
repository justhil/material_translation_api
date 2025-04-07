# 材料领域翻译质量评估系统API

本项目是一个基于Python和FastAPI开发的材料领域翻译质量评估系统后端API，实现了以下核心功能：

1. 从本地文件加载术语库和翻译范本
2. 接入大语言模型实现文本翻译功能
3. 从词汇、句式和语篇三个层面评估翻译质量
4. 提供改进建议

## 技术栈

- **后端框架**: FastAPI
- **语言**: Python 3.8+
- **依赖管理**: pip/requirements.txt
- **翻译实现**: 接入大语言模型API
- **评估指标**: BLEU分数、术语准确性、句式转换、语篇连贯性

## 项目结构

```
material_translation_api/
│
├── app/                      # 主应用目录
│   ├── api/                  # API路由
│   │   ├── endpoints/        # API端点
│   │   │   ├── translation.py  # 翻译端点
│   │   │   ├── evaluation.py   # 评估端点
│   │   │   ├── data.py         # 数据访问端点
│   │   │   └── health.py       # 健康检查端点
│   │   └── api.py            # API路由汇总
│   │
│   ├── core/                 # 核心配置
│   │   └── config.py         # 配置文件
│   │
│   ├── data/                 # 数据文件
│   │   ├── terminology/      # 术语库文件夹
│   │   └── examples/         # 翻译范本文件夹
│   │
│   ├── models/               # 数据模型
│   │   └── schemas.py        # 模型定义
│   │
│   ├── services/             # 业务服务
│   │   ├── data_service.py   # 数据服务
│   │   ├── llm_service.py    # 语言模型服务
│   │   └── evaluation_service.py # 评估服务
│   │
│   ├── utils/                # 工具函数
│   │
│   └── main.py               # 应用入口
│
├── requirements.txt          # 依赖列表
├── .env.sample              # 环境变量示例文件
├── frontend/                # 简单前端示例
│   ├── index.html           # 前端页面
│   ├── styles.css           # 样式文件
│   └── script.js            # 脚本文件
└── README.md                 # 项目说明
```

## 安装与运行

### 环境需求

- Python 3.8+
- pip

### 安装步骤

1. 克隆仓库

```bash
git clone <repository_url>
cd material_translation_api
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量（可选）

```bash
cp .env.sample .env
# 编辑 .env 文件，设置你的 API 密钥和其他配置
```

4. 运行应用

```bash
uvicorn app.main:app --reload
```

应用将在 http://localhost:8000 启动，API文档可访问 http://localhost:8000/api/docs

## API文档

### 1. 翻译API

#### 翻译文本

- **URL**: `/api/translation/translate`
- **方法**: POST
- **请求体**:
  ```json
  {
    "source_text": "本研究探讨了碳纳米管的机械性能。",
    "source_language": "zh",
    "target_language": "en",
    "domain": "materials_science",
    "reference_texts": ["The mechanical properties of carbon nanotubes were investigated in this study."]
  }
  ```
- **响应**:
  ```json
  {
    "source_text": "本研究探讨了碳纳米管的机械性能。",
    "translated_text": "The mechanical properties of carbon nanotubes were investigated in this study.",
    "model_used": "deepseek-api"
  }
  ```

### 2. 评估API

#### 评估翻译质量

- **URL**: `/api/evaluation/evaluate`
- **方法**: POST
- **请求体**:
  ```json
  {
    "source_text": "本研究探讨了碳纳米管的机械性能。",
    "translated_text": "This study investigated the mechanical properties of carbon nanotubes.",
    "reference_texts": ["The mechanical properties of carbon nanotubes were investigated in this study."],
    "source_language": "zh",
    "target_language": "en",
    "domain": "materials_science"
  }
  ```
- **响应**: 包含综合评分、BLEU分数、术语准确性、句式转换、语篇连贯性等评估结果

### 3. 数据API

#### 获取术语库

- **URL**: `/api/data/terminology`
- **方法**: GET
- **参数**:
  - `domain`: 领域名称，默认为materials_science
  - `source_lang`: 源语言代码，默认为zh
  - `target_lang`: 目标语言代码，默认为en

#### 获取翻译示例

- **URL**: `/api/data/examples`
- **方法**: GET
- **参数**:
  - `domain`: 领域名称，默认为materials_science
  - `text_type`: 文本类型，如academic, technical等（可选）
  - `source_lang`: 源语言代码，默认为zh
  - `target_lang`: 目标语言代码，默认为en

#### 初始化示例数据

- **URL**: `/api/data/init-sample-data`
- **方法**: POST

### 4. 系统API

#### 健康检查

- **URL**: `/api/system/health`
- **方法**: GET
- **响应**:
  ```json
  {
    "status": "healthy",
    "version": "0.1.0"
  }
  ```

## 数据格式

### 术语库JSON格式

```json
[
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
  }
]
```

### 翻译范本JSON格式

```json
[
  {
    "example_id": "1",
    "source_text": "本研究探讨了碳纳米管的机械性能。",
    "target_text": "The mechanical properties of carbon nanotubes were investigated in this study.",
    "domain": "materials_science",
    "text_type": "academic",
    "notes": "注意英文中使用了被动语态"
  }
]
```

## 使用说明

1. 首先初始化示例数据（调用`/api/data/init-sample-data`）
2. 然后可以使用翻译API进行文本翻译
3. 最后使用评估API对翻译结果进行质量评估

## 简单前端示例

### 前端文件结构

在项目根目录下创建 `frontend` 文件夹，包含以下文件：
- `index.html`: 前端页面
- `styles.css`: 样式文件
- `script.js`: JavaScript脚本

### HTML (index.html)

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>材料领域翻译质量评估系统</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>材料领域翻译质量评估系统</h1>
            <button id="init-data" class="btn">初始化示例数据</button>
            <div id="system-status">
                <span>系统状态: </span>
                <span id="status-value">检查中...</span>
            </div>
        </header>

        <div class="main-content">
            <div class="section">
                <h2>翻译</h2>
                <div class="form-group">
                    <label for="source-text">输入源文本:</label>
                    <textarea id="source-text" placeholder="请输入要翻译的材料科学文本..."></textarea>
                </div>
                <div class="form-row">
                    <div class="form-group half">
                        <label for="source-lang">源语言:</label>
                        <select id="source-lang">
                            <option value="zh">中文 (zh)</option>
                            <option value="en">英文 (en)</option>
                        </select>
                    </div>
                    <div class="form-group half">
                        <label for="target-lang">目标语言:</label>
                        <select id="target-lang">
                            <option value="en">英文 (en)</option>
                            <option value="zh">中文 (zh)</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label for="domain">领域:</label>
                    <select id="domain">
                        <option value="materials_science">材料科学</option>
                    </select>
                </div>
                <div class="form-actions">
                    <button id="translate-btn" class="btn primary">翻译</button>
                </div>
                <div class="form-group">
                    <label for="translated-text">翻译结果:</label>
                    <textarea id="translated-text" readonly placeholder="翻译结果将显示在这里..."></textarea>
                </div>
            </div>

            <div class="section">
                <h2>评估</h2>
                <div class="form-group">
                    <label for="reference-text">参考译文:</label>
                    <textarea id="reference-text" placeholder="请输入参考译文，用于评估..."></textarea>
                </div>
                <div class="form-actions">
                    <button id="evaluate-btn" class="btn primary">评估</button>
                </div>
                <div class="evaluation-results">
                    <h3>评估结果</h3>
                    <div id="evaluation-data">
                        <div class="score-card">
                            <div class="score-title">综合评分</div>
                            <div id="overall-score" class="score">--</div>
                        </div>
                        <div class="score-details">
                            <div class="score-card">
                                <div class="score-title">BLEU分数</div>
                                <div id="bleu-score" class="score">--</div>
                            </div>
                            <div class="score-card">
                                <div class="score-title">术语准确性</div>
                                <div id="terminology-score" class="score">--</div>
                            </div>
                            <div class="score-card">
                                <div class="score-title">句式转换</div>
                                <div id="sentence-score" class="score">--</div>
                            </div>
                            <div class="score-card">
                                <div class="score-title">语篇连贯性</div>
                                <div id="discourse-score" class="score">--</div>
                            </div>
                        </div>
                    </div>
                    <div id="feedback-section">
                        <h4>详细反馈</h4>
                        <div id="detailed-feedback" class="feedback-box"></div>
                        <h4>改进建议</h4>
                        <ul id="suggestions" class="suggestions-list"></ul>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>术语库</h2>
                <div class="form-actions">
                    <button id="load-terminology-btn" class="btn">加载术语库</button>
                </div>
                <div class="terminology-container">
                    <table id="terminology-table">
                        <thead>
                            <tr>
                                <th>源语言术语</th>
                                <th>目标语言术语</th>
                                <th>定义</th>
                            </tr>
                        </thead>
                        <tbody id="terminology-body">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <footer>
            <p>© 2023 材料领域翻译质量评估系统 | <a href="/api/docs" target="_blank">API文档</a></p>
        </footer>
    </div>

    <div id="loading-overlay">
        <div class="spinner"></div>
        <div id="loading-message">处理中...</div>
    </div>

    <script src="script.js"></script>
</body>
</html>
```

### CSS (styles.css)

```css
:root {
    --primary-color: #4a6fa5;
    --secondary-color: #6b8caf;
    --accent-color: #ff6b6b;
    --bg-color: #f8f9fa;
    --text-color: #333;
    --border-color: #dee2e6;
    --success-color: #28a745;
    --warning-color: #ffc107;
    --error-color: #dc3545;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
    flex-wrap: wrap;
}

h1 {
    color: var(--primary-color);
    font-size: 1.8rem;
}

h2 {
    color: var(--secondary-color);
    margin-bottom: 15px;
    font-size: 1.5rem;
}

h3 {
    color: var(--secondary-color);
    margin: 20px 0 10px;
    font-size: 1.3rem;
}

h4 {
    color: var(--text-color);
    margin: 15px 0 10px;
    font-size: 1.1rem;
}

.section {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    padding: 20px;
    margin-bottom: 30px;
}

.form-group {
    margin-bottom: 15px;
}

.form-row {
    display: flex;
    gap: 20px;
    margin-bottom: 15px;
}

.half {
    width: 50%;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
}

textarea, select {
    width: 100%;
    padding: 10px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-family: inherit;
    font-size: 14px;
}

textarea {
    min-height: 100px;
    resize: vertical;
}

.form-actions {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 15px;
}

.btn {
    background-color: var(--secondary-color);
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: background-color 0.2s;
}

.btn.primary {
    background-color: var(--primary-color);
}

.btn:hover {
    background-color: var(--primary-color);
}

.btn.primary:hover {
    opacity: 0.9;
}

#system-status {
    background-color: #f8f9fa;
    padding: 8px 15px;
    border-radius: 4px;
    font-size: 14px;
}

.evaluation-results {
    margin-top: 20px;
}

.score-details {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 10px;
}

.score-card {
    background-color: white;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 15px;
    text-align: center;
    flex: 1;
    min-width: 120px;
}

.score-title {
    font-weight: 500;
    margin-bottom: 10px;
}

.score {
    font-size: 24px;
    font-weight: bold;
    color: var(--primary-color);
}

.feedback-box {
    background-color: #f8f9fa;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 15px;
    margin-top: 10px;
    white-space: pre-line;
}

.suggestions-list {
    margin-left: 20px;
    margin-top: 10px;
}

.suggestions-list li {
    margin-bottom: 5px;
}

.terminology-container {
    margin-top: 20px;
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 12px 15px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th {
    background-color: #f8f9fa;
    font-weight: 600;
}

tbody tr:hover {
    background-color: #f8f9fa;
}

footer {
    margin-top: 40px;
    text-align: center;
    padding: 20px;
    border-top: 1px solid var(--border-color);
    color: #6c757d;
}

#loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(255, 255, 255, 0.8);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    display: none;
}

.spinner {
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-radius: 50%;
    border-top: 4px solid var(--primary-color);
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

#loading-message {
    margin-top: 15px;
    font-weight: 500;
}
```

### JavaScript (script.js)

```javascript
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

// 页面加载时检查API状态
document.addEventListener('DOMContentLoaded', checkApiStatus);

// 按钮事件监听
initDataBtn.addEventListener('click', initializeData);
translateBtn.addEventListener('click', translateText);
evaluateBtn.addEventListener('click', evaluateTranslation);
loadTerminologyBtn.addEventListener('click', loadTerminology);

// 检查API健康状态
async function checkApiStatus() {
    try {
        showLoading('检查API状态...');
        const response = await fetch(`${API_BASE_URL}/system/health`);
        const data = await response.json();
        
        if (response.ok) {
            statusValue.textContent = `正常 (版本: ${data.version})`;
            statusValue.style.color = '#28a745';
        } else {
            statusValue.textContent = '异常';
            statusValue.style.color = '#dc3545';
        }
    } catch (error) {
        statusValue.textContent = '无法连接';
        statusValue.style.color = '#dc3545';
        console.error('API状态检查失败:', error);
    } finally {
        hideLoading();
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
    const translatedTextElem = document.getElementById('translated-text');
    
    if (!sourceText) {
        alert('请输入源文本');
        return;
    }
    
    try {
        showLoading('翻译中...');
        const response = await fetch(`${API_BASE_URL}/translation/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_text: sourceText,
                source_language: sourceLang,
                target_language: targetLang,
                domain: domain
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            translatedTextElem.value = data.translated_text;
        } else {
            alert(`翻译失败: ${data.detail}`);
        }
    } catch (error) {
        alert('翻译过程中出错，请查看控制台了解详情');
        console.error('翻译失败:', error);
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
    
    if (!sourceText || !translatedText || !referenceText) {
        alert('请确保源文本、翻译结果和参考译文均已填写');
        return;
    }
    
    try {
        showLoading('评估中...');
        const response = await fetch(`${API_BASE_URL}/evaluation/evaluate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_text: sourceText,
                translated_text: translatedText,
                reference_texts: [referenceText],
                source_language: sourceLang,
                target_language: targetLang,
                domain: domain
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayEvaluationResults(data);
        } else {
            alert(`评估失败: ${data.detail}`);
        }
    } catch (error) {
        alert('评估过程中出错，请查看控制台了解详情');
        console.error('评估失败:', error);
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

// 加载术语库
async function loadTerminology() {
    const sourceLang = document.getElementById('source-lang').value;
    const targetLang = document.getElementById('target-lang').value;
    const domain = document.getElementById('domain').value;
    
    try {
        showLoading('加载术语库...');
        const response = await fetch(`${API_BASE_URL}/data/terminology?domain=${domain}&source_lang=${sourceLang}&target_lang=${targetLang}`);
        
        const data = await response.json();
        
        if (response.ok) {
            displayTerminology(data);
        } else {
            alert(`加载术语库失败: ${data.detail}`);
        }
    } catch (error) {
        alert('加载术语库时出错，请查看控制台了解详情');
        console.error('加载术语库失败:', error);
    } finally {
        hideLoading();
    }
}

// 显示术语库
function displayTerminology(data) {
    const tableBody = document.getElementById('terminology-body');
    tableBody.innerHTML = '';
    
    if (data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="3" style="text-align: center;">未找到术语数据，请先初始化示例数据</td></tr>';
        return;
    }
    
    data.forEach(term => {
        const row = document.createElement('tr');
        
        const sourceTerm = document.createElement('td');
        sourceTerm.textContent = term.source_term;
        
        const targetTerm = document.createElement('td');
        targetTerm.textContent = term.target_term;
        
        const definition = document.createElement('td');
        definition.textContent = term.definition;
        
        row.appendChild(sourceTerm);
        row.appendChild(targetTerm);
        row.appendChild(definition);
        
        tableBody.appendChild(row);
    });
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
```

## 前端使用说明

1. 创建前端文件
```bash
mkdir -p frontend
touch frontend/index.html
touch frontend/styles.css
touch frontend/script.js
```

2. 将上面的HTML、CSS和JavaScript代码分别复制到对应文件中

3. 启动后端API服务
```bash
uvicorn app.main:app --reload
```

4. 在浏览器中直接打开`frontend/index.html`文件，或者通过简单的HTTP服务器提供前端文件

5. 使用步骤：
   - 点击"初始化示例数据"按钮创建示例数据
   - 在翻译区域输入要翻译的文本，选择语言方向，点击"翻译"
   - 在参考译文输入框中输入参考译文
   - 点击"评估"按钮评估翻译质量
   - 查看术语库

## 配置

主要配置项在`app/core/config.py`中定义，包括：

- 应用名称和版本
- 数据文件路径
- 语言模型API设置
- 评估权重设置
- CORS设置

可以通过环境变量或`.env`文件修改这些配置。

## 扩展和自定义

- 在`app/data/terminology/`中添加新的术语库文件
- 在`app/data/examples/`中添加新的翻译范本文件
- 修改`app/services/evaluation_service.py`中的评估算法
- 在`app/services/llm_service.py`中更改大语言模型API接口

## 注意事项

- 由于使用本地文件存储数据，请确保数据文件夹有适当的读写权限
- 在生产环境中，建议配置适当的API密钥和访问控制
- 对于大规模部署，可考虑将本地文件存储迁移到数据库 
