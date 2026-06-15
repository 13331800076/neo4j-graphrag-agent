# Neo4j GraphRAG Agent 设计文档

## 1. 项目信息

- **项目名称**: `neo4j-graphrag-agent`
- **日期**: 2026-06-15
- **设计者**: AI Application Engineer (中软国际)
- **目标**: 构建面向企业文档的 GraphRAG Agent，将产品文档、API 文档、流程文档转换为 Neo4j 知识图谱，实现比普通 RAG 更可靠的问答。

## 2. 一句话定位

A GraphRAG agent that converts enterprise-style documents into a Neo4j knowledge graph and answers questions through hybrid graph and vector retrieval.

## 3. 设计约束

基于用户确认的关键约束：

1. **无 LLM API Key**: text2cypher 完全使用模板匹配；Agent 答案生成使用规则模板 + 证据拼接；embedding 使用 `sentence-transformers` 本地模型。
2. **Neo4j 通过 Docker 启动**: `docker-compose.yml` 包含 `neo4j` 和 `api` 服务。
3. **第一版使用规则抽取**: 不依赖 LLM 做实体抽取，保证可复现、可测试。
4. **项目目录**: `/Users/harryyu/neo4j-graphrag-agent/`

## 4. 业务场景

**企业 ERP 产品知识库问答系统**

文档类型：
- 产品模块说明（采购、库存、财务、销售、附件管理）
- API / SDK 文档（`createPurchaseOrder`, `queryInventory` 等）
- 业务流程文档（采购申请 → 审批 → 下单 → 入库 → 对账）
- 权限规则文档（采购员、财务审核员、仓库管理员）
- 常见问题文档（订单无法提交、库存不足、附件上传失败）

## 5. 系统架构

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

## 6. 核心模块设计

### 6.1 Ingestion Module (`src/graphrag_agent/ingestion/`)

**职责**: 读取文档并标准化为统一格式。

**输入**: Markdown, TXT, JSON, CSV 文件
**输出**: `Document` 对象

```python
class Document:
    doc_id: str
    title: str
    source: str
    text: str
    metadata: dict
```

**核心文件**:
- `loader.py`: 文件读取器
- `document.py`: Document 数据类

### 6.2 Ontology Module (`src/graphrag_agent/ontology/`)

**职责**: 定义知识图谱的 schema。

```python
ENTITY_TYPES = [
    "Module", "BusinessObject", "API", "Role",
    "Permission", "Workflow", "Step", "ErrorCode",
    "Document", "Chunk"
]

RELATION_TYPES = [
    "BELONGS_TO", "USES_API", "REQUIRES_PERMISSION",
    "HAS_STEP", "NEXT_STEP", "RELATED_TO",
    "DEFINED_IN", "CAUSES", "SOLVED_BY"
]
```

**核心文件**:
- `schema.py`: 定义实体类型、关系类型、Pydantic 模型

### 6.3 Extraction Module (`src/graphrag_agent/extraction/`)

**职责**: 从文档中抽取实体和关系（规则-based，v1 不用 LLM）。

**输入**: `Document[]`
**输出**: `Entity[]`, `Relation[]`

**抽取规则**:
- 从 Markdown 标题识别 `Module`
- 从代码块/API 段落识别 `API`
- 从角色列表识别 `Role` 和 `Permission`
- 从流程列表识别 `Workflow` 和 `Step`
- 从 FAQ 识别 `ErrorCode`

**核心文件**:
- `rule_extractor.py`: 规则抽取器
- `models.py`: Entity, Relation 数据模型

### 6.4 Graph Module (`src/graphrag_agent/graph/`)

**职责**: Neo4j 写入、查询、安全执行。

**功能**:
- 初始化约束（唯一键等）
- 批量写入节点和关系
- 只读 Cypher 安全执行

**安全规则**:
- 只允许: `MATCH`, `RETURN`, `WHERE`, `LIMIT`, `ORDER BY`
- 禁止: `CREATE`, `MERGE`, `DELETE`, `SET`, `DROP`, `CALL dbms`

**核心文件**:
- `neo4j_client.py`: Neo4j 连接和查询
- `graph_loader.py`: 批量导入 Entity/Relation
- `safety.py`: Cypher 安全检查器

### 6.5 Retrieval Module (`src/graphrag_agent/retrieval/`)

**职责**: 文档切片、向量化、FAISS 检索。

**输入**: `Document[]`
**输出**: `SearchResult[]`

**核心文件**:
- `chunker.py`: 文本切片
- `embedder.py`: sentence-transformers  embedding
- `vector_store.py`: FAISS 索引管理

### 6.6 Text2Cypher Module (`src/graphrag_agent/text2cypher/`)

**职责**: 模板式将自然语言转换为 Cypher。

