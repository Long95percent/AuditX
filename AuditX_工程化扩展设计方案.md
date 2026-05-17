# AuditX 工程化扩展设计方案

> 本文档基于现有 `方案.txt` 进行工程化扩充，目标是在不急于写代码的前提下，先明确项目边界、模块拆分、可扩展架构、目录结构、接口契约、测试策略与后续迭代路线，避免后期把 Agent、规则、工具、UI、评测全部堆在一个文件里。

## 1. 项目定位

AuditX 是一个面向企业非结构化文档的合规与风险审计 Agent 中台。第一阶段可落地为 HR 简历 / 背调 / 招聘风控审稿机器人，后续通过替换规则包与工具插件，扩展到服装供应链质检报告审计、跨境合同审查、招投标文件审查、财务票据合规检查等场景。

核心原则：

- **内核不绑定业务**：Agent 编排、证据校验、任务流转、评测框架保持通用。
- **场景通过插件注入**：HR、服装质检、法务合同等只作为独立 domain package 接入。
- **所有结论必须有证据**：风险点必须绑定页码、原文片段、版面块 ID 或表格单元格来源。
- **规则、工具、模型解耦**：规则可配置，工具可注册，模型可替换。
- **工程结构优先**：从第一天开始按模块、接口、测试分层设计，避免单文件脚本式堆叠。

## 2. 总体架构

推荐采用“前端工作台 + 后端审计服务 + 可插拔领域包 + 自动化评测流水线”的架构。

```text
┌──────────────────────────────────────────────────────────────┐
│                        Frontend Workbench                     │
│  文件上传 | 文档预览 | 风险看板 | 证据高亮 | 审计报告导出        │
└───────────────────────────────┬──────────────────────────────┘
                                │ HTTP / WebSocket
┌───────────────────────────────▼──────────────────────────────┐
│                         API Gateway                           │
│  Auth | File API | Audit API | Report API | Evaluation API     │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│                       Application Layer                       │
│  AuditUseCase | JobService | ReportService | EvaluationService │
└──────────────┬────────────────┬────────────────┬──────────────┘
               │                │                │
┌──────────────▼───────┐ ┌──────▼────────┐ ┌─────▼──────────────┐
│ Document Pipeline    │ │ Agent Core    │ │ Domain Packages     │
│ parse/ocr/layout     │ │ plan/act/check│ │ hr / fabric / legal  │
└──────────────┬───────┘ └──────┬────────┘ └─────┬──────────────┘
               │                │                │
┌──────────────▼────────────────▼────────────────▼──────────────┐
│                    Infrastructure Layer                        │
│ LLM Provider | Tool Registry | Vector Store | Object Storage   │
│ Database | Queue | Observability | External APIs               │
└───────────────────────────────────────────────────────────────┘
```

## 3. 分层设计

### 3.1 Presentation 层

负责用户交互，不写业务规则。

职责：

- 上传 PDF、Word、图片、Excel 等文档。
- 展示解析后的文档结构、页码、表格、图片区域。
- 展示审计任务状态、Agent 步骤、风险列表。
- 支持点击风险点后跳转到原文证据位置。
- 导出 HTML / PDF / JSON 审计报告。

不应承担：

- 不在前端判断业务风险。
- 不在前端拼接复杂 Prompt。
- 不在前端直连第三方背调、企查、质检标准 API。

### 3.2 API 层

负责输入输出协议、权限、参数校验、任务提交。

建议接口：

```text
POST   /api/files                         上传文档
GET    /api/files/{file_id}                获取文档元信息
POST   /api/audit-jobs                     创建审计任务
GET    /api/audit-jobs/{job_id}            查询任务状态
GET    /api/audit-jobs/{job_id}/events     获取实时事件流
GET    /api/audit-jobs/{job_id}/findings   获取风险点列表
POST   /api/reports                        生成审计报告
GET    /api/reports/{report_id}            下载报告
POST   /api/evaluations                    运行评测任务
```

### 3.3 Application 层

负责业务用例编排，但不包含具体领域规则。

核心服务：

- `AuditUseCase`：一次完整审计流程的入口。
- `DocumentIngestionService`：文件接收、格式识别、去重、入库。
- `AuditJobService`：任务创建、状态流转、取消、重试。
- `ReportService`：将审计结果渲染为报告。
- `EvaluationService`：执行测试集评测并计算指标。

