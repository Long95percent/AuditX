# AuditX / VeriDoc 代码审查导览

> 这份文档用于帮助你快速审查当前项目骨架：从哪里进、各层逻辑在哪个目录、核心类型和函数在哪里、审查时应该重点看什么。当前项目仍处于基础框架阶段，尚未实现 OCR、LLM、第三方 API、完整 Agent 编排和真实业务审计逻辑。

## 1. 先看哪些文件

建议按这个顺序审查：

1. `README.md`：看项目定位、技术栈、当前阶段范围。
2. `pyproject.toml`：看后端依赖、Python 版本、pytest/ruff/mypy 配置。
3. `frontend/package.json`：看前端 Vite/React/TypeScript 依赖与脚本。
4. `src-tauri/tauri.conf.json`：看桌面端 Tauri 配置和 Python sidecar 预留方式。
5. `backend/auditx/main.py`：看 FastAPI 后端入口。
6. `backend/auditx/domain/`：看强类型领域模型，尤其是 bbox 和 evidence 约束。
7. `backend/tests/unit/`：看当前最小验证用例。
8. `WORKLOG.md`：看每一步初始化和安装操作的时间戳记录。

## 2. 项目入口

### 2.1 后端 API 入口

文件：`backend/auditx/main.py`

关键函数 / 对象：

- `create_app()`：FastAPI 应用工厂，后续所有 API router 都应该挂到这里。
- `app = create_app()`：ASGI 入口对象，后续可由 `uvicorn auditx.main:app` 启动。
- `/health`：当前唯一健康检查接口，用于确认后端服务可运行。

审查重点：

- 入口是否保持轻量，只负责组装应用，不写业务逻辑。
- 配置是否通过 `get_settings()` 注入，而不是在入口里硬编码。
- 后续新增路由时，应该通过 `backend/auditx/api/` 下的 router 文件引入。

### 2.2 前端入口

文件：`frontend/src/main.tsx`

关键逻辑：

- 使用 `ReactDOM.createRoot(...)` 挂载 React 应用。
- 渲染 `frontend/src/app/App.tsx` 中的 `App` 组件。
- 引入全局样式 `frontend/src/styles/global.css`。

主组件：`frontend/src/app/App.tsx`

当前内容：

- 显示 AuditX / VeriDoc 桌面审计工作台占位界面。
- 预留文档预览、风险列表、审计时间线三个区域。
- 使用 `AuditFinding` 类型占位，类型定义来自 `frontend/src/types/audit.ts`。

审查重点：

- UI 当前只是骨架，不应期待真实数据流。
- 前端不应该拼接审计 Prompt，也不应该直接调用 OCR/LLM/第三方 API。
- 后续 API 调用应集中放在 `frontend/src/api/`。

### 2.3 桌面端入口

文件：`src-tauri/src/main.rs`

关键逻辑：

- `tauri::Builder::default()`：Tauri 桌面应用启动入口。
- `tauri::generate_context!()`：读取 `src-tauri/tauri.conf.json` 配置。

配置文件：`src-tauri/tauri.conf.json`

关键配置：

- `devUrl`: 指向 Vite 开发服务 `http://127.0.0.1:5173`。
- `frontendDist`: 指向前端构建产物 `../frontend/dist`。
- `externalBin`: 预留 Python sidecar 二进制 `binaries/auditx-sidecar`。

审查重点：

- 当前还没有真实 sidecar 二进制，只是预留结构。
- Rust/Tauri 只作为桌面壳，不承载审计业务逻辑。
- 后续如果加入 Tauri command，应避免把复杂审计逻辑写进 Rust 层。

## 3. 后端目录职责

### 3.1 `backend/auditx/domain/`

职责：定义稳定的领域模型，不依赖 FastAPI、数据库、LLM、OCR 或第三方 API。

重要文件：

#### `backend/auditx/domain/documents.py`

核心类型：

- `BBox`：页面坐标框，字段为 `x0/y0/x1/y1`。
  - 约束：所有坐标必须 `>= 0`。
  - 约束：`x1 > x0`，`y1 > y0`。
- `BlockType`：版面块类型，包括 `title/paragraph/table/image/header/footer`。
- `LayoutBlock`：文档中的一个版面块，包含 `block_id`、`page_number`、`block_type`、`text`、`bbox`。
- `DocumentPage`：单页文档，包含页码、页面尺寸和 blocks。
- `ParsedDocument`：解析后的文档结构，包含文档 ID、文件名和页面列表。