**意图分类**:
- `API_BY_MODULE`: 查询模块下的 API
- `ROLES_BY_PERMISSION`: 查询拥有某权限的角色
- `WORKFLOW_STEPS`: 查询流程步骤
- `ERROR_SOLUTION`: 查询错误原因和解决方案
- `BUSINESS_OBJECT_RELATION`: 查询业务对象关系

**模板示例**:
```python
# API_BY_MODULE
MATCH (m:Module {name: $module})<-[:BELONGS_TO]-(api:API)
RETURN api.name, api.description

# WORKFLOW_STEPS
MATCH (w:Workflow {name: $workflow})-[:HAS_STEP]->(s:Step)
OPTIONAL MATCH (s)-[:NEXT_STEP]->(next:Step)
RETURN s.name, next.name
ORDER BY s.order
```

**核心文件**:
- `intent_classifier.py`: 基于关键词的意图分类
- `templates.py`: Cypher 模板库
- `generator.py`: 模板渲染器

### 6.7 Agent Module (`src/graphrag_agent/agent/`)

**职责**: 工具编排、路由、答案生成。

**Agent 流程**:
1. 接收问题
2. 意图分类（复用 text2cypher 的分类器）
3. 选择模式：graph / vector / hybrid
4. 调用工具获取证据
5. 整合证据生成答案

**工具**:
- `search_vector_db`: 向量检索
- `query_neo4j`: 安全 Cypher 查询
- `generate_cypher`: 模板生成 Cypher
- `summarize_evidence`: 证据拼接（规则-based，无 LLM）

**核心文件**:
- `router.py`: 问题路由
- `tools.py`: 工具实现
- `answerer.py`: 答案生成

## 7. API 设计 (FastAPI)

| 端点 | 方法 | 描述 |
|---|---|---|
| `/health` | GET | 健康检查 |
| `/graph/build` | POST | 构建图谱（导入文档 + 抽取 + 写入 Neo4j） |
| `/search/vector` | POST | 向量检索 |
| `/cypher/generate` | POST | 生成 Cypher |
| `/graph/query` | POST | 执行安全 Cypher 查询 |
| `/agent/ask` | POST | GraphRAG 问答（支持 mode: graph/vector/hybrid） |

## 8. 测试问题设计（展示 GraphRAG 优势）

1. **Which APIs are available in the procurement module?**
2. **What are the steps from creating a purchase request to inventory receiving?**
3. **Which roles can approve purchase orders?**
4. **Why does attachment upload fail and how can it be fixed?**
5. **Which modules are involved when a purchase order is converted into inventory stock?**
6. **Which API should be used to query inventory availability before creating a purchase order?**
7. **How is PurchaseOrder related to InventoryItem and Supplier?**

## 9. 技术栈

| 类别 | 技术 |
|---|---|
| 语言 | Python 3.11+ |
| Web 框架 | FastAPI |
| 数据验证 | Pydantic |
| CLI | Typer |
| 测试 | pytest |
| 图数据库 | Neo4j (Docker) |
| 向量检索 | FAISS + sentence-transformers |
| 部署 | Docker, Docker Compose |

## 10. 仓库结构

```
neo4j-graphrag-agent/
├── README.md
├── SPEC.md
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── data/
│   ├── raw_docs/
│   └── sample_*.json
├── examples/
├── src/graphrag_agent/
│   ├── ingestion/
│   ├── extraction/
│   ├── ontology/
│   ├── graph/
│   ├── retrieval/
│   ├── text2cypher/
│   ├── agent/
│   ├── evaluation/
│   ├── api/
│   └── cli.py
├── tests/
│   ├── fixtures/
│   └── test_*.py
└── docs/
    ├── architecture.md
    ├── ontology.md
    └── graph_schema.md
```

## 11. 开发里程碑

| 周次 | 任务 | 交付物 |
|---|---|---|
| Week 1 | 项目骨架 + 文档 + ontology | 可运行空壳 + 测试通过 |
| Week 2 | 抽取 + Neo4j | 图谱可视化 + 数据导入 |
| Week 3 | 向量检索 + text2cypher | FAISS 搜索 + 模板 Cypher |
| Week 4 | Agent + README + 对比展示 | 完整演示 + Docker Compose |

## 12. 亮点总结

普通候选人展示：
```
文档 → embedding → vector search → LLM answer
```

本项目展示：
```
企业文档 → ontology → Neo4j 知识图谱 → text2cypher → graph reasoning → vector retrieval → evidence fusion → Agent answer
```

## 13. 第一版验收标准

- [ ] `docker compose up -d` 一键启动（Neo4j + API）
- [ ] 能导入模拟 ERP 文档并构建知识图谱
- [ ] 能在 Neo4j Browser 中查看图谱
- [ ] 5-7 个测试问题能返回结构化答案
- [ ] README 包含架构图、Quick Start、对比表
- [ ] pytest 测试通过
- [ ] 有 API 调用示例