应用层只依赖抽象接口，例如 `DocumentParser`、`AgentOrchestrator`、`RuleProvider`、`ToolRegistry`，不直接依赖某个 OCR SDK、某个 LLM 厂商或某个业务场景。

### 3.4 Domain 层

Domain 层定义系统稳定的业务对象与规则抽象。

核心对象：

```text
Document
DocumentPage
LayoutBlock
TableBlock
SceneGraph
AuditJob
AuditContext
AuditFinding
Evidence
RiskLevel
Rule
RuleSet
ToolCall
AuditReport
EvaluationCase
EvaluationResult
```

其中 `AuditFinding` 必须包含：

```text
finding_id       风险点 ID
rule_id          命中的规则 ID
title            风险标题
description      风险描述
risk_level       high / medium / low / info
confidence       置信度
evidences        证据列表，不能为空
suggestion       修改建议
source_agent     extractor / evaluator / tool
created_at       创建时间
```

`Evidence` 必须包含：

```text
document_id       文档 ID
page_number       页码
block_id          版面块 ID
quote             原文片段
start_offset      文本起始位置，可选
end_offset        文本结束位置，可选
bbox              页面坐标，可选
table_cell        表格单元格坐标，可选
```

强约束：没有 `Evidence` 的 `AuditFinding` 不允许进入最终报告。

### 3.5 Infrastructure 层

负责外部系统、存储、模型、队列、第三方 API 对接。

建议拆分：

- `llm_providers`：OpenAI、Anthropic、本地模型、兼容 OpenAI API 的模型。
- `ocr_providers`：PaddleOCR、Tesseract、云 OCR、版面分析模型。
- `storage`：本地文件、S3 / MinIO、数据库。
- `tool_adapters`：天眼查、企查查、国标数据库、内部知识库。
- `queue`：Celery、RQ、Arq 或消息队列。
- `observability`：日志、trace、metrics、成本统计。

基础设施层必须实现上层定义的接口，不能让 SDK 类型泄漏到 Application 或 Domain 层。

## 4. 核心模块拆分

### 4.1 文档解析模块 Document Pipeline

目标是把原始文件转换成带结构和证据坐标的 `ParsedDocument`。

子模块：

- `file_loader`：读取 PDF、DOCX、图片、Excel。
- `text_extractor`：提取原始文本。
- `ocr_engine`：处理扫描件和图片型 PDF。
- `layout_analyzer`：识别标题、段落、表格、页眉页脚、图片区域。
- `reading_order_resolver`：修复双栏、页眉干扰、表格乱序等问题。
- `table_parser`：将表格转成结构化 rows / columns / cells。
- `scene_graph_builder`：构建块与块之间的关系，例如标题从属、表格说明、脚注引用。
- `pii_redactor`：对手机号、身份证、邮箱等敏感信息脱敏。

输出对象示例：

```json
{
  "document_id": "doc_001",
  "pages": [
    {
      "page_number": 1,
      "blocks": [
        {
          "block_id": "p1_b3",
          "type": "paragraph",
          "text": "2022.03 - 2024.05 任职于 A 公司",
          "bbox": [120, 240, 500, 280]
        }
      ]
    }
  ]
}
```

设计重点：后续所有 Agent 结论都引用 `block_id`，而不是只引用一段不可追踪的纯文本。

### 4.2 Agent Core

Agent Core 只负责通用推理编排，不写 HR 或服装行业规则。

建议拆成：

- `PromptBuilder`：根据任务、规则、上下文生成 Prompt。
- `AgentOrchestrator`：控制 Extractor、Evaluator、Refiner 的执行顺序。
- `ExtractorAgent`：识别候选风险点。
- `EvaluatorAgent`：逐条验证风险是否有足够证据。
- `EvidenceValidator`：硬性校验页码、块 ID、原文片段是否真实存在。
- `FindingNormalizer`：统一风险输出结构。
- `RetryPolicy`：当证据不足、工具失败、模型输出非法时重试。
- `Guardrail`：限制模型输出范围，防止泄露隐私或编造证据。

推荐审计流程：

```text
1. Load RuleSet
2. Parse Document
3. Build AuditContext
4. ExtractorAgent generates candidate findings
5. EvidenceValidator checks quote/page/block existence
6. EvaluatorAgent reviews each candidate finding
7. Reject findings without evidence
8. Optional tools verify external facts
9. Normalize and rank findings
10. Generate report
```

