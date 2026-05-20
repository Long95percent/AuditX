# AuditX 批量筛选系统体系与下一阶段实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 AuditX 从单份简历审查闭环推进到具备清晰边界的批量候选人筛选系统骨架。

**Architecture:** 保持现有单份 `AuditJob` 链路稳定，新增简历库、候选人画像、证据索引、批次、排名筛选等独立模块。Agent 暂时只作为后续可替换评估执行器插槽，不进入本阶段主线。

**Tech Stack:** Python/FastAPI/Pydantic/SQLite repository seam、filesystem artifact store、React/TypeScript、PaddleOCR artifact 链路。

---

## 1. 当前执行阶段

当前阶段不是继续加深 Agent 能力，而是完成批量筛选系统的外部框架设计与实施顺序拆分。

- 当前已有：单份 PDF 审查、PaddleOCR、parsed document artifact、finding/evidence/score/trace、PDF evidence 高亮。
- 当前没有：简历库、候选人画像持久化、批次任务、批次候选人、Top N 批量排序、失败隔离、并发 worker、批量 UI。
- 当前原则：不能把批量逻辑塞进单份 `AuditJob` payload，不能把大对象塞进数据库主表，不能声称已经支持大批量并行。

## 2. 本次范围

本阶段先完成系统体系、模块职责、接口方向和实施顺序，不直接落数据库表。

- 梳理单份审查、简历库、候选人画像、批量任务、证据索引、排名筛选、前端工作台、Agent 插槽边界。
- 定义每个模块当前状态：已有、雏形、计划新增、延后。
- 给出下一阶段按 TDD 推进的任务顺序。
- 明确真实交付、mock 边界、验证方式。

## 3. 不做范围

- 不开发 Agent 自主规划能力。
- 不开发复杂 prompt、skill、database agent tool。
- 不把所有简历全文塞进 Agent 上下文。
- 不把 batch 塞进 `AuditJob.payload`。
- 不在数据库设计前跳写零散表。
- 不破坏现有单份审查链路。

## 4. 模块体系与边界

### 4.1 单份审查模块

**状态：已有，继续保护。**

职责：处理一份简历从文档解析到 finding、score、trace、artifact refs 的完整审查链路。

边界：

- 输入是单个本地文档路径或单份上传文件。
- 输出是单份 `AuditResult`、`AuditJob`、artifact refs。
- 不负责批次状态、候选人排名、Top N、批量失败隔离。

关键文件：

- `backend/auditx/application/audit_use_case.py`
- `backend/auditx/application/audit_job_service.py`
- `backend/auditx/api/routes_audit_jobs.py`

### 4.2 简历库模块

**状态：领域雏形已有，repository/API/UI 待新增。**

职责：承载 OCR 后可长期查询的简历记录和 artifact 引用。

边界：

- 保存简历元信息、状态、来源、创建时间、最近审查时间。
- 保存 source PDF、OCR raw、parsed document 等 artifact refs。
- 不保存大对象正文。
- 不承担批次排序逻辑。

建议对象：

- `ResumeRecord`
- `ResumeArtifactRef`
- `ResumeStatus`

### 4.3 候选人画像模块

**状态：计划新增。**

职责：将单份审查结果沉淀为可筛选、可排序、可复核的候选人结构化数据。

边界：

- 从 parsed document、finding、score、trace 摘要中抽取候选人画像。
- 支持候选人列表、详情、标签、风险数、分层、最近审查状态。
- 不直接保存 OCR 全文。
- 不直接调用 Agent。

建议对象：

- `CandidateProfile`
- `CandidateScoreRecord`
- `CandidateFindingRecord`
- `CandidateReviewSummary`

### 4.4 证据索引模块

**状态：artifact 链路已有，结构化索引待新增。**

职责：把 parsed blocks、finding evidence、PDF bbox 变成可查询证据索引。

边界：

- 数据库只保存 page、block id、bbox、text excerpt、artifact uri、hash 等轻量索引。
- OCR raw、parsed document、原始 PDF 继续放 artifact store。
- 支持按候选人、finding、page、block 查询。
- 支持前端 PDF 精准高亮复核。

建议对象：

- `EvidenceIndexRecord`
- `ParsedBlockIndex`
- `FindingEvidenceLink`

### 4.5 批量任务模块

**状态：计划新增。**

职责：表达一次岗位/筛选配置下的候选人批量评估任务。

