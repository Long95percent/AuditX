# AuditX 简历审查 MVP 12 天执行计划

> 本计划替代旧版“全量铺开”的 12 天计划。  
> 核心策略：先完成最小真实 MVP，再进入小批量、列表页、Top N、分级压测。  
> 判断标准：每天必须同时满足“功能产出 + 自动化测试/手工验收 + 可记录结果”，否则不进入下一阶段。

## 1. 计划目标

用 12 天完成一个可演示、可测试、可继续扩展的简历审查 MVP。

MVP 必须真实闭环：

```text
本地简历 / fake parser
  -> 结构化简历最小字段
  -> 岗位模板
  -> AgentOrchestrator
  -> LLM mock + 规则工具
  -> FindingCandidate
  -> evidence 校验
  -> 正式风险 / rejected candidates
  -> scoring signals
  -> ScoreResult + CandidateLayer
  -> ReviewTrace
  -> API 返回
  -> 前端展示
```

当前 12 天不追求完整企业系统，不追求 10 万历史库，不追求真实网页搜索。

## 2. 设计文档链接

执行本计划前，必须先阅读以下设计文档：

1. `docs/plans/agent_first_routing_design.md`
   - `AgentOrchestrator` 是唯一审查主入口。
   - 规则是工具，不是总路由。
   - `FindingCandidate`、正式风险、`ReviewTrace` 的边界。
   - 工具失败、Agent 失败和证据失败的降级方式。

2. `docs/plans/resume_review_scoring_and_presentation_design.md`
   - 简历库输入、已筛查简历复用、当前批次重算。
   - 评分维度、候选人分层、Top N 选择规则。
   - HR 列表页、详情页、风险和证据展示。
   - 测试数据、黄金测试集和 5000 份压测目标。

3. `docs/plans/resume_review_product_flow.drawio`
   - 产品流程图。
   - 后续实现列表页、详情页、批量任务时参考。

4. `docs/suggestions/2026-05-19-architecture-review-baseline.md`
   - 架构审查红线。
   - 后续代码审查标准。

5. `docs/suggestions/2026-05-19-mvp-first-plan-and-12-day-review.md`
   - 为什么先做最小真实 MVP。
   - 为什么旧版 12 天计划不能继续硬推。

## 3. 执行原则

- 先完成真实 MVP，再扩展批量能力。
- 不允许评分输入硬编码在 `AuditUseCase`。
- 不允许 API route、规则或前端绕过 `AgentOrchestrator`。
- 不允许无证据候选进入正式风险。
- 不允许只写 worklog / acceptance 文档而没有测试或可运行验收。
- 每天结束必须跑当天相关测试；阶段结束必须跑后端全量测试和前端 build。
- 12 天内证据链接先用简历原文和本地模拟文件，不做真实网页搜索。
- 压测采用分级策略：100 -> 500 -> 1000 -> 5000，不直接跳到 5000。

## 4. 当前代码已具备的基础

当前已有基础能力：

- `backend/auditx/agent_core/orchestrator.py`：已有 `AgentOrchestrator` 雏形。
- `backend/auditx/domain/review.py`：已有 `FindingCandidate`、`ReviewTrace` 雏形。
- `backend/auditx/agent_core/llm_candidate_tool.py`：已有 LLM mock candidate 工具。
- `backend/auditx/agent_core/rule_tools.py`：已有部分基础规则工具。
- `backend/auditx/domain/scoring.py`：已有评分和 Top N 雏形。
- `frontend/src/app/App.tsx`：已有单份 fake audit 展示页面。

但当前仍有阻断缺口：

- Day 1 数据契约不完整。
- `AgentOrchestrator.review()` 只接收 `document`，缺少岗位模板和上下文。
- `AuditUseCase` 中评分输入仍有演示硬编码。
- 规则工具和 scoring signal 没有完整打通。
- 简历库状态、批量任务、黄金测试集和压测尚未完成。

## 5. 12 天安排

### Day 1：补齐 MVP 数据契约

目标：把后续所有链路依赖的数据结构先定稳。

任务：

- 定义 `ResumeStatus`：`new`、`reviewed`、`shortlisted`。
- 定义 `ResumeRecord`：简历 ID、文件名、入库时间、状态、解析结果引用。
- 定义 `ReviewContext`：岗位模板、运行配置、历史上下文、是否复用解析结果。
- 扩展 `JobTemplate`：硬性要求、优势词典、权重、风险策略、模板版本。
- 补齐 3 个岗位模板样例：前端、财务、产品经理。
- 明确结果对象：分数、分层、优势、风险、证据、计算明细、trace、rejected candidates。