### 4.3 Tool Registry

工具以插件形式注册，Agent Core 只调用统一接口。

统一接口建议：

```text
Tool.name
Tool.description
Tool.input_schema
Tool.output_schema
Tool.timeout_seconds
Tool.run(input, context) -> ToolResult
```

工具分类：

- `document_tools`：文档搜索、表格查询、上下文定位。
- `external_query_tools`：企业查询、工商信息、黑名单、标准法规。
- `calculation_tools`：时间线冲突、日期区间重叠、金额校验。
- `knowledge_tools`：RAG 检索、标准条款检索、政策库检索。

工具实现原则：

- 每个工具单独文件，单一职责。
- 工具输入输出必须结构化，避免返回大段不可控文本。
- 工具失败必须返回可区分的错误类型，例如超时、鉴权失败、无结果、限流。
- 工具不得直接修改审计结果，只返回事实，由 Agent 或规则层决定是否形成风险点。

### 4.4 Rule Engine

规则必须与代码解耦，优先使用 YAML / JSON 配置。

规则包结构示例：

```text
rules/
  hr_recruitment/
    ruleset.yaml
    prompts.yaml
    risk_taxonomy.yaml
  fabric_quality/
    ruleset.yaml
    standards.yaml
    prompts.yaml
  legal_contract/
    ruleset.yaml
    clause_library.yaml
    prompts.yaml
```

单条规则建议字段：

```yaml
id: hr.timeline.overlap
name: 任职时间线重叠
domain: hr_recruitment
severity: high
description: 检查候选人简历中不同工作经历是否存在异常重叠。
required_evidence:
  min_count: 2
  types: [date_range, employer]
tools:
  - timeline_conflict_checker
prompt_hint: 提取所有公司名称、职位、起止时间，并检查时间区间是否重叠。
output_schema: audit_finding_v1
```

Rule Engine 职责：

- 加载规则包。
- 按领域、风险等级、文件类型筛选规则。
- 注入 Prompt 片段和工具权限。
- 验证模型输出是否符合该规则的证据要求。

### 4.5 Domain Packages

业务场景作为独立包接入。

#### HR 招聘风控包

能力：

- 简历时间线冲突检测。
- 任职经历与背调信息不一致检测。
- 竞业限制风险识别。
- 学历、证书、项目经历异常描述识别。
- JD 与候选人经历匹配度分析。

工具：

- `ResumeTimelineTool`
- `EnterpriseQueryTool`
- `EducationPatternTool`
- `EmploymentGapTool`

#### 服装质检审计包

能力：

- 质检报告字段完整性检查。
- 面料成分与标签一致性检查。
- GB 18401、GB 31701 等标准条款匹配。
- 供应商资质、批次、检测日期异常检查。
- 高风险化学物质指标阈值审计。

工具：

- `FabricStandardLookupTool`
- `ChemicalLimitCheckerTool`
- `SupplierQualificationTool`
- `BatchConsistencyTool`

#### 合同法务审查包

能力：

- 霸王条款识别。
- 付款、违约、交付、保密、管辖条款风险识别。
- 条款缺失检查。
- 跨境合同中英文关键条款一致性检查。

工具：

- `ClauseRetrieverTool`
- `ContractRiskClassifierTool`
- `BilingualConsistencyTool`
- `JurisdictionCheckerTool`

## 5. 推荐目录结构

后端建议使用 Python，因为 OCR、文档解析、Agent 编排、评测生态更成熟；前端可用 React / Vue。目录示例：

