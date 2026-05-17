# Phase 1A 审计最小闭环说明

> 本文档记录当前已经实现的后端审计任务最小闭环。该阶段的目标不是做真实 OCR、真实 LLM 或真实 HR 风控，而是先验证 AuditX / VeriDoc 的工程主干：文档结构化、风险生成、证据校验、结果标准化和 API 返回。

## 1. 当前阶段目标

Phase 1A 跑通以下链路：

```text
POST /api/audit-jobs
  -> AuditJobService.create_and_run(...)
  -> AuditUseCase.run(...)
  -> FakeDocumentParser.parse(...)
  -> FakeExtractor.extract(...)
  -> EvidenceValidator.validate(...)
  -> FindingNormalizer.normalize(...)
  -> AuditJobResponse
```

当前链路使用 fake parser 和 fake extractor，目的是稳定接口和架构边界。

## 2. API 入口

### 2.1 创建审计任务

文件：`backend/auditx/api/routes_audit_jobs.py`

函数：`create_audit_job(...)`

接口：

```text
POST /api/audit-jobs
```

请求：

```json
{
  "file_path": "demo_resume.pdf"
}
```

响应类型：`AuditJobResponse`

当前行为：

- 立即同步执行一次 fake 审计。
- 返回 `job_id`、`status`、`document_id`、`findings`、`rejected_count`。
- 当前 `status` 正常情况下为 `completed`。

后续替换点：

- MVP 后期可以改成异步队列。
- `file_path` 后续应替换成真实上传后的 `file_id` 或 `document_id`。

### 2.2 查询审计任务

文件：`backend/auditx/api/routes_audit_jobs.py`

函数：`get_audit_job(...)`

接口：

```text
GET /api/audit-jobs/{job_id}
```

当前行为：

- 从内存任务表中读取任务。
- 不存在返回 404。

### 2.3 查询风险点

文件：`backend/auditx/api/routes_audit_jobs.py`

函数：`get_audit_job_findings(...)`

接口：

```text
GET /api/audit-jobs/{job_id}/findings
```

当前行为：

- 返回指定任务的 `findings`。
- 不存在返回 404。

## 3. 应用层编排

### 3.1 审计用例

文件：`backend/auditx/application/audit_use_case.py`

类：`AuditUseCase`

函数：`run(file_path: str) -> AuditResult`

当前执行步骤：

1. 调用 `DocumentParser.parse(file_path)` 得到 `ParsedDocument`。
2. 调用 `FindingExtractor.extract(document)` 得到候选 `AuditFinding`。
3. 调用 `EvidenceValidator.validate(finding, document)` 逐条校验证据。
4. 剔除无法匹配文档证据的 finding。
5. 调用 `FindingNormalizer.normalize(...)` 统一排序 / 标准化。
6. 返回 `AuditResult`。

审查重点：

- `AuditUseCase` 只依赖抽象 `DocumentParser` 和 `FindingExtractor`，不依赖具体 OCR 或 LLM SDK。
- 无证据或证据不匹配的 finding 不会进入最终结果。
- 当前 `rejected_count` 会记录被剔除的候选风险数量。

### 3.2 审计任务服务

文件：`backend/auditx/application/audit_job_service.py`

类：`AuditJobService`

核心函数：

- `create_and_run(file_path: str) -> AuditJob`
- `get(job_id: str) -> AuditJob | None`
- `findings(job_id: str) -> list[AuditFinding] | None`

当前存储：

- 使用进程内 `dict[str, AuditJob]` 保存任务。

当前状态：

- `pending`
- `running`
- `completed`
- `failed`

后续替换点：

- 内存 dict 后续应替换成 repository 抽象，再落 PostgreSQL / SQLite。
- 同步执行后续应替换成队列 worker。

## 4. 文档解析层

文件：`backend/auditx/document_pipeline/fake_parser.py`

类：`FakeDocumentParser`

实现接口：`DocumentParser.parse(file_path: str) -> ParsedDocument`

当前输出：

- `document_id`: `fake_doc_001`
- `filename`: 来自传入 `file_path`
- 一页文档。
- 一个 paragraph block：`p1_b1`
- block 带有固定 bbox：`x0=96, y0=180, x1=720, y1=224`

作用：

- 模拟 OCR / layout engine 的输出。
- 让上层先稳定依赖 `ParsedDocument`，未来替换真实解析器时不动上层逻辑。

## 5. Agent Core 层