审查重点：

- bbox 是后续“精准定位证据”的基础，不能改成松散的 list 或 dict。
- 文档解析结果必须保留 `page_number`、`block_id`、`bbox`。
- Domain 层不应该 import `fastapi`、`requests`、`openai`、数据库 SDK。

#### `backend/auditx/domain/audit.py`

核心类型：

- `RiskLevel`：风险等级，取值 `high/medium/low/info`。
- `Evidence`：风险证据。
  - 必填：`document_id`、`page_number`、`block_id`、`quote`、`bbox`。
  - 可选：`start_offset`、`end_offset`。
  - 约束：如果同时存在 offset，必须 `end_offset > start_offset`。
- `AuditFinding`：审计风险点。
  - 必填：`finding_id`、`rule_id`、`title`、`description`、`risk_level`、`confidence`、`evidences`、`source_agent`。
  - `confidence` 限制在 `[0, 1]`。
  - `evidences` 使用 `Field(min_length=1)`，即至少必须有一条证据。

审查重点：

- `AuditFinding.evidences` 不能为空，这是“无证据不出报告”的第一道强约束。
- 每条 `Evidence` 必须有 bbox，这是后续 PDF 高亮和工业级审计可信度的基础。
- 不要让模型输出的任意 JSON 绕过这些 Pydantic 模型。

### 3.2 `backend/auditx/agent_core/`

职责：后续放通用 Agent 编排、证据校验、输出标准化、重试策略和 guardrails。

当前文件：`backend/auditx/agent_core/evidence_validator.py`

核心类：

- `EvidenceValidator`

核心函数：

- `validate(finding: AuditFinding, document: ParsedDocument) -> bool`

当前校验逻辑：

1. 从 `ParsedDocument.pages[].blocks[]` 建立 `block_id -> LayoutBlock` 映射。
2. 遍历 `AuditFinding.evidences`。
3. 校验 `block_id` 是否存在。
4. 校验 evidence 的 `page_number` 是否等于 block 的 `page_number`。
5. 校验 evidence 的 `quote` 是否出现在 block 的 `text` 中。
6. 任一失败返回 `False`，全部通过返回 `True`。

审查重点：

- 这是第二道证据校验，不取代 Pydantic 类型约束。
- 当前还没有校验 bbox 是否落在页面尺寸内，后续可加。
- 当前还没有校验 evidence.document_id 是否等于 document.document_id，后续应加。
- 该模块不应该直接调用 LLM 或工具。

### 3.3 `backend/auditx/document_pipeline/`

职责：后续放 PDF/DOCX/图片解析、OCR、版面分析、表格解析、阅读顺序恢复。

当前文件：`backend/auditx/document_pipeline/base.py`

核心抽象：

- `DocumentParser`
- `parse(file_path: str) -> ParsedDocument`

审查重点：

- 当前只有接口，没有实现。
- 后续 PaddleOCR、PDF parser、布局模型都应该实现这个抽象或更细分的 provider 抽象。
- 输出必须统一为 `ParsedDocument`，不能让 OCR SDK 的原始结构泄漏到上层。

### 3.4 `backend/auditx/tool_registry/`

职责：后续统一管理可插拔工具，例如企业查询、时间线检查、国标数据库、合同条款库。

重要文件：

#### `backend/auditx/tool_registry/base.py`

核心类型：

- `ToolResult`
  - `tool_name`
  - `ok`
  - `data`
  - `error`
- `Tool`
  - 抽象字段：`name`、`description`
  - 抽象方法：`run(input_data: dict[str, Any]) -> ToolResult`

#### `backend/auditx/tool_registry/registry.py`

核心类：

- `ToolRegistry`

核心函数：

- `register(tool: Tool) -> None`：注册工具，重复名称会抛 `ValueError`。
- `get(name: str) -> Tool`：按名称获取工具，未知工具会抛 `KeyError`。
- `names() -> list[str]`：返回已注册工具名称。

审查重点：

- Agent Core 后续应该只依赖 `ToolRegistry`，不能直接 import 某个 HR/服装/法务工具实现。
- 工具只返回事实，不直接生成最终审计结论。
- 外部 API 工具后续必须可 mock，方便黄金测试集评测。

