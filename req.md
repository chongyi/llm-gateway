# 最终需求文档：模型路由与代理服务（兼容 OpenAI / Anthropic）+ 管理面板

## 1. 背景
需要实现一个代理服务，用于接收 OpenAI 或 Anthropic 客户端请求。系统根据用户请求中的模型（requested model）以及用户提供的规格与内部规则进行匹配：在**不改变请求体其它字段**的前提下，仅替换请求体中的**模型名**为目标模型（target model），再将请求转发给配置的上游供应商（Provider/Vendor）处理，并将结果返回给客户端。系统需具备自动重试与故障切换能力，并将关键请求信息与性能指标记录入库，提供管理后台用于配置与查询。

## 2. 目标
1. **透明代理**：兼容 OpenAI/Anthropic 客户端调用方式，返回兼容格式响应。
2. **仅修改模型名**：请求转发过程中只允许修改 model 字段，不改动请求体其它内容。
3. **规则引擎匹配**：通过规则引擎处理所有规则，输出可用供应商集合及其目标模型。
4. **轮询选择**：对匹配到的供应商节点使用轮询（轮转）策略选择当前节点。
5. **可靠重试与故障切换**：按状态码执行同供应商重试或切换到下一供应商节点。
6. **Token 统计**：按“标准大模型接口 Token 计数方法”统计输入/输出 Token 并落日志。
7. **完整可观测**：记录详细请求日志，包括时间、模型、供应商、重试、延迟、Token、请求/响应、错误等。
8. **可配置可管理**：提供现代化管理面板支持供应商、模型/规则、API Case、日志查询与筛选。
9. **多数据库引擎**：支持 SQLite 与 PostgreSQL，默认 SQLite；数据访问抽象以便切换。
10. **工程质量**：所有代码必须具备单元测试，且执行过程中保证全部单测通过。

## 3. 范围与非范围
### 3.1 范围（In Scope）
- 接入 OpenAI/Anthropic 风格请求并代理转发（只改模型名）。
- 规则引擎：基于上下文匹配并输出候选供应商及目标模型。
- 轮询策略选择供应商节点。
- 重试与故障切换逻辑。
- Token 统计与入库日志。
- 数据库存储：供应商、模型映射/规则、策略、API Case（API Key）、请求日志。
- 管理面板：供应商/模型/规则/API Case CRUD；请求日志查询与多条件筛选。

### 3.2 非范围（Out of Scope）
- **不需要限流**（Rate limiting）。
- **不需要账户级别控制**（账户/租户配额、分层权限、用量控制等）。
- 除 model 字段外的请求/响应内容改写（不做）。
- 若需权限体系（管理后台登录/角色权限）未在本需求中定义（可后续补充）。

## 4. 术语与关键概念
- **Requested Model**：客户端请求体中携带的模型名。
- **Target Model**：系统匹配后，替换进请求体的模型名。
- **Provider/Vendor**：上游供应商节点，拥有接口地址、协议与 API 类型。
- **Vendor Node**：一个可调用的供应商节点（通常对应一条 provider 配置记录）。
- **API Case**：用于鉴权的 API Key 实体（含 key_name 与 key_value/token）。
- **策略（Strategy）**：当前仅支持 **轮询（轮询/轮转）**。
- **规则引擎上下文（Context）**：用于规则匹配的输入数据集合。

## 5. 总体架构
### 5.1 系统组件
- **后端**：Python + FastAPI
  - Proxy 接口（兼容 OpenAI/Anthropic）
  - 管理接口（供前端面板调用）
  - 规则引擎
  - Provider 转发客户端（多协议/多 API 适配）
  - 重试与故障切换器
  - Token 计数器
  - 日志记录与脱敏模块
  - 数据访问抽象层（Repository/DAO）+ 多 DB 适配（SQLite/PG）
- **前端**：Next.js + TypeScript
  - 供应商管理
  - 模型与规则管理（含供应商-目标模型差异化配置）
  - API Case 管理
  - 请求日志查看与多条件筛选

### 5.2 核心请求流程（代理链路）
1. 客户端发起请求（OpenAI/Anthropic 风格）。
2. 后端鉴权（API Case token），获得 `api_key_id`。
3. 解析请求体与 headers，提取 `requested_model`。
4. 计算输入 Token（标准 Token 计数方法）。
5. 规则引擎处理所有规则，基于上下文输出**候选供应商集合**（每个供应商对应一个目标模型）。
6. 轮询策略从候选供应商中选出当前供应商节点。
7. **仅替换请求体中的 model 字段**为该供应商对应的 target model。
8. 转发请求到该供应商；按失败策略进行同供应商重试或切换至下一供应商节点。
9. 返回最终响应给客户端。
10. 计算输出 Token，记录请求日志（对敏感字段脱敏后入库）。