```text
AuditX/
  README.md
  pyproject.toml
  .env.example
  docs/
    architecture.md
    api_contract.md
    evaluation.md
    deployment.md
  backend/
    auditx/
      __init__.py
      main.py
      api/
        __init__.py
        routes_files.py
        routes_audit_jobs.py
        routes_reports.py
        routes_evaluations.py
        schemas.py
        dependencies.py
      application/
        __init__.py
        audit_use_case.py
        document_ingestion_service.py
        audit_job_service.py
        report_service.py
        evaluation_service.py
      domain/
        __init__.py
        documents.py
        audit.py
        evidence.py
        rules.py
        tools.py
        reports.py
        evaluations.py
        errors.py
      document_pipeline/
        __init__.py
        file_loader.py
        text_extractor.py
        ocr_engine.py
        layout_analyzer.py
        reading_order.py
        table_parser.py
        scene_graph.py
        pii_redactor.py
      agent_core/
        __init__.py
        orchestrator.py
        extractor_agent.py
        evaluator_agent.py
        prompt_builder.py
        evidence_validator.py
        finding_normalizer.py
        retry_policy.py
        guardrails.py
      rule_engine/
        __init__.py
        rule_loader.py
        rule_selector.py
        rule_validator.py
      tool_registry/
        __init__.py
        base.py
        registry.py
        schemas.py
      infrastructure/
        __init__.py
        llm/
          base.py
          openai_provider.py
          local_provider.py
        ocr/
          base.py
          paddle_provider.py
        storage/
          database.py
          object_storage.py
          repositories.py
        queue/
          worker.py
          tasks.py
        observability/
          logging.py
          tracing.py
          metrics.py
      domains/
        hr_recruitment/
          __init__.py
          ruleset.yaml
          prompts.yaml
          tools.py
          schemas.py
        fabric_quality/
          __init__.py
          ruleset.yaml
          standards.yaml
          tools.py
          schemas.py
        legal_contract/
          __init__.py
          ruleset.yaml
          prompts.yaml
          tools.py
          schemas.py
      reports/
        templates/
          audit_report.html
      config/
        settings.py
    tests/
      unit/
        test_evidence_validator.py
        test_rule_loader.py
        test_tool_registry.py
        test_timeline_checker.py
      integration/
        test_audit_use_case.py
        test_document_pipeline.py
      evaluation/
        golden_cases/
          hr_case_001/
            input.pdf
            ground_truth.json
        test_evaluation_metrics.py
  frontend/
    package.json
    src/
      app/
      pages/
      components/
        DocumentViewer/
        FindingPanel/
        EvidenceHighlighter/
        AuditTimeline/
        ReportExporter/
      api/
      stores/
      types/
      styles/
  scripts/
    run_dev.ps1
    run_eval.ps1
    seed_demo_data.py
```

## 6. 模块依赖规则

为保证解耦，建议强制遵守以下依赖方向：

```text
api ───────────────► application
application ───────► domain abstractions
document_pipeline ─► domain documents
agent_core ────────► domain + tool_registry abstractions + rule_engine
rule_engine ───────► domain rules
domains/* ─────────► domain + tool_registry
infrastructure ────► implements abstractions
```

禁止：

- `domain` 依赖 `infrastructure`。
- `agent_core` 直接 import 某个 HR 工具实现。
- `api` 层直接调用 OCR SDK、LLM SDK 或第三方查询 SDK。
- `frontend` 直接拼接 Agent Prompt。
- 单个文件同时处理路由、Prompt、工具调用、数据库写入和报告生成。

## 7. 数据流设计

### 7.1 审计任务主流程

```text
用户上传文件
  -> File API 保存原始文件
  -> DocumentIngestionService 创建 Document
  -> AuditJobService 创建 Job
  -> Document Pipeline 解析文档
  -> Rule Engine 加载领域规则
  -> Agent Core 执行 Extractor
  -> Tool Registry 执行必要工具
  -> EvidenceValidator 校验证据
  -> EvaluatorAgent 复核风险
  -> FindingNormalizer 统一结构
  -> ReportService 生成报告
  -> Frontend 展示结果和证据高亮
```

### 7.2 实时事件流

为了提升演示效果和可观测性，后端应向前端推送审计事件。

事件类型：

```text
job.created
document.parsing.started
document.parsing.completed
agent.extractor.started
tool.called
tool.completed
finding.created
finding.rejected
agent.evaluator.completed
report.generated
job.completed
job.failed
```

事件对象建议：

```json
{
  "event_id": "evt_001",
  "job_id": "job_001",
  "type": "tool.called",
  "message": "正在查询候选人前东家工商信息",
  "payload": {
    "tool_name": "enterprise_query"
  },
  "created_at": "2026-05-16T20:00:00+08:00"
}
```

## 8. 测试策略

### 8.1 单元测试

优先覆盖纯逻辑、无外部依赖模块。

重点测试：