### 3.5 `backend/auditx/config/`

职责：集中管理配置。

当前文件：`backend/auditx/config/settings.py`

核心类型 / 函数：

- `Settings`：基于 `pydantic-settings` 的配置对象。
- `get_settings() -> Settings`：返回配置实例。

当前配置项：

- `env`
- `log_level`
- `api_host`
- `api_port`
- `storage_dir`
- `llm_provider`
- `llm_model`
- `llm_api_key`
- `ocr_provider`

审查重点：

- 密钥不应该写入代码，应该来自 `.env` 或系统环境变量。
- 配置命名使用 `AUDITX_` 前缀。
- 后续新增模型、OCR、存储配置应先进入这里，而不是散落到业务文件里。

### 3.6 `backend/auditx/domains/hr_recruitment/`

职责：HR 招聘审计领域包。当前只是占位，后续可添加规则、Prompt、工具和 schema。

当前文件：

- `ruleset.yaml`：HR 规则包占位，目前 `rules: []`。
- `prompts.yaml`：HR Prompt 占位，强调每个风险点必须有页码、block id、quote、bbox。

审查重点：

- 领域规则应该放这里，不应该写死在 `agent_core`。
- HR 场景不应该污染服装质检或合同审查场景。

### 3.7 当前空目录说明

这些目录目前只有 `__init__.py`，用于预留清晰边界：

- `backend/auditx/api/`：后续 FastAPI routers。
- `backend/auditx/application/`：后续用例编排，例如 `AuditUseCase`。
- `backend/auditx/rule_engine/`：后续规则加载、筛选、校验。
- `backend/auditx/infrastructure/llm/`：后续 LLM Provider。
- `backend/auditx/infrastructure/ocr/`：后续 OCR Provider。
- `backend/auditx/infrastructure/storage/`：后续数据库、文件存储。
- `backend/auditx/infrastructure/observability/`：后续日志、指标、trace。

审查重点：

- 这些目录为空是刻意的，不是遗漏。
- 后续开发时应把代码放到对应边界内，不要把实现堆到入口文件。

## 4. 前端目录职责

### 4.1 `frontend/src/app/`

当前文件：`frontend/src/app/App.tsx`

职责：应用顶层布局。

当前区域：

- Hero 区：展示 AuditX / VeriDoc 定位。
- Document Viewer Placeholder：文档预览区域占位。
- Findings Placeholder：风险列表区域占位。
- Audit Timeline Placeholder：审计事件流区域占位。

后续建议：

- 顶层只负责布局和状态组合。
- 具体 PDF 渲染放 `components/DocumentViewer/`。
- 风险列表放 `components/FindingPanel/`。
- 证据高亮放 `components/EvidenceHighlighter/`。
- 事件流放 `components/AuditTimeline/`。

### 4.2 `frontend/src/types/`

当前文件：`frontend/src/types/audit.ts`

核心类型：

- `BBox`
- `Evidence`
- `RiskLevel`
- `AuditFinding`

审查重点：

- 前端类型应与后端 Pydantic 模型保持字段语义一致。
- 目前前端字段使用 camelCase，后端字段使用 snake_case；后续 API 层需要明确转换策略。
- bbox 不应被简化掉，否则前端无法做精准证据高亮。

### 4.3 `frontend/src/styles/`

当前文件：`frontend/src/styles/global.css`

职责：全局样式和 Glassmorphism 基础视觉。

审查重点：

- 当前只是视觉骨架。
- 后续复杂组件样式可以按组件拆分，避免全堆到 global.css。

### 4.4 `frontend/src/api/`

当前为空。

后续职责：

- 封装后端 API 调用。
- 管理 `fetch`、错误处理、DTO 转换。

审查重点：

- 不要在组件里散落裸 `fetch`。
- 不要在前端直接访问 LLM、OCR 或第三方审计 API。

## 5. 测试入口

### 5.1 pytest 配置

文件：`pyproject.toml`

关键配置：

- `testpaths = ["backend/tests"]`
- `pythonpath = ["backend"]`
- `addopts = "-q"`

运行方式：