## 6. 功能性需求（Functional Requirements）

### 6.1 请求接入与转发
- FR-REQ-1：支持接收 OpenAI 或 Anthropic 客户端请求（兼容其调用方式）。
- FR-REQ-2：转发过程中保持请求 headers 与 body 原样不变，**仅允许修改模型名字段**。
- FR-REQ-3：按配置将请求转发到上游供应商接口，并将响应返回给客户端。

### 6.2 模型替换（只改 model）
- FR-MDL-1：从请求体获取 `requested_model`。
- FR-MDL-2：根据规则与策略确定目标模型 `target_model`（与供应商绑定）。
- FR-MDL-3：仅替换请求体中的 model 字段，不修改其它字段（messages/tools/temperature/max_tokens 等均保持一致）。

### 6.3 规则引擎（Rule Engine）
- FR-RULE-1：规则引擎每次请求必须“处理所有规则”（全量评估），并输出匹配结果。
- FR-RULE-2：规则引擎上下文必须包含：
  - `current_model`：当前请求模型（requested_model）
  - `headers`：请求头（结构化对象）
  - `request_body`：请求体（结构化对象）
  - `token_usage`：当前 Token 消耗（至少包含本次输入 Token；可扩展）
- FR-RULE-3：规则引擎输出必须包含：
  - 候选供应商节点列表（按匹配结果）
  - **每个候选供应商对应的 target_model**（因为：同一个请求模型在不同供应商下映射到不同目标模型）
  - 供策略选择所需的元信息（如优先级、权重、可用性等，可扩展）

### 6.4 供应商选择策略（轮询 / 轮转）
- FR-STR-1：系统必须实现策略机制；当前策略仅支持 **轮询（轮询/轮转）**。
- FR-STR-2：轮询在候选供应商节点之间进行轮转选择。
- FR-STR-3：轮询状态需可并发安全（可通过 DB/缓存/原子计数等方式实现，具体实现由设计决定）。

### 6.5 重试与故障切换
- FR-RT-1：当上游响应状态码 **≥ 500**：
  - 对**同一供应商**重试
  - 每次间隔 **1000ms**
  - 最多 **3 次**重试
- FR-RT-2：若同一供应商 3 次重试仍失败，则切换到**下一个匹配的供应商节点**继续尝试。
- FR-RT-3：当上游响应状态码 **< 500**：
  - 不对同一供应商重试
  - 直接切换到**下一个匹配的供应商节点**尝试
- FR-RT-4：当候选供应商全部尝试失败时，系统应向客户端返回失败结果（建议返回最后一次失败的状态与错误信息；具体响应封装可在实现阶段统一定义）。

### 6.6 Token 统计
- FR-TOK-1：输入 Token：使用“标准大模型接口 Token 计数方法”对用户请求进行统计。
- FR-TOK-2：输出 Token：对上游响应统计输出 Token。
- FR-TOK-3：输入/输出 Token 必须写入请求日志。

> 备注：Token 计数方法需要与目标协议（OpenAI/Anthropic）一致；实现可采用可插拔计数器，按 endpoint/协议选择计数方式。

### 6.7 请求日志记录（全量、可追溯、入库）
- FR-LOG-1：所有请求必须记录详细日志，字段至少包含：
  - 请求时间（request_time）
  - API Case：`api_key_id`、`api_key_name`
  - requested_model、target_model
  - 供应商：provider_id / provider_name
  - retry_count
  - first_byte_delay（首字节延迟）
  - total_time（总耗时）
  - input_tokens、output_tokens
  - request_headers（结构化、**脱敏后**）
  - request_body（结构化）
  - response_status
  - response_body
  - error_info（错误信息：结构化或文本）
- FR-LOG-2：日志必须能够支持多条件筛选查询（供前端日志页面使用）。

### 6.8 敏感信息脱敏
- FR-SEC-LOG-1：日志中记录的 `request_headers` 必须对 `authorization` 字段进行脱敏/打码后再入库。
  - 示例要求：保留字段名，值部分进行掩码（如 `Bearer *****` 或只保留前后若干位，中间打码）。
- FR-SEC-LOG-2：脱敏应在入库前统一处理，保证数据库内不保存明文 authorization。

### 6.9 API Case（API Key）管理
- FR-KEY-1：系统提供 API Case 表，包含：
  - API key name
  - API key value（token）
- FR-KEY-2：API key value 通过随机算法生成。
- FR-KEY-3：每次请求使用的 API Case 的 **ID 必须落日志**（`api_key_id`）。

## 7. 数据存储与多数据库支持

### 7.1 数据库存储引擎
- FR-DB-1：支持 **SQLite** 与 **PostgreSQL（PG）** 两种存储引擎。
- FR-DB-2：默认使用 SQLite。
- FR-DB-3：通过配置切换数据库引擎（例如环境变量或配置文件指定）。

