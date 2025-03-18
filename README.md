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
- **翻译实现**: 接入大语言模型API（如DeepSeek）
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

### 前端文件结构

在项目根目录下创建 `frontend` 文件夹，包含以下文件：
- `index.html`: 前端页面
- `styles.css`: 样式文件
- `script.js`: JavaScript脚本

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