边界：

- `BatchRecord` 只描述批次元信息、状态、配置、统计。
- `BatchCandidate` 只描述候选人在当前批次内的状态、排名、入围/淘汰原因。
- 批次引用 resume/candidate，不复制单份审查 payload。
- 单个候选人失败不应导致整个批次失败。

建议对象：

- `BatchRecord`
- `BatchCandidate`
- `BatchRunConfig`
- `BatchStatus`

### 4.6 排名与筛选模块

**状态：评分和 TopN 算法雏形已有，批量查询服务待新增。**

职责：对候选人集合进行筛选、排序、Top N、入围/淘汰解释。

边界：

- 排名输入来自候选人画像、分数、风险、证据摘要、岗位模板。
- 输出写回 batch candidate 或 ranking result。
- 不直接调用 OCR，不读取完整 PDF，不依赖 Agent 自主规划。

建议对象：

- `CandidateQuery`
- `CandidateRankingResult`
- `TopNSelection`
- `EliminationReason`

### 4.7 前端工作台模块

**状态：单份审查 UI 已有，批量工作台待新增。**

职责：让 HR 能从简历库、候选人表格、批次详情、Top N、PDF/evidence 复核完成筛选工作。

边界：

- 单份审查页继续保留。
- 新增简历库、候选人列表、批次列表、批次详情、候选人详情。
- 不在前端伪造批量并行状态。
- 前端只展示 API 返回的真实状态。

### 4.8 Agent 插槽模块

**状态：延后，仅保留接口概念。**

职责：后续作为智能评估执行器读取结构化数据并写回评估结果。

边界：

- 输入：`batch_id`、岗位模板、筛选配置、候选人查询接口。
- 读取：候选人画像、分数、风险、证据索引、artifact refs。
- 输出：分级、风险摘要、排序原因、淘汰原因、待复核原因。
- 写回：`evaluation_runs`、`batch_candidates`、`candidate_scores`、`candidate_findings`。
- 当前不开发复杂 tool runtime。

## 5. 下一阶段开发顺序

### Task 1: 固化批量系统领域契约

**Files:**
- Create: `backend/tests/unit/test_batch_domain_contracts.py`
- Create: `backend/auditx/domain/candidate.py`
- Create: `backend/auditx/domain/batch.py`
- Create: `backend/auditx/domain/evidence_index.py`

- [ ] Step 1: 先写领域对象测试，覆盖候选人画像、批次状态、证据索引的最小字段和不可变边界。
- [ ] Step 2: 运行定向测试，确认因为对象不存在而失败。
- [ ] Step 3: 新增最小 Pydantic/Enum 领域对象，不接数据库。
- [ ] Step 4: 运行定向测试通过。

### Task 2: 定义 repository seam，不落复杂 schema

**Files:**
- Create: `backend/tests/unit/test_resume_repository_contract.py`
- Create: `backend/tests/unit/test_candidate_repository_contract.py`
- Create: `backend/tests/unit/test_batch_repository_contract.py`
- Create: `backend/auditx/infrastructure/storage/resume_repository.py`
- Create: `backend/auditx/infrastructure/storage/candidate_repository.py`
- Create: `backend/auditx/infrastructure/storage/batch_repository.py`

- [ ] Step 1: 先写 repository contract 测试，覆盖 create/get/list/status update。
- [ ] Step 2: 先用 in-memory repository 跑通 contract，避免过早陷入 schema 细节。
- [ ] Step 3: 明确 artifact refs 只保存轻量引用。
- [ ] Step 4: 保证 repository 不接受完整 OCR raw、完整 parsed document、完整 PDF bytes。

### Task 3: 新增简历库 application service

**Files:**
- Create: `backend/tests/unit/test_resume_library_service.py`
- Create: `backend/auditx/application/resume_library_service.py`

- [ ] Step 1: 测试简历入库只写元信息和 artifact refs。
- [ ] Step 2: 测试简历列表支持状态过滤和分页参数。
- [ ] Step 3: 测试简历详情能返回最新审查摘要引用。
- [ ] Step 4: 实现最小 service，不调用 Agent，不复制 job payload。

### Task 4: 新增候选人查询 service

**Files:**
- Create: `backend/tests/unit/test_candidate_query_service.py`
- Create: `backend/auditx/application/candidate_query_service.py`

