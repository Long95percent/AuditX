# 批量筛选外部框架与 Agent 延后交接

## 当前决策

Agent 能力暂时不作为下一阶段主开发目标。

当前更重要的是先把外部系统框架做好：数据库、接口、批量任务、简历库、候选人列表、Top N、详情页、PDF/evidence 复核。Agent 后续可以作为一个可替换的“智能评估执行器”，通过接口读取数据库、写回结果。

## 为什么 Agent 可以延后

最终工作流可以抽象成：

1. OCR / Parser 把简历转成结构化数据和 evidence artifacts。
2. 系统把候选人、简历文本摘要、评分、风险、证据索引写入数据库。
3. 智能评估模块读取数据库，做风险审查、批量对比、智能分级、原因摘要。
4. 智能评估模块把结果写回数据库。
5. UI 和 API 从数据库读取最终结果。

在这个模型里，Agent 不是系统骨架。Agent 只是第 3 步的一个实现方式，可以先用规则服务/接口服务代替，等数据库和 UI 稳定后再替换为更强 Agent。

## 当前系统定位

当前 AuditX 已经具备单份简历审查链路：

- 单份 PDF 进入任务。
- PaddleOCR 解析。
- source PDF、OCR raw、parsed document 写 artifact。
- findings、candidates、score、trace 写 job。
- 前端展示 PDF 和 evidence 高亮。

但当前系统还不是大批量候选人对比系统。它缺少简历库、批量任务、候选人画像表、批量排序和批量 UI。

## 下一阶段优先级

### 第一优先级：数据库模型

先把 OCR 后的信息和审查结果落到可查询数据库，而不是只挂在单个 job payload 里。

需要建模：

- `resumes`：简历入库记录。
- `resume_artifacts`：source PDF、OCR raw、parsed document、导出文件等 artifact refs。
- `parsed_blocks` 或 `evidence_index`：page、block、text、bbox、artifact_uri。
- `candidate_profiles`：候选人结构化画像。
- `review_sessions`：单份审查运行记录。
- `candidate_findings`：正式风险。
- `candidate_scores`：总分、维度分、layer、优势标签、风险数。
- `batches`：批量任务。
- `batch_candidates`：批次内候选人、状态、排名、入围/淘汰原因。

### 第二优先级：接口

先用普通服务接口表达批量筛选工作流，不强依赖 Agent。

需要接口：

- 简历入库。
- 简历列表。
- 简历详情。
- 创建批次。
- 批次加入候选人。
- 批次运行。
- 批次状态。
- 批次 Top N。
- 重算排名。
- 候选人筛选 / 排序 / 聚合。
- evidence lookup。

### 第三优先级：UI

先把外部产品形态做好，让 HR 能操作大批量候选人。

需要页面：

- 简历库列表。
- 候选人结构化信息表。
- 批量任务列表。
- 批次详情页。
- Top N 排名页。
- 筛选面板。
- 候选人详情页。
- PDF/evidence 复核抽屉或详情区。

### 第四优先级：Agent 插槽

暂时只保留 Agent 插槽，不深入开发 Agent 能力。

Agent 后续只需要遵守接口契约：

- 输入：`batch_id`、`job_template_id`、筛选配置、可查询数据库接口。
- 读取：候选人表、分数表、风险表、证据索引、artifact refs。
- 输出：候选人分级、风险摘要、排序原因、淘汰原因、待复核原因。
- 写回：`batch_candidates`、`candidate_findings`、`candidate_scores`、`review_trace` 或专门的 `agent_runs`。

## 后续要修改或新增的文件

### 数据库与领域模型

- 修改：`backend/auditx/domain/resume_library.py`
  - 扩展 `ResumeRecord`。
  - 新增 `CandidateProfile`、`ReviewSessionRecord`、`BatchRecord`、`BatchCandidate`、`EvidenceIndexRecord`。

- 新增：`backend/auditx/infrastructure/storage/resume_repository.py`
  - 保存简历入库记录、artifact refs、状态。

- 新增：`backend/auditx/infrastructure/storage/candidate_repository.py`
  - 保存候选人画像、分数、风险摘要、标签。

- 新增：`backend/auditx/infrastructure/storage/evidence_repository.py`
  - 保存 OCR block/evidence index，支持按候选人、page、block 查询。

- 新增：`backend/auditx/infrastructure/storage/batch_repository.py`
  - 保存批次、批次候选人、排名、入围/淘汰状态。