### 5.1 Extractor 抽象

文件：`backend/auditx/agent_core/extractor.py`

类：`FindingExtractor`

函数：`extract(document: ParsedDocument) -> list[AuditFinding]`

作用：

- 定义候选风险提取器的统一接口。
- 后续真实 LLM Extractor、规则 Extractor、工具 Extractor 都应实现它。

### 5.2 Fake Extractor

文件：`backend/auditx/agent_core/fake_extractor.py`

类：`FakeExtractor`

当前行为：

- 默认生成一个合法 `AuditFinding`。
- 该 finding 的 evidence 指向 `block_id=p1_b1`。
- `quote` 为 `任职于 A 公司`，能在 fake parser 的 block text 中找到。
- `include_invalid_finding=True` 时，会额外生成一个引用 `missing_block` 的无效 finding，用于测试证据剔除。

### 5.3 Evidence Validator

文件：`backend/auditx/agent_core/evidence_validator.py`

类：`EvidenceValidator`

函数：`validate(finding, document) -> bool`

当前校验：

- evidence 的 `block_id` 必须存在于文档 blocks。
- evidence 的 `page_number` 必须和 block 页码一致。
- evidence 的 `quote` 必须出现在 block text 中。

后续应增强：

- 校验 `evidence.document_id == document.document_id`。
- 校验 bbox 是否落在页面尺寸范围内。
- 校验 bbox 与 block bbox 的关系。
- 校验 quote offset。

### 5.4 Finding Normalizer

文件：`backend/auditx/agent_core/finding_normalizer.py`

类：`FindingNormalizer`

函数：`normalize(findings) -> list[AuditFinding]`

当前行为：

- 按 `risk_level.value` 和 `finding_id` 做稳定排序。

后续可扩展：

- 风险等级排序权重。
- 去重。
- 合并同类 finding。
- 输出字段清洗。

## 6. 领域模型

### 6.1 审计结果

文件：`backend/auditx/domain/results.py`

类型：`AuditResult`

字段：

- `document: ParsedDocument`
- `findings: list[AuditFinding]`
- `rejected_count: int`

### 6.2 既有强约束模型

文件：`backend/auditx/domain/audit.py`

关键约束：

- `AuditFinding.evidences` 至少一条。
- `Evidence.bbox` 必填。
- `confidence` 必须在 0 到 1 之间。

文件：`backend/auditx/domain/documents.py`

关键约束：

- `BBox.x1 > x0`
- `BBox.y1 > y0`
- page number 必须从 1 起。

## 7. 测试覆盖

### 7.1 用例闭环测试

文件：`backend/tests/integration/test_audit_use_case.py`

覆盖：

- `AuditUseCase` 能从 fake document 生成一个 evidence-backed finding。
- 无效 finding 会被 evidence validator 剔除。

### 7.2 API 闭环测试

文件：`backend/tests/integration/test_audit_jobs_api.py`

覆盖：

- `POST /api/audit-jobs` 能创建并完成任务。
- `GET /api/audit-jobs/{job_id}` 能查到任务。
- `GET /api/audit-jobs/{job_id}/findings` 能查到风险点。

### 7.3 运行命令

当前环境如果 `uv` 拉依赖受网络限制，可先使用系统 Python：

```powershell
python -m pytest backend/tests/unit backend/tests/integration -q
```

如果依赖已通过 uv 同步完成：

```powershell
$env:UV_CACHE_DIR = ".uv-cache"
uv run pytest backend/tests/unit backend/tests/integration -q
```

## 8. 当前明确不包含的内容

本阶段没有实现：

- 真实文件上传。
- 真实 OCR。
- 真实 PDF bbox 解析。
- 真实 LLM Extractor / Evaluator。
- 真实 Tool Registry 工具调用。
- 数据库存储。
- 异步任务队列。
- 前端 API 对接。
- Tauri sidecar 启动 Python 后端。

这些都应该在 Phase 1B 之后逐步接入。

## 9. 下一阶段建议

Phase 1B 建议做：

1. 给 `EvidenceValidator` 增加 document_id 与 bbox 页面范围校验。
2. 抽象 `AuditJobRepository`，把内存 dict 从 service 中拆出去。
3. 增加 `GET /api/audit-jobs/{job_id}/events` 的事件流骨架。
4. 前端接入当前 audit jobs API，但仍使用 fake 审计结果。
5. 设计真实上传接口 `POST /api/files`，但可以先保存到本地 `.data/`。