- [ ] Step 1: 测试按 layer、risk count、score range、keyword/tag 查询。
- [ ] Step 2: 测试排序字段只使用结构化摘要。
- [ ] Step 3: 测试 Top N 使用批次候选人分数和风险，不读取完整 artifact。
- [ ] Step 4: 实现最小 query service。

### Task 5: 新增批次 service

**Files:**
- Create: `backend/tests/unit/test_batch_review_service.py`
- Create: `backend/auditx/application/batch_review_service.py`

- [ ] Step 1: 测试创建批次、添加候选人、查询批次详情。
- [ ] Step 2: 测试单个候选人失败只更新该 `BatchCandidate` 状态。
- [ ] Step 3: 测试批次 Top N 结果可重算。
- [ ] Step 4: 实现最小批次状态机，不做并发 worker。

### Task 6: 新增 API 边界

**Files:**
- Create: `backend/tests/integration/test_resumes_api.py`
- Create: `backend/tests/integration/test_candidates_api.py`
- Create: `backend/tests/integration/test_batches_api.py`
- Create: `backend/auditx/api/routes_resumes.py`
- Create: `backend/auditx/api/routes_candidates.py`
- Create: `backend/auditx/api/routes_batches.py`
- Modify: `backend/auditx/api/dependencies.py`
- Modify: `backend/auditx/main.py`

- [ ] Step 1: 先写 API contract 测试，覆盖列表、详情、创建批次、Top N。
- [ ] Step 2: 实现 routes，只调用 application service。
- [ ] Step 3: 保持 `routes_audit_jobs.py` 仍只负责单份审查。
- [ ] Step 4: 确认 API 响应不包含大对象。

### Task 7: 新增前端信息架构骨架

**Files:**
- Create: `frontend/src/api/resumes.ts`
- Create: `frontend/src/api/candidates.ts`
- Create: `frontend/src/api/batches.ts`
- Create: `frontend/src/types/resumeLibrary.ts`
- Create: `frontend/src/app/ResumeLibraryView.tsx`
- Create: `frontend/src/app/CandidateTable.tsx`
- Create: `frontend/src/app/BatchReviewView.tsx`
- Modify: `frontend/src/app/App.tsx`

- [ ] Step 1: 新增 API client 和类型，字段与后端 contract 对齐。
- [ ] Step 2: 新增简历库列表、候选人表格、批次详情空态/加载态/错误态。
- [ ] Step 3: 在主页面增加导航，但保留现有单份审查页。
- [ ] Step 4: 不展示不存在的并发 worker、压测能力、批量完成能力。

### Task 8: SQLite schema 与迁移策略

**Files:**
- Modify: `backend/auditx/infrastructure/storage/resume_repository.py`
- Modify: `backend/auditx/infrastructure/storage/candidate_repository.py`
- Modify: `backend/auditx/infrastructure/storage/batch_repository.py`
- Test: corresponding repository tests

- [ ] Step 1: 在 repository contract 稳定后再新增 SQLite 表。
- [ ] Step 2: 表只保存结构化摘要和 artifact refs。
- [ ] Step 3: 保证现有 `audit_jobs` 数据不需要破坏性迁移。
- [ ] Step 4: 回归运行后端测试。

## 6. 验证方式

每个代码任务必须先写测试再实现。

推荐验证顺序：

```powershell
$env:AUDITX_OCR_PROVIDER='fake'
$env:UV_CACHE_DIR='.uv-cache'
uv run pytest backend/tests/unit/test_batch_domain_contracts.py -q -p no:cacheprovider
uv run pytest backend/tests -q -p no:cacheprovider
npm.cmd --prefix frontend run build
```

## 7. Mock 与延后边界

- LLM 真实调用仍延后，API key 由用户后续配置。
- Agent 复杂推理、tool runtime、database tool、skill prompt 延后。
- 并发 worker、队列、失败重试、压测报告延后到批次状态机稳定后。
- 真实大批量能力必须等批次、队列、失败隔离、Top N、压测证据齐备后才能宣称支持。
- OCR raw、parsed document、PDF、LLM response、压测报告等大对象继续进入 artifact store。

## 8. 交付红线

- 不破坏当前单份审查链路。
- 不让 API route、前端或规则绕过当前单份审查主入口生成正式结论。
- 不把完整简历全文、OCR raw、parsed document 放进 `AuditJob.payload` 或批次主表。
- 不在没有压测证据前声称支持大批量并行。
- 不跳过 TDD。
