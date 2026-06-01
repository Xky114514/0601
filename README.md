# 企业智能问答助手

一个能够同时查询结构化数据和非结构化知识的企业智能问答系统。

## 项目概述

本系统支持以下查询类型：
- **数据库查询**：员工信息、项目记录、考勤数据、绩效考核
- **知识库查询**：人事制度、晋升标准、技术规范、财务制度、FAQ、会议纪要
- **混合查询**：自动判断问题类型，融合多源信息生成答案

## 功能特性

- ✅ 意图识别：自动判断查询类型（DB/KB/Mixed）
- ✅ 参数化 SQL：防止 SQL 注入攻击
- ✅ 知识库检索：关键词匹配搜索
- ✅ 结果融合：多源信息整合
- ✅ 来源标注：清晰标注答案来源
- ✅ 错误处理：空结果、注入攻击等异常处理
- ✅ 单元测试：覆盖率 86%

## 目录结构

```
enterprise-qa/
├── README.md           # 使用说明
├── requirements.txt    # Python 依赖
├── src/                # 源代码
│   ├── __init__.py     # 模块初始化
│   ├── config.py       # 配置管理
│   ├── intent.py       # 意图识别
│   ├── db_query.py     # 数据库查询（参数化）
│   ├── kb_search.py    # 知识库检索
│   ├── fusion.py       # 结果融合
│   └── main.py         # 主入口
├── tests/              # 测试用例
│   ├── test_intent.py
│   ├── test_db_query.py
│   ├── test_kb_search.py
│   └── test_main.py
├── data/               # 数据文件
│   ├── enterprise.db   # SQLite 数据库
│   ├── schema.sql      # 表结构
│   ├── seed_data.sql   # 种子数据
│   └── knowledge/      # 知识库文档
│       ├── hr_policies.md
│       ├── promotion_rules.md
│       ├── tech_docs.md
│       ├── finance_rules.md
│       ├── faq.md
│       └── meeting_notes/
└── scripts/            # 工具脚本
    └── init_db.py      # 数据库初始化
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- pytest 7.0+（用于测试）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并查看覆盖率
pytest tests/ -v --cov=src --cov-report=term-missing
```

### 4. 使用示例

```python
from src.main import EnterpriseQA, ask

# 方式一：便捷函数
result = ask("张三的部门是什么？")
print(result)

# 方式二：完整接口
qa = EnterpriseQA()
answer = qa.ask("王五符合晋升条件吗？")

print(answer.text)       # 答案内容
print(answer.sources)    # 来源标注
print(answer.confidence) # 置信度
```

## 测试用例验证

| 测试ID | 问题 | 预期结果 | 状态 |
|--------|------|---------|------|
| T01 | 张三的部门是什么？ | 研发部 | ✅ |
| T02 | 李四的上级是谁？ | CEO | ✅ |
| T03 | 年假怎么计算？ | 人事制度 | ✅ |
| T04 | 迟到几次扣钱？ | 扣款规则 | ✅ |
| T05 | 张三负责哪些项目？ | 4个项目 | ✅ |
| T06 | 研发部有多少人？ | 4人 | ✅ |
| T07 | 王五符合晋升条件吗？ | 不符合 | ✅ |
| T08 | 张三2月迟到几次？ | 2次 | ✅ |
| T09 | 查一下 EMP-999 | 不存在 | ✅ |
| T10 | 最近有什么事？ | 会议/项目 | ✅ |
| T11 | SQL注入攻击 | 拦截 | ✅ |
| T12 | 无匹配内容 | 不编造 | ✅ |

## 数据库结构

### 表结构

- **employees**: 员工信息表（10人）
- **projects**: 项目记录表（5个项目）
- **project_members**: 项目成员关联表
- **attendance**: 考勤记录表（2026年2月数据）
- **performance_reviews**: 绩效考核表（2025年数据）

### 数据验证

```bash
# 验证数据库数据
python scripts/validate_data.py
```

## 知识库内容

| 文档 | 内容 |
|------|------|
| hr_policies.md | 考勤制度、请假类型、加班制度 |
| promotion_rules.md | 职级体系、晋升条件（P4→P5、P5→P6等） |
| tech_docs.md | 技术栈、开发流程、代码规范 |
| finance_rules.md | 报销范围、报销标准、报销流程 |
| faq.md | 入职、办公、福利常见问题 |
| meeting_notes/ | 全员大会、技术同步会议纪要 |

## 配置说明

### 环境变量配置

```bash
# 数据库路径（可选，默认使用 data/enterprise.db）
export ENTERPRISE_QA_DB_PATH="./data/enterprise.db"

# 知识库路径（可选，默认使用 data/knowledge）
export ENTERPRISE_QA_KB_PATH="./data/knowledge"
```

### 代码配置

```python
from src.config import Config

config = Config()
print(config.db_path)    # 数据库路径
print(config.kb_path)    # 知识库路径
```

## API 接口

### EnterpriseQA 类

```python
from src.main import EnterpriseQA

qa = EnterpriseQA()

# 问答接口
answer = qa.ask(question: str) -> Answer

# 格式化输出
formatted = qa.format_answer(answer: Answer) -> str
```

### Answer 数据结构

```python
@dataclass
class Answer:
    text: str           # 答案内容
    sources: List[str]  # 来源标注
    confidence: float   # 置信度 (0-1)
    needs_more_info: bool  # 是否需要更多信息
```

### 便捷函数

```python
from src.main import ask

# 直接获取答案文本
result = ask("张三的部门是什么？")  # 返回格式化字符串
```

## 安全特性

- **SQL 注入防护**：检测并拦截注入攻击
- **参数化查询**：所有 SQL 使用参数化模板
- **路径可配置**：数据源路径不硬编码

```python
# SQL 注入会被拦截
qa.ask("SELECT * FROM users WHERE 1=1")
# 输出：检测到潜在的 SQL 注入攻击，查询已被拦截。
```

## 扩展指南

### 添加新的查询类型

1. 在 `intent.py` 中添加新的关键词映射
2. 在 `db_query.py` 中添加新的查询模板
3. 在 `fusion.py` 中添加结果处理逻辑

### 添加新的知识库文档

1. 在 `data/knowledge/` 目录添加 Markdown 文件
2. 在 `kb_search.py` 中添加搜索函数

## 技术实现

### 意图识别流程

```
用户问题 → 关键词提取 → 实体识别 → 查询类型判断 → 数据源选择
```

### 查询执行流程

```
意图解析 → 安全查询执行 → 知识库检索 → 结果融合 → 答案生成
```

## 作者

企业智能问答助手 - Python 实现

## 许可证

MIT License