建议修改文件：

- `backend/auditx/domain/scoring.py`
- `backend/auditx/domain/review.py`
- `backend/auditx/domain/results.py`
- 可新增 `backend/auditx/domain/resume_library.py`

测试：

- `JobTemplate` 必须包含硬性要求、风险策略和模板版本。
- 三个岗位模板 ID 不同，权重和优势词典不同。
- `ResumeStatus` 状态枚举完整。
- `ReviewContext` 能携带岗位模板和复用开关。

产出：

- MVP 数据契约。
- 三个岗位模板样例。
- 数据契约单元测试。

### Day 2：扩展 AgentOrchestrator 输入和上下文

目标：让主路由从 `document -> draft` 升级为 `document + job_template + context -> draft`。

任务：

- 修改 `AgentOrchestrator.review()`，接收 `document`、`job_template`、`context`。
- 统一工具输入：`document`、`job_template`、`context`。
- 修改 LLM mock 工具和规则工具，使其适配统一输入。
- 修改 `AuditUseCase`，只负责 parser + orchestrator + result assembly。
- 保证 API route 不直接调用规则、Agent 或具体工具。

建议修改文件：

- `backend/auditx/agent_core/orchestrator.py`
- `backend/auditx/agent_core/llm_candidate_tool.py`
- `backend/auditx/agent_core/rule_tools.py`
- `backend/auditx/application/audit_use_case.py`
- `backend/auditx/api/dependencies.py`

测试：

- 调用审查流程必然产生 `ReviewTrace`。
- trace 中能看到 LLM mock 和规则工具 step。
- 工具失败不影响整份审查。
- `AdvantageDictionaryTool` 能通过 orchestrator 拿到 `job_template`。

产出：

- 带上下文的 Agent 主链路。
- 不绕过 orchestrator 的路由测试。

### Day 3：打通候选发现和 evidence gate

目标：让 LLM mock 和规则工具都统一产出候选，再通过证据门禁进入正式风险。

任务：

- 统一 LLM mock、规则工具输出为 `FindingCandidate`。
- 补 rejected candidate 的拒绝原因字段或 trace metadata。
- 未通过 evidence 校验的候选进入 rejected candidates。
- 正式 findings 必须全部经过 `EvidenceValidator`。
- 本地简历原文 evidence 支持 quote、block、bbox。

建议修改文件：

- `backend/auditx/domain/review.py`
- `backend/auditx/agent_core/orchestrator.py`
- `backend/auditx/agent_core/evidence_validator.py`
- `backend/auditx/agent_core/llm_candidate_normalizer.py`

测试：

- LLM mock 返回有证据候选时，可转正式风险。
- LLM mock 返回无证据候选时，被拒绝但 trace 可见。
- 规则候选无证据时不能进入正式 findings。
- rejected candidates 保留来源和拒绝原因。

产出：

- 候选发现端到端链路。
- evidence gate 测试。

### Day 4：去掉评分硬编码，接入 scoring signals

目标：评分结果来自岗位模板、规则输出、Agent output 和正式风险，而不是写死在 `AuditUseCase`。

任务：

- 定义 `ScoringSignal` 或等价结构。
- 让优势词典、关键词命中、硬性要求相关规则输出 scoring signals。
- 从 `FindingCandidate`、正式 findings 和 scoring signals 生成 `CandidateScoreInput`。
- 删除 `AuditUseCase` 中固定的 `hard_requirement_match=0.75`、`ability_match=0.8`、固定 advantage signals。
- 计算明细要能追溯到 signal、规则或 Agent step。

建议修改文件：

- `backend/auditx/domain/scoring.py`
- `backend/auditx/agent_core/rule_tools.py`
- `backend/auditx/agent_core/orchestrator.py`
- `backend/auditx/application/audit_use_case.py`

测试：

- 同一简历在不同岗位模板下 score 或 advantage tags 不同。
- 风险数量影响扣分。
- 硬性要求低分但不自动淘汰。
- 计算明细包含 signal 来源。
- 代码中不再存在演示硬编码评分输入。

产出：

- 真实评分链路第一版。
- 评分与 signal 测试。

### Day 5：单份简历 MVP 前端闭环

目标：完成可演示的单份简历审查详情页。

任务：