- `EvidenceValidator`：不存在页码、错误 block_id、quote 不匹配时必须拒绝。
- `RuleLoader`：规则 YAML 字段缺失、类型错误时必须报错。
- `ToolRegistry`：重复注册、未知工具、输入 schema 不合法时必须报错。
- `TimelineChecker`：日期区间重叠、空缺、格式异常。
- `FindingNormalizer`：模型输出转标准结构。

### 8.2 集成测试

覆盖模块协作，但 mock 外部 API 与 LLM。

重点测试：

- 上传文件后能创建审计任务。
- 解析结果能进入 Agent Core。
- Agent 候选风险无证据时会被剔除。
- 工具超时不会导致整个任务无控制崩溃。
- 报告生成包含风险等级、证据和建议。

### 8.3 评测测试

建立黄金测试集，每个 case 包含：

```text
input.pdf / input.docx
ground_truth.json
expected_findings.json
metadata.json
```

指标：

- `recall`：真实风险中被识别的比例。
- `precision`：输出风险中真实存在的比例。
- `faithfulness`：输出风险中证据可追踪的比例。
- `latency_p50 / latency_p95`：端到端耗时。
- `tool_success_rate`：工具调用成功率。
- `cost_per_document`：单文档模型与工具成本。

必须把 `faithfulness` 作为硬门槛：低于 100% 时，不允许标记该版本为可发布。

## 9. 可扩展性设计

### 9.1 新增业务领域

新增一个领域时，只允许新增 `domains/{domain_name}` 下的规则、Prompt、工具和 schema，原则上不修改 Agent Core。

步骤：

```text
1. 新建 domains/new_domain/ruleset.yaml
2. 新建 domains/new_domain/prompts.yaml
3. 实现该领域需要的 Tool
4. 在 ToolRegistry 注册工具
5. 增加 golden cases
6. 运行评测，观察 recall / precision / faithfulness
```

### 9.2 替换模型

通过 `LLMProvider` 抽象替换模型。

接口保持：

```text
generate(messages, response_schema, temperature, timeout) -> LLMResult
```

不同模型的差异只存在于 `infrastructure/llm`，不能影响 `agent_core`。

### 9.3 替换 OCR / 文档解析

通过 `DocumentParser` 或更细粒度的 `OcrProvider`、`LayoutAnalyzer` 抽象替换底层能力。上层只接收统一的 `ParsedDocument`。

### 9.4 横向扩容

审计任务适合异步化：

- API 服务只负责接收请求。
- Worker 负责 OCR、LLM、工具调用。
- 大文件和报告放对象存储。
- 任务状态和结果放数据库。
- 前端通过轮询或 WebSocket 获取进度。

## 10. 安全与合规设计

必须从第一版就考虑安全，因为系统处理简历、合同、质检报告等敏感文件。

措施：

- 文件上传限制类型、大小、页数。
- 原始文件和解析文本分级存储。
- PII 脱敏后再进入 Prompt，必要时保留映射表。
- 外部 API 调用记录审计日志。
- LLM 请求日志默认不保存完整敏感原文。
- 报告导出加水印和访问权限。
- 每个工具有最小权限，不允许任意网络访问。
- Prompt 中加入禁止编造证据、禁止输出无来源结论的约束。

## 11. 可观测性设计

为了定位问题和优化成本，需要记录结构化日志。

建议追踪：

- 每个审计任务耗时。
- 每个解析阶段耗时。
- 每次 LLM 调用模型、token、耗时、是否重试。
- 每个工具调用入参摘要、结果状态、错误类型。
- 每个风险点从候选到通过 / 驳回的原因。
- 每个版本在黄金测试集上的指标变化。

日志中不要记录完整身份证号、手机号、合同金额等敏感信息，必要时 hash 或脱敏。

## 12. UI 信息架构

建议前端分成四个主区域：

```text
顶部：任务信息、领域选择、上传入口、导出按钮
左侧：文档预览、页码导航、证据高亮
右侧：风险列表、风险等级、置信度、处理建议
底部：Agent 时间线、工具调用记录、评测指标摘要
```

核心组件：

- `DocumentViewer`：展示 PDF / 图片 / 解析文本。
- `EvidenceHighlighter`：根据 bbox 或 block_id 高亮证据。
- `FindingPanel`：展示风险点详情。
- `AuditTimeline`：展示实时事件流。
- `RuleSetSelector`：切换 HR、服装质检、法务合同等规则包。
- `ReportExporter`：导出报告。