### Application 服务

- 修改：`backend/auditx/application/audit_use_case.py`
  - 保持单份审查逻辑。
  - 输出可落库的候选人画像、分数、finding、evidence refs。

- 修改：`backend/auditx/application/audit_job_service.py`
  - 单份任务完成后，把结果同步写入 resume/candidate/evidence 相关 repository。
  - 不把批量逻辑塞进 audit job。

- 新增：`backend/auditx/application/resume_library_service.py`
  - 简历入库、查询、状态变更。

- 新增：`backend/auditx/application/batch_review_service.py`
  - 创建批次、添加候选人、运行批次、失败隔离、状态推进。

- 新增：`backend/auditx/application/candidate_query_service.py`
  - 提供筛选、排序、聚合、Top N、百分位过滤。

### API 路由

- 新增：`backend/auditx/api/routes_resumes.py`
  - `POST /api/resumes/import`
  - `GET /api/resumes`
  - `GET /api/resumes/{resume_id}`
  - `GET /api/resumes/{resume_id}/evidence`

- 新增：`backend/auditx/api/routes_batches.py`
  - `POST /api/batches`
  - `POST /api/batches/{batch_id}/candidates`
  - `POST /api/batches/{batch_id}/run`
  - `GET /api/batches/{batch_id}`
  - `GET /api/batches/{batch_id}/top-n`
  - `POST /api/batches/{batch_id}/rerank`

- 新增：`backend/auditx/api/routes_candidates.py`
  - `GET /api/candidates`
  - `GET /api/candidates/{candidate_id}`
  - `POST /api/candidates/query`
  - `POST /api/candidates/aggregate`

- 修改：`backend/auditx/api/dependencies.py`
  - 注入新增 repository/service。

- 修改：`backend/auditx/main.py`
  - 注册新增 routes。

### 前端

- 新增：`frontend/src/api/resumes.ts`
  - 简历库 API client。

- 新增：`frontend/src/api/batches.ts`
  - 批次 API client。

- 新增：`frontend/src/api/candidates.ts`
  - 候选人筛选/聚合 API client。

- 新增：`frontend/src/types/resumeLibrary.ts`
  - 简历、候选人、批次、证据索引类型。

- 新增：`frontend/src/app/ResumeLibraryView.tsx`
  - 简历库列表。

- 新增：`frontend/src/app/BatchReviewView.tsx`
  - 批次详情、运行状态、Top N。

- 新增：`frontend/src/app/CandidateTable.tsx`
  - 候选人表格、筛选、排序、分数、风险、标签。

- 修改：`frontend/src/app/App.tsx`
  - 增加单份审查 / 简历库 / 批量任务导航。

### Agent 延后但保留接口边界

- 暂不新增复杂 `batch_orchestrator`。
- 暂不开发数据库 Agent tool。
- 暂不开发筛选评估 skill。
- 只预留 `agent_runs` 或 `evaluation_runs` 数据表概念，后续 Agent 写回结果时使用。
- 目前批量筛选先由 `candidate_query_service.py` 和普通 API 完成。

## 当前是否支持大批量并行

结论：不支持。

当前是单份审查系统，不是批量并行系统。它具备部分基础：

- OCR artifact。
- parsed document artifact。
- job 持久化。
- score。
- trace。
- PDF evidence 高亮。

但缺少批量系统的核心：

- 没有简历库。
- 没有候选人画像数据库。
- 没有批次表。
- 没有批次状态机。
- 没有并发 worker 或队列。
- 没有批量失败隔离。
- 没有 Top N 批次重算。
- 没有候选人表格筛选/聚合接口。
- 没有面向大批量的前端列表和批次 UI。

## 推荐开发顺序

1. **简历库数据库与 API**
   - 先让所有 OCR 后信息可落库、可查询。

2. **候选人画像与 evidence index**
   - 把 parsed blocks、finding evidence、score 变成可筛选数据。

3. **候选人列表与详情 UI**
   - 做表格、筛选、排序、PDF 复核。

4. **批次与 Top N**
   - 批量任务、Top N、重算、入围/淘汰原因。

5. **并发和失败隔离**
   - 队列、并发数、retry、单份失败不影响批次。

6. **Agent 插入点**
   - 数据库和 UI 稳定后，再把 Agent 替换进 `evaluation_runs` / `batch_review_service`。