- 前端展示 score、layer、dimension scores、advantage tags。
- 展示正式 findings 和 rejected candidates。
- 展示 evidence quote、page、block、bbox。
- 展示 ReviewTrace：Agent、规则、工具、evidence gate 状态。
- API response schema 与前端类型保持一致。
- 编写 MVP 手工验收说明。

建议修改文件：

- `backend/auditx/api/schemas.py`
- `frontend/src/types/audit.ts`
- `frontend/src/app/App.tsx`
- `frontend/src/styles/global.css`
- 可新增 `docs/acceptance/day5-single-resume-mvp.md`

测试：

- API 集成测试断言返回 score、layer、findings、rejected candidates、trace。
- 前端 `npm.cmd --prefix frontend run build` 通过。
- 手工验收单份简历详情页可解释。

产出：

- 最小真实 MVP。
- 单份简历审查演示闭环。

### Day 6：MVP 集成测试和缺口修复

目标：不新增大功能，专门验证 Day 1-5 真实闭环。

任务：

- 跑后端全量测试。
- 跑前端 build。
- 检查所有正式风险都有 evidence。
- 检查 trace 是否覆盖 LLM mock、规则工具、evidence gate、评分。
- 修复 Day 1-5 遗留缺口。
- 整理 MVP 已知限制。

测试：

- `python -m pytest backend\tests -q -p no:cacheprovider`
- `npm.cmd --prefix frontend run build`
- 手工跑一次桌面/浏览器 MVP 流程。

产出：

- MVP 集成测试记录。
- 已知限制清单。
- 是否进入批量阶段的 go / no-go 结论。

### Day 7：测试数据生成器和小型黄金集

目标：先有稳定测试数据，再做批量和 Top N。

任务：

- 实现测试简历数据生成器。
- 生成覆盖三层候选人的样本：最优、次优但有潜力、不建议。
- 建立小型黄金集：每个岗位至少 5 份，后续再扩到 20 份。
- 标注预期分层、主要优势、主要风险和关键证据。
- 黄金集结果可导出或快照比较。

建议新增文件：

- `backend/auditx/testing/resume_factory.py`
- `backend/tests/golden/` 或 `backend/tests/fixtures/golden/`
- `backend/tests/integration/test_golden_resume_set.py`

测试：

- 生成数据字段完整。
- 黄金集能稳定跑通。
- 修改评分权重后，测试能发现分层变化。

产出：

- 测试数据生成器。
- 小型黄金测试集。

### Day 8：简历库状态和输入筛选

目标：实现最小简历库模型，为列表页和批量任务做准备。

任务：

- 实现内存版 `ResumeRepository` 或等价存储接口。
- 支持 `new`、`reviewed`、`shortlisted` 状态。
- 支持按入库时间排序。
- 支持只看新简历。
- 审查完成后状态从 `new` 变为 `reviewed`。
- 已筛查简历再次输入时允许复用解析结果，但当前岗位 score 需要重算。

建议新增/修改文件：

- `backend/auditx/domain/resume_library.py`
- `backend/auditx/application/resume_library_service.py`
- `backend/tests/unit/test_resume_library.py`
- `backend/tests/integration/test_reviewed_resume_reuse.py`

测试：

- 新入库简历可按时间排序。
- 只看新简历筛选正确。
- 审查完成后状态更新。
- 已筛查简历复用解析结果但重算 score。

产出：

- 最小简历库能力。
- 状态流转测试。

### Day 9：HR 列表页和详情页第一版

目标：让 HR 能从简历库选择输入，并查看结果列表和详情。

任务：

- 后端提供简历列表 API。
- 后端提供审查结果详情 API。
- 前端列表展示：姓名/文件名、状态、岗位、分层、总分、优势标签、风险数量。
- 支持按时间排序和只看新简历两个预定义筛选。
- 详情页复用 Day 5 单份展示。

建议修改文件：

- `backend/auditx/api/routes_audit_jobs.py`
- 可新增 `backend/auditx/api/routes_resumes.py`
- `frontend/src/api/auditJobs.ts`
- `frontend/src/app/App.tsx`
- `frontend/src/types/audit.ts`

测试：

- 列表 API 可返回状态和排序结果。
- 前端 build 通过。
- 手工验收列表筛选和详情一致性。

产出：

- HR 列表页第一版。
- 简历详情页第一版。

### Day 10：批量任务和 Top N 当前批次排序

目标：实现小批量处理，不直接追求 5000。