```powershell
$env:Path = "C:\Users\22641\.local\bin;C:\Users\22641\.cargo\bin;$env:Path"
$env:UV_CACHE_DIR = ".uv-cache"
uv run pytest backend/tests/unit -q
```

如果只是使用当前系统 Python，也可以：

```powershell
python -m pytest backend/tests/unit -q
```

### 5.2 当前单元测试

文件：`backend/tests/unit/test_audit_models.py`

覆盖点：

- `AuditFinding` 不允许 `evidences=[]`。
- `Evidence` 不允许非法 bbox，例如 `x1 <= x0`。

文件：`backend/tests/unit/test_evidence_validator.py`

覆盖点：

- 当 evidence 的 `block_id/page_number/quote` 能在 `ParsedDocument` 中找到时，`EvidenceValidator.validate(...)` 返回 `True`。

审查重点：

- 这些测试是基础护栏，不是完整黄金测试集。
- 后续每增加一个核心规则或工具，都应有对应单元测试或评测 case。

## 6. 配置和环境审查

### 6.1 `.env.example`

用途：记录可配置项模板，不放真实密钥。

重点字段：

- `AUDITX_ENV`
- `AUDITX_LOG_LEVEL`
- `AUDITX_API_HOST`
- `AUDITX_API_PORT`
- `AUDITX_STORAGE_DIR`
- `AUDITX_LLM_PROVIDER`
- `AUDITX_LLM_MODEL`
- `AUDITX_LLM_API_KEY`
- `AUDITX_OCR_PROVIDER`
- `UV_CACHE_DIR=.uv-cache`

审查重点：

- 真实 API Key 不允许提交。
- `UV_CACHE_DIR=.uv-cache` 是为规避本机默认 uv cache 权限问题。

### 6.2 `.gitignore`

重点忽略：

- `.venv/`
- `.uv-cache/`
- `__pycache__/`
- `.pytest_cache/`
- `frontend/node_modules/`
- `frontend/dist/`
- `src-tauri/target/`
- `.env`

审查重点：

- 不应提交虚拟环境、缓存、构建产物、真实环境变量。

## 7. 当前逻辑调用关系

当前骨架的逻辑关系很少，可以理解为：

```text
后端：
backend/auditx/main.py
  -> get_settings() from backend/auditx/config/settings.py
  -> FastAPI /health

证据校验：
AuditFinding from backend/auditx/domain/audit.py
ParsedDocument from backend/auditx/domain/documents.py
  -> EvidenceValidator.validate(...) in backend/auditx/agent_core/evidence_validator.py

工具注册：
Tool from backend/auditx/tool_registry/base.py
  -> ToolRegistry.register/get/names in backend/auditx/tool_registry/registry.py

前端：
frontend/src/main.tsx
  -> App from frontend/src/app/App.tsx
  -> AuditFinding type from frontend/src/types/audit.ts
  -> global styles from frontend/src/styles/global.css

桌面：
src-tauri/src/main.rs
  -> src-tauri/tauri.conf.json
  -> frontend devUrl/dist
  -> future Python sidecar externalBin
```

## 8. 审查时最重要的红线

如果后续代码违反这些点，需要及时指出：

- 不允许把 OCR、Agent、工具调用、数据库、报告生成全写进一个文件。
- 不允许 `AuditFinding` 没有 evidence。
- 不允许 evidence 没有 bbox。
- 不允许 Agent Core 直接依赖某个具体业务场景工具。
- 不允许 Domain 层依赖 FastAPI、LLM SDK、OCR SDK、数据库 SDK。
- 不允许前端直接拼 Prompt 或直连 LLM/OCR/第三方 API。
- 不允许真实密钥进入 `.env.example`、README 或代码。
- 不允许绕过 Pydantic 模型直接返回任意 dict 作为审计结果。

## 9. 后续审查建议

当我后续继续写代码时，你可以按下面的问题审查：

1. 新增文件是否放在正确目录？
2. 这个文件是否只有一个清晰职责？
3. 是否有入口层、应用层、领域层、基础设施层混写？
4. 新增审计结果是否经过 Pydantic 强类型约束？
5. 每个风险点是否一定能追踪到 `page_number/block_id/quote/bbox`？
6. 外部依赖是否可替换、可 mock？
7. 是否新增或更新了对应测试？
8. `WORKLOG.md` 是否记录了关键操作和异常？
