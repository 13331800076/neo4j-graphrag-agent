# 从企业文档到知识图谱：构建一个 Neo4j GraphRAG Agent 的完整实战

> 英文版：[Building a Neo4j GraphRAG Agent from Enterprise Documents](https://dev.to/...) (待发布)

## 引言

在做 AI 应用工程师的过程中，我发现一个普遍痛点：**普通 RAG 在处理结构化企业知识时总是力不从心**。比如问"采购模块有哪些 API？"，向量检索只能返回包含"采购"和"API"的段落；问"采购订单从创建到入库需要哪些审批步骤？"，语义搜索更是容易漏掉中间环节。

这个问题的本质是：**非结构化文档中蕴含的关系和流程，无法通过纯语义相似度捕捉**。

本文将完整介绍我构建的 `neo4j-graphrag-agent` 项目——一个从零开始、不依赖 LLM API、能证明"知识图谱建模 + GraphRAG + Agent 工程化"能力的作品集项目。

---

## 一、为什么普通 RAG 不够？

### 普通 RAG 的链路

```
文档 → 切片 → Embedding → 向量检索 → LLM 生成答案
```

这个链路对**事实性问答**（如"系统如何处理库存不足？"）效果不错，但对**结构化推理**问题非常脆弱：

| 问题类型 | 普通 RAG 表现 | 问题根源 |
|---|---|---|
| "采购模块有哪些 API？" | 可能只返回文档片段，API 列表不完整 | 语义相似度不保证覆盖全部 API |
| "采购订单从创建到入库经过哪些步骤？" | 可能漏掉中间审批步骤 | 切片边界切断流程链条 |
| "谁可以审批采购订单？" | 只找到包含"approve"的段落 | 无法推理 Role → Permission → Workflow 链条 |
| "附件上传失败怎么解决？" | 可能返回 FAQ 片段 | 无法结构化错误码 → 原因 → 解决方案 |

### GraphRAG 的解决思路

```
企业文档 → Ontology 建模 → 知识图谱 → 图查询推理 → 向量检索 → 证据融合 → 答案生成
```

**核心区别**：把文档中的实体和关系显式建模到图谱中，让查询可以直接遍历关系（`HAS_STEP` → `NEXT_STEP` → `REQUIRES_PERMISSION`），而不是依赖语义近似。

---

## 二、项目架构

```
                    ┌─────────────────────┐
                    │     User Query       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Agent / Router     │
                    │  (规则意图分类)        │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
┌─────────▼─────────┐ ┌────────▼────────┐ ┌─────────▼─────────┐
│  Template-based    │ │  FAISS Vector   │ │  Hybrid (Graph +   │
│    Text2Cypher     │ │    Search       │ │    Vector)          │
└─────────┬─────────┘ └────────┬────────┘ └─────────┬─────────┘
          │                    │                    │
┌─────────▼─────────┐ ┌──────▼────────┐          │
│    Neo4j Graph     │ │  Text Evidence │          │
│ (Entity/Relation) │ │  (Chunk/Sim)   │          │
└─────────┬─────────┘ └──────┬────────┘          │
          │                    │                    │
          └──────────┬─────────┘                    │
                     │                              │
          ┌──────────▼──────────┐                   │
          │   Evidence Fusion    │◄─────────────────┘
          │   (规则拼接证据)      │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Answer Generation   │
          │  (模板 + 证据引用)    │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │  Return with Source  │
          └─────────────────────┘
```

---

## 三、Ontology 设计：企业 ERP 知识图谱

为什么 Ontology 设计是 GraphRAG 的核心？因为**实体类型和关系类型决定了你能回答什么类型的问题**。

本项目针对 ERP 产品知识库设计了以下 Ontology：

### 实体类型 (10种)

| 类型 | 示例 | 来源 |
|---|---|---|
| Module | Procurement, Inventory | 文档标题 |
| BusinessObject | PurchaseOrder, InventoryItem | 文档中显式列出 |
| API | createPurchaseOrder, queryInventory | 代码块/API 段落 |
| Role | Procurement Clerk, Manager | 角色列表 |
| Permission | PURCHASE_CREATE, APPROVE | 权限说明 |
| Workflow | Procurement Workflow | 流程标题 |
| Step | Submit Request, Manager Approval | 流程步骤 |
| ErrorCode | ATT_001 | 错误码列表 |
| Document | procurement.md | 原始文档 |
| Chunk | procurement_chunk_0 | 切片 |

### 关系类型 (9种)

| 关系 | 示例 | 用途 |
|---|---|---|
| BELONGS_TO | API → Module | 查询模块下的 API |
| USES_API | BusinessObject → API | 查询业务对象使用的 API |
| REQUIRES_PERMISSION | Role → Permission | 查询角色所需权限 |
| HAS_STEP | Workflow → Step | 查询流程步骤 |
| NEXT_STEP | Step → Step | 遍历流程顺序 |
| RELATED_TO | Module → Module | 跨模块关联 |
| DEFINED_IN | API → Document | 溯源 |
| CAUSES | ErrorCode → Cause | 错误原因 |
| SOLVED_BY | ErrorCode → Solution | 解决方案 |

---

## 四、技术实现要点

### 1. 规则抽取：不用 LLM，也能抽取结构化知识

第一版刻意不用 LLM 抽取，原因：
- **可复现**：同样的文档，永远产出同样的图谱
- **零成本**：不需要 API Key，本地直接跑
- **可测试**：每个规则可以写单元测试验证

抽取规则示例：
```python
# 从 H1 提取 Module
re.search(r"^#\s+(.+)\s+Module", text, re.MULTILINE | re.IGNORECASE)

# 从列表提取 API
re.match(r"-\s+`?([^`]+)`?\s*-\s*(.+)", line)

# 从列表提取 Role-Permission
re.match(r"-\s+(.+?)\s*-\s*Requires?\s+(.+)\s+permission", line, re.IGNORECASE)

# 从有序列表提取 Workflow Step
re.match(r"\d+\.\s+(.+)", line)
```

### 2. 模板 Text2Cypher：零 LLM 成本的结构化查询

不用 LLM 生成 Cypher，而是**先分类意图，再匹配模板**：

```python
class QuestionIntent(Enum):
    API_BY_MODULE = "api_by_module"
    ROLES_BY_PERMISSION = "roles_by_permission"
    WORKFLOW_STEPS = "workflow_steps"
    ERROR_SOLUTION = "error_solution"
    BUSINESS_OBJECT_RELATION = "business_object_relation"
```

每个意图对应一个 Cypher 模板：

```cypher
// API_BY_MODULE
MATCH (m:Entity {type: 'Module', name: 'Procurement'})
<-[:RELATION {type: 'BELONGS_TO'}]-(api:Entity {type: 'API'})
RETURN api.name AS api_name, api.properties.description AS description

// WORKFLOW_STEPS
MATCH (wf:Entity {type: 'Workflow', name: 'Procurement Workflow'})
-[:RELATION {type: 'HAS_STEP'}]->(s:Entity {type: 'Step'})
OPTIONAL MATCH (s)-[:RELATION {type: 'NEXT_STEP'}]->(next:Entity {type: 'Step'})
RETURN s.name AS step_name, s.properties.order AS step_order, next.name AS next_step
ORDER BY s.properties.order
```

**优势**：速度快、零成本、100%可预测、安全（只读模板）。

### 3. Cypher 安全校验：防止注入和误操作

```python
FORBIDDEN_KEYWORDS = {
    "CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE",
    "DROP", "CALL", "LOAD", "CSV", "apoc", "gds", "dbms",
}

def validate_read_only(cypher: str) -> bool:
    upper = cypher.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in upper:
            raise CypherSafetyError(f"Forbidden keyword: {keyword}")
    return True
```

### 4. 向量检索：FAISS + sentence-transformers

使用 `all-MiniLM-L6-v2` 模型（384 维），本地运行，不需要 API Key：

```python
class VectorStore:
    def __init__(self, embedder: Embedder, dimension: int = 384):
        self.index = faiss.IndexFlatIP(dimension)
        # ...
```

**为什么用 FAISS 而不是 Milvus/Pinecone？** 第一版要求"能本地一键跑起来"，FAISS 是最轻量的选择。

### 5. Agent 路由：根据问题类型自动选择工具

```python
class Router:
    def decide_mode(self, question: str) -> str:
        intent = self.classifier.classify(question)
        if intent in {API_BY_MODULE, WORKFLOW_STEPS, ROLES_BY_PERMISSION}:
            return "graph"
        if intent == ERROR_SOLUTION:
            return "hybrid"
        return "vector"
```

**三种模式**：
- **graph**：结构化问题（API、流程、权限）→ 用 text2cypher + Neo4j
- **vector**：普通语义问题 → 用 FAISS 检索
- **hybrid**：错误排查 → 同时查图谱和文档

---

## 五、测试设计：证明 GraphRAG 的优势

设计了 5 类测试问题，覆盖 GraphRAG 的核心优势：

| 问题 | 模式 | 为什么普通 RAG 不够 |
|---|---|---|
| 采购模块有哪些 API？ | graph | 需要精确列表，语义搜索会遗漏 |
| 谁可以审批采购订单？ | graph | 需要 Role → Permission 链条推理 |
| 采购订单从创建到入库经过哪些步骤？ | graph | 需要遍历 `NEXT_STEP` 关系链 |
| 附件上传失败怎么解决？ | hybrid | 需要 ErrorCode → Cause → Solution 结构 |
| 采购订单转库存涉及哪些模块？ | graph | 需要跨模块关系查询 |

---

## 六、项目结构

```
neo4j-graphrag-agent/
├── data/raw_docs/          # 5 份模拟 ERP 文档
├── src/graphrag_agent/
│   ├── ingestion/          # 文档加载
│   ├── ontology/           # Schema 定义 (10 实体 + 9 关系)
│   ├── extraction/         # 规则抽取
│   ├── graph/              # Neo4j 客户端 + 安全校验 + 批量导入
│   ├── retrieval/          # 切片 + Embedding + FAISS
│   ├── text2cypher/        # 意图分类 + Cypher 模板
│   ├── agent/              # 路由 + 工具 + 答案生成
│   ├── api/                # FastAPI (6 个端点)
│   └── cli.py              # Typer CLI
├── tests/                  # 27 个 pytest 测试
├── examples/               # 3 个演示脚本
└── docker-compose.yml      # Neo4j + API 一键启动
```

---

## 七、Quick Start

```bash
# 1. 安装依赖
pip install -e ".[dev]"

# 2. 启动 Neo4j + API
docker compose up -d

# 3. 构建知识图谱
python examples/build_graph.py

# 4. 提问
graphrag ask "Which APIs are available in the procurement module?"
```

---

## 八、第一版的设计哲学：克制

这个项目刻意做了以下**减法**：
- ❌ 不用 LLM 做实体抽取 → ✅ 规则抽取，保证可复现
- ❌ 不用 LLM 做 text2cypher → ✅ 模板匹配，零成本
- ❌ 不用 LLM 生成答案 → ✅ 规则拼接证据，可测试
- ❌ 不用 Milvus/Pinecone → ✅ FAISS，本地轻量
- ❌ 不做前端界面 → ✅ FastAPI + CLI，聚焦核心能力

**减法的目的**：把"知识图谱建模"和"Agent 工程化"这两个核心能力做到极致，而不是做一个功能堆砌的半成品。

---

## 九、适合投递的岗位

| 岗位 | 这个项目证明的能力 |
|---|---|
| LLM Application Engineer | Agent 工具编排、意图路由、证据融合 |
| RAG Engineer | 向量检索、Hybrid RAG、检索策略设计 |
| AI Agent Engineer | 工具调用、流程设计、结构化输出 |
| Knowledge Graph Engineer | Ontology 建模、Neo4j、Cypher、图导入 |
| Enterprise AI Engineer | 业务文档理解、ERP 知识建模、结构化推理 |

---

## 十、后续扩展方向

如果想继续迭代，可以按以下顺序扩展：
1. **LLM-based text2cypher**：在模板基础上，用 LLM 处理更灵活的问法
2. **LLM 抽取**：在规则抽取的基础上，用 LLM 补充边界情况
3. **多跳推理**：支持"哪些角色能审批涉及库存的采购订单？"（Role → Permission → Workflow → Step → Module 多跳）
4. **评估体系**：设计 Recall@k、MRR 等指标，对比 Vector RAG vs GraphRAG vs Hybrid
5. **前端界面**：Gradio/Streamlit 做一个问答界面

---

## 结语

这个项目的核心目的不是"做一个能用的 Chatbot"，而是**证明你能把企业知识从非结构化文档中提取出来、建模成结构化图谱、设计安全的查询接口、并用 Agent 把这些能力编排成一个可靠的问答系统**。

如果你正在准备 AI 应用工程师的面试，把这个项目放在简历上，面试官问"你做过什么 RAG 项目？"的时候，你可以直接打开 Neo4j Browser 给他看图谱，然后演示 text2cypher 的生成过程——这比说"我用 LangChain 接了一个向量库"要有说服力得多。

**GitHub:** https://github.com/13331800076/neo4j-graphrag-agent

---

## 参考

- [Neo4j GraphRAG Python SDK](https://neo4j.com/docs/neo4j-graphrag-python/current/)
- [FAISS 官方文档](https://github.com/facebookresearch/faiss)
- [sentence-transformers](https://www.sbert.net/)
- [GraphRAG: A modular graph-based Retrieval-Augmented Generation system](https://microsoft.github.io/graphrag/)