### 7.2 数据访问抽象与分层
- FR-DB-4：数据库访问必须抽象一层（Repository/DAO 接口），业务逻辑不得耦合具体数据库实现。
- FR-DB-5：公共的数据访问模式、事务管理、分页查询等能力应沉淀在公共 package，避免重复实现。

## 8. 数据模型（推荐结构，支持“同模型+不同供应商=不同目标模型”）
> 具体字段类型以实现为准；建议统一使用可兼容 SQLite/PG 的设计，并通过迁移工具维护。

### 8.1 服务商表：`service_providers`
- `id`（PK）
- `name`
- `base_url`（接口地址）
- `protocol`（协议/兼容类型）
- `api_type` / `api_name`
- `is_active`（建议）
- `created_at` / `updated_at`（建议）

### 8.2 模型映射表：`model_mappings`（以 requested_model 为主键）
- `requested_model`（PK）
- `strategy`（当前固定：轮询）
- `matching_rules`（模型层规则，可选；格式由规则引擎定义）
- `capabilities` / `functionality`（可选）
- `created_at` / `updated_at`（建议）

### 8.3 模型-供应商映射表：`model_mapping_providers`（关键：每个供应商可有不同 target_model）
- `id`（PK）
- `requested_model`（FK -> model_mappings.requested_model）
- `provider_id`（FK -> service_providers.id）
- `target_model_name`（**该供应商对应的目标模型名**）
- `provider_rules`（可选：供应商级规则，用于更细粒度控制；格式同规则引擎定义）
- `priority`（可选）
- `weight`（可选）
- `is_active`（建议）
- `created_at` / `updated_at`（建议）

### 8.4 API Case 表：`api_keys`
- `id`（PK）
- `key_name`（unique）
- `key_value`（随机生成 token）
- `is_active`（建议）
- `created_at` / `last_used_at`（建议）

### 8.5 请求日志表：`request_logs`
- `id`（PK）
- `request_time`
- `api_key_id`（FK -> api_keys.id）
- `api_key_name`（可冗余）
- `requested_model`
- `target_model`
- `provider_id`（FK -> service_providers.id）
- `retry_count`
- `first_byte_delay_ms`
- `total_time_ms`
- `input_tokens`
- `output_tokens`
- `request_headers`（JSON / JSONB；**已脱敏**）
- `request_body`（JSON / JSONB）
- `response_status`
- `response_body`（JSON/TEXT）
- `error_info`（JSON/TEXT）
- `trace_id`（建议）

## 9. 后端接口（FastAPI）

### 9.1 代理接口（面向客户端）
- 兼容 OpenAI/Anthropic 的核心接口（按实现确定具体路径集合）。
- 行为：鉴权 -> 规则匹配 -> 轮询选供应商 -> 替换 model -> 转发 -> 重试/切换 -> 返回 -> 记录日志。

### 9.2 管理接口（供前端面板）
- `/admin/providers`：供应商 CRUD
- `/admin/models`：模型映射 CRUD（含规则字段）
- `/admin/model-providers`：模型-供应商映射 CRUD（requested_model + provider_id + target_model + provider_rules）
- `/admin/api-keys`：API Case CRUD
- `/admin/logs`：日志查询（分页 + 多条件过滤）
- `/admin/logs/{id}`：日志详情

## 10. 前端管理面板（Next.js + TypeScript）

### 10.1 通用要求
- FE-UI-1：现代化设计风格（清晰层级、统一间距、响应式布局、良好交互反馈）。
- FE-UI-2：通用组件沉淀：表格、表单、弹窗、分页、筛选器、JSON 展示/编辑组件等，避免重复代码。
- FE-UI-3：列表页支持分页、排序、搜索；操作需有确认与结果提示。

### 10.2 供应商管理（CRUD）
- 列表：展示 ID、名称、base_url、protocol、api_type/api_name、状态、更新时间等。
- 新增/编辑：表单校验（必填、URL 格式等）。
- 删除：二次确认；若被引用需提示（具体约束由后端决定）。

### 10.3 模型管理（CRUD + 规则设定 + 供应商差异化目标模型）
- 模型映射（model_mappings）CRUD：
  - requested_model、策略（轮询）、模型层 rules（如启用）、功能描述等。
- **模型-供应商映射（model_mapping_providers）CRUD（重点）**：
  - 同一个 requested_model 下，可配置多个供应商
  - **每个供应商可配置不同 target_model_name**
  - 可配置 provider_rules（如启用）以支持更细的匹配逻辑
  - 可配置 priority/weight（可选）