任务：

- 定义 `BatchReviewJob` 和单份任务状态：待处理、解析中、审查中、完成、失败。
- 支持单批 100 份测试数据处理。
- 单份失败不影响整批。
- 失败任务记录失败原因。
- 实现当前批次 Top N：默认 N=20，HR 可传 N。
- Top N 并列规则：风险更少优先、优势更多优先、入库时间更新优先。

建议新增/修改文件：

- `backend/auditx/domain/batch.py`
- `backend/auditx/application/batch_review_service.py`
- `backend/tests/integration/test_batch_review.py`
- `backend/tests/unit/test_top_n_current_batch.py`

测试：

- 单批 100 份可完成。
- 失败任务可追踪。
- 自定义 N 生效。
- 输入少于 N 时全选。
- 非法 N 返回错误。

产出：

- 批量任务第一版。
- 当前批次 Top N。

### Day 11：本地证据库和分级压测

目标：补本地模拟公司证据，并跑 100/500/1000 分级压测。

任务：

- 建立本地公司模拟库。
- 风险证据支持 `local://evidence/company_mock_db.json#...`。
- 模糊公司名生成风险候选。
- 白名单公司不误报高风险。
- 公司库查询失败降级为不确定提示。
- 跑 100、500、1000 份分级压测。
- 记录耗时、失败率、任务积压、列表响应情况。

建议新增/修改文件：

- `backend/auditx/agent_core/company_evidence_tool.py`
- `backend/auditx/domains/hr_recruitment/company_mock_db.json`
- `backend/tests/integration/test_company_evidence_tool.py`
- `docs/acceptance/day11-scaled-pressure-test.md`

测试：

- 本地证据链接可生成。
- 模糊公司名风险可降级处理。
- 100/500/1000 压测有结果记录。

产出：

- 本地证据链。
- 分级压测报告。

### Day 12：5000 份压测和演示验收

目标：完成最终演示版本和回归验收。

任务：

- 跑完整后端测试。
- 跑前端 build。
- 跑黄金测试集。
- 准备演示数据：最优、次优但有潜力、不建议各若干份。
- 如 Day 11 的 1000 份压测稳定，再跑 5000 份累计处理测试。
- 如果 1000 份不稳定，不强行宣称 5000 完成，记录阻断原因。
- 整理已知限制和下一阶段计划。

测试：

- 后端单元测试。
- Agent 路由测试。
- 端到端审查测试。
- 黄金测试集回归。
- 关键 UI 手工验收。
- 5000 份压测或阻断报告。

产出：

- 可演示版本。
- 回归测试结果。
- 压测报告。
- 已知问题和下一阶段清单。

## 6. 阶段验收门槛

### MVP 门槛，Day 6 必须满足

- 单份简历能输出分层、优势、风险、证据和计算明细。
- `ReviewTrace` 能说明调用了哪些 Agent、规则和工具。
- 无证据候选不会进入正式风险。
- 同一份简历在不同岗位模板下有不同匹配结果。
- 评分输入不再硬编码在 `AuditUseCase`。
- 前端能展示 score、layer、findings、rejected candidates、evidence、trace。

### 批量门槛，Day 10 必须满足

- 简历状态可区分 `new`、`reviewed`、`shortlisted`。
- HR 可按时间排序或只看新简历。
- 批量任务支持单份失败隔离。
- 当前批次 Top N 可重算。
- 自定义 N、非法 N、小于 N 都有测试。

### 最终门槛，Day 12 必须满足

- 黄金测试集能稳定回归。
- 本地证据链接可展示。
- 压测有结果、失败可追踪。
- 已知限制明确记录。
- 不把未完成的 5000 压测写成完成。

## 7. 不做事项

- 不做真实网页搜索。
- 不做生产级公司背景调查。
- 不做 10 万实时压测。
- 不做复杂权限和团队协作。
- 不做真实企业级持久化方案；当前可以先用内存或轻量本地文件，但接口要可替换。
- 不让规则路由绕过 `AgentOrchestrator`。

## 8. 每日记录要求

每天完成后必须更新 worklog 或 acceptance 文档，记录：

- 当天完成的文件。
- 当天新增/修改的测试。
- 实际运行的命令和结果。
- 未完成项和阻断原因。
- 是否允许进入下一天。

建议 acceptance 文件命名：

```text
docs/acceptance/dayN-<topic>.md
```

如果当天测试未通过，不得把失败链路继续堆到后续天数。