UI 不需要展示完整 Chain-of-Thought，只展示可解释的“任务步骤”和“工具调用摘要”，避免泄露模型内部推理。

## 13. 数据库建议

初期可用 SQLite / PostgreSQL。生产更推荐 PostgreSQL。

核心表：

```text
documents
document_pages
layout_blocks
audit_jobs
audit_events
audit_findings
evidences
tool_calls
reports
evaluation_runs
evaluation_cases
evaluation_metrics
```

对象存储：

```text
raw_files/{document_id}/original.pdf
parsed/{document_id}/parsed_document.json
reports/{report_id}/report.pdf
reports/{report_id}/report.html
```

## 14. 第一阶段 MVP 范围

为了快速做出可演示版本，建议第一阶段聚焦 HR 审稿机器人。

MVP 功能：

- 支持上传 PDF / 图片型简历。
- 完成基础 OCR / 文本解析 / 页码保留。
- 支持 HR 规则包。
- 实现时间线冲突、任职经历异常、竞业风险三个核心风险。
- 实现 Extractor + Evaluator 双 Agent。
- 所有风险点必须带证据。
- 前端展示文档、风险列表、证据高亮、Agent 事件流。
- 支持导出 HTML 报告。
- 准备 10 份黄金测试样例。

暂缓功能：

- 不急于支持所有文件格式。
- 不急于做复杂权限系统。
- 不急于接入太多第三方 API。
- 不急于实现完整企业级多租户。
- 不急于把所有行业规则都做完。

## 15. 迭代路线

### Phase 1：HR 审稿 MVP

- 建立后端目录结构和领域模型。
- 实现文档解析最小闭环。
- 实现 HR 规则包和 3 个风险类型。
- 实现证据强校验。
- 实现基础前端看板。
- 建立 10 个 golden cases。

### Phase 2：评测与稳定性

- 扩展 golden cases 到 30 份。
- 增加自动化 recall / precision / faithfulness 计算。
- 增加工具调用 mock 与集成测试。
- 增加任务重试、超时、错误恢复。
- 增加日志、trace、成本统计。

### Phase 3：服装质检领域包

- 新增 `fabric_quality` 规则包。
- 接入国标条款知识库。
- 实现成分、批次、检测项、阈值校验工具。
- 准备质检报告样例和标准答案。
- 复用同一套 Agent Core 与前端看板。

### Phase 4：法务合同领域包

- 新增 `legal_contract` 规则包。
- 实现条款缺失、风险条款、双语一致性检查。
- 支持合同报告模板。
- 增加 RAG 检索法律条款能力。

### Phase 5：生产化

- 支持异步队列和 Worker 横向扩容。
- 增加权限、审计日志、文件生命周期管理。
- 增加模型路由与 fallback。
- 增加灰度发布和版本评测对比。

## 16. 工程约束清单

后续写代码时建议把这些作为硬规则：

- 一个文件只做一类事情。
- 业务规则不写死在 Agent Core。
- Prompt 不散落在各处，统一由规则包或 PromptBuilder 管理。
- 工具不直接生成最终风险结论。
- 没有证据的 finding 一律丢弃。
- 外部 API 必须可 mock。
- LLM Provider 必须可替换。
- 文档解析结果必须保留页码和定位信息。
- 每个新增领域必须配 golden cases。
- 每个核心纯逻辑模块必须有单元测试。

## 17. 建议优先实现的抽象接口

第一批代码可以先围绕这些接口搭骨架：

```text
DocumentParser
RuleProvider
Tool
ToolRegistry
LLMProvider
AgentOrchestrator
EvidenceValidator
FindingRepository
AuditJobRepository
ReportRenderer
EvaluationRunner
```

这些接口稳定后，底层 OCR、模型、工具、数据库、前端都可以并行开发。

## 18. 总结

AuditX 不应被设计成一个“Prompt 脚本项目”，而应被设计成一个“文档解析 + 规则注入 + 工具调用 + 证据校验 + 自动评测”的通用审计中台。HR 场景只是第一个可演示入口，真正的价值在于内核稳定、业务插件可替换、证据链可信、评测指标可量化。

如果后续开始编码，建议优先搭建后端骨架、领域模型、证据校验器、工具注册表和 HR 最小规则包，再逐步补 OCR、LLM、前端和评测流水线。