- 规则编辑器：
  - 需要支持规则设定与校验，规则可引用上下文：model、headers、request_body、token_usage。
  - 形态建议（实现选型）：
    1) **结构化规则编辑器**（优先，减少手写错误）
    2) **JSON 规则编辑器**（兜底）  
       - 建议评估开源组件：Monaco Editor（JSON + Schema 校验）、或基于 JSON Schema 的表单编辑器等（由实现阶段选型）

### 10.4 请求日志页面（查看 + 多条件筛选）
- 列表默认按时间倒序。
- 必须支持筛选条件（至少）：
  - 时间范围（起止）
  - requested_model / target_model（模糊）
  - provider（下拉）
  - response_status（精确/区间，如 2xx/4xx/5xx 或 >=500）
  - 是否错误（error_info 是否为空）
  - api_key_id / api_key_name
  - retry_count（=0 / >0）
  - token 区间（可选）
  - 总耗时区间（可选）
- 日志详情：展示脱敏后的 headers、结构化 request_body、response_body、error_info，并支持复制/折叠。

### 10.5 API Case 页面（CRUD）
- 列表：id、key_name、key_value（默认隐藏，可复制显示策略）、状态、创建时间、最后使用时间等。
- 新增：输入 key_name，key_value 由后端随机生成并返回；创建成功后提供复制入口。
- 编辑：允许修改名称/状态（是否支持重置 key_value 可作为扩展）。
- 删除：二次确认。

## 11. 工程架构与代码规范（后端）
### 11.1 分层与可复用性
- NFR-ARCH-1：采用清晰分层，避免路由层直接写业务逻辑或 SQL。
- NFR-ARCH-2：业务逻辑（Service）依赖 Repository 接口而非具体数据库实现。
- NFR-ARCH-3：公共能力抽取到公共 package（common），避免重复代码：
  - 重试器、HTTP 客户端封装、计时器、token 计数器、脱敏器、错误封装、配置加载等。
- NFR-ARCH-4：模块职责单一、命名规范、可测试、可扩展。

### 11.2 推荐目录结构（示例）
- `app/`
  - `api/`（路由层）
  - `services/`（业务编排：匹配/轮询/转发/重试/日志）
  - `rules/`（规则引擎：规则定义、上下文、执行器）
  - `providers/`（上游适配：openai-like / anthropic-like）
  - `repositories/`（Repository 接口）
  - `repositories/sqlalchemy/`（SQLite/PG 实现）
  - `db/`（连接、会话、迁移）
  - `domain/`（领域模型/DTO）
  - `common/`（公共能力）
  - `tests/`

## 12. 测试与质量门禁（必须）
- NFR-TEST-1：**所有代码必须有单元测试**。
- NFR-TEST-2：执行/交付过程中必须确保**所有单元测试全部通过**（失败即阻断）。
- NFR-TEST-3：关键覆盖范围（至少）：
  - 规则引擎：上下文包含 headers/request_body/token_usage/model 的匹配逻辑
  - 模型替换：只改 model、不改其它字段
  - 轮询策略：多节点轮转正确性与并发一致性（按设计选择可测方案）
  - 重试/切换：≥500 同供应商 1000ms * 3；&lt; 500 直接切换；节点耗尽行为
  - Provider 转发：请求透传、响应透传、错误处理
  - Token 计数：输入/输出统计与落库
  - Repository：SQLite（默认）下的基础读写与一致性；可扩展 PG 适配的契约测试
  - 脱敏：authorization 字段打码后入库验证
- NFR-TEST-4：外部依赖可注入/可 Mock（DB、上游 HTTP、时间、随机数），保证测试稳定可重复。

## 13. 验收标准（Definition of Done）
1. 代理链路可用：请求接入、规则匹配、轮询选择、仅替换 model、转发、按规则重试/切换、返回响应。
2. 规则引擎上下文包含：model、headers、request_body、token_usage；并能输出候选供应商及其 target_model。
3. 日志完整落库：字段齐全；authorization 已脱敏；可按条件查询。
4. 数据库支持：默认 SQLite 可运行；切换到 PG 不改业务代码（仅配置切换 + 实现层适配）。
5. 管理面板可用：供应商 CRUD、模型/规则/供应商目标模型配置 CRUD、API Case CRUD、日志查询与多条件筛选。
6. 单元测试覆盖满足要求，且项目执行过程中所有单元测试均通过。

## 14. 下一步（实施建议）
1. 明确首期需要兼容的 OpenAI/Anthropic 具体 endpoint 列表与字段差异处理策略（保持“只改 model”原则）。
2. 定义规则格式（JSON/DSL）与校验机制，并同步前端规则编辑器选型（结构化优先 + JSON 编辑兜底）。
3. 确定多 DB 技术方案（例如统一 ORM/迁移工具），落实 Repository 接口与实现分离。
4. 建立测试基线：测试框架、Mock 规范、契约测试模板与 CI 门禁流程。
