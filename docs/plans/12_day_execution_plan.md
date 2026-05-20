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

## 1.1 产品定位和交付红线

AuditX 的产品定位不是“AI 读简历 demo”，而是 **Agent 主导的智能简历初筛工作台**。

它要解决的真实业务问题是：HR 面对大量简历时，能快速知道谁最值得先看、为什么值得看、风险在哪里、证据在哪里、AI 做了哪些判断。

因此，12 天计划内允许使用 MVP 方式逐步搭建和测试，但每天交付给用户的代码必须是可继续演进的真实业务代码，不允许只搭假页面或不可维护 demo。

交付红线：

- 可以用 mock LLM 或 fake parser 做阶段验证，但必须标明 mock 边界和替换位置。
- 后端必须有真实 API / service / domain contract，不能只在前端写假数据。
- 审查任务、结果和 trace 必须能持久化，不能只放进进程内内存。
- 风险结论必须有证据，不能让 LLM 直接编正式风险。
- AgentOrchestrator 是审查主入口，API、规则、前端不能绕过它各自生成结论。
- 大对象必须进入 artifact store，不能无限塞进 `audit_jobs.payload`。
- 每天必须能说明：当前是 Day 几，完成了哪条任务，哪些是真实业务代码，哪些仍是 mock。

产品完整方案见：`docs/plans/product_blueprint_resume_screening.md`。

## 2. 设计文档链接

执行本计划前，必须先阅读以下设计文档。AI 开始任何实现前，必须先声明自己正在执行 Day 几，并引用对应任务。

1. `docs/plans/product_blueprint_resume_screening.md`
   - 产品定位、买点、用户场景和真实业务交付标准。
   - Agent、证据、视觉定位、风险数据源、存储和压测的整体产品方案。

2. `docs/plans/agent_first_routing_design.md`
   - `AgentOrchestrator` 是唯一审查主入口。
   - 规则是工具，不是总路由。
   - `FindingCandidate`、正式风险、`ReviewTrace` 的边界。
   - 工具失败、Agent 失败和证据失败的降级方式。

3. `docs/plans/resume_review_scoring_and_presentation_design.md`
   - 简历库输入、已筛查简历复用、当前批次重算。
   - 评分维度、候选人分层、Top N 选择规则。
   - HR 列表页、详情页、风险和证据展示。
   - 测试数据、黄金测试集和 5000 份压测目标。

4. `docs/plans/resume_review_product_flow.drawio`
   - 产品流程图。
   - 后续实现列表页、详情页、批量任务时参考。

5. `docs/suggestions/2026-05-19-architecture-review-baseline.md`
   - 架构审查红线。
   - 后续代码审查标准。

6. `docs/suggestions/2026-05-19-mvp-first-plan-and-12-day-review.md`
   - 为什么先做最小真实 MVP。
   - 为什么旧版 12 天计划不能继续硬推。

## 3. 执行原则

- 先完成真实 MVP，再扩展批量能力；MVP 是测试路径，不是低质量交付借口。
- 不允许评分输入硬编码在 `AuditUseCase`。
- 不允许 API route、规则或前端绕过 `AgentOrchestrator`。
- 不允许无证据候选进入正式风险。
- 不允许只写 worklog / acceptance 文档而没有测试或可运行验收。
- 每天结束必须跑当天相关测试；阶段结束必须跑后端全量测试和前端 build。
- 12 天内证据链接先用简历原文和本地模拟文件，不把真实网页搜索作为 Day 1-10 阻塞项；但要预留 `web_search_runs` / artifact 接口位置。
- 压测采用分级策略：100 -> 500 -> 1000 -> 5000，不直接跳到 5000。
- 每个 Day 都必须更新 worklog，记录真实完成、mock 边界、阻断点和下一步。

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


## 4.1 AI 执行控制协议

后续让 AI 搭建代码时，必须使用以下控制协议，避免跳阶段、乱扩展或只做 demo。

### 4.1.1 每次任务开始前必须声明

AI 在动代码前必须输出：

```text
当前执行：Day X - [标题]
本次范围：对应 12_day_execution_plan.md 的哪几条任务
不做范围：明确列出本次不做哪些后续阶段功能
真实交付：本次完成后哪些能力可以真实运行
Mock 边界：本次仍有哪些 mock，以及替换点在哪里
验证方式：准备新增/运行哪些测试
```

如果 AI 不能把任务对应到 Day X，就不能开始写代码，应先回到计划文档澄清。

### 4.1.2 每次任务结束时必须汇报

AI 结束时必须汇报：

```text
完成 Day X 的哪些条目
修改文件列表
新增测试列表
验证命令和结果
仍然是 mock 的部分
真实可用的部分
对后续 Day 的影响
下一步建议执行 Day X 的哪一条
```

### 4.1.3 不允许的行为

- 不允许越过 Day 1-6 直接做 5000 份压测。
- 不允许在没有 artifact 分层时把 LLM / 网页搜索大内容塞进 job JSON。
- 不允许为了展示效果写前端假数据冒充后端能力。
- 不允许绕过 `AgentOrchestrator` 直接在 API route 里拼审查结论。
- 不允许把“有 mock”说成“生产完成”。
- 不允许只更新文档不补测试。

### 4.1.4 允许的 MVP 手段

- 可以用 fake parser 验证文档解析接口，但必须保持 `DocumentParser` 可替换。
- 可以用 LLM mock 验证 Agent 候选发现，但必须记录 trace。
- 可以用本地模拟证据库替代真实联网搜索，但证据结构必须和未来 web evidence 兼容。
- 可以先用 SQLite，但必须区分结构化状态和 artifact 大对象。

## 4.2 产品化交付标准

每个 Day 的交付都要按“真实业务代码”判断，而不是按“页面能看”判断。

### 4.2.1 后端标准

- 有 domain model 或 schema。
- 有 service/use case。
- 有 API 或明确被 API 调用的服务层。
- 有错误处理和失败状态。
- 有持久化或明确的 artifact 引用。
- 有至少一个自动化测试覆盖主行为。

### 4.2.2 前端标准

- 通过 API 读取真实后端结果。
- 能展示 loading / failed / completed 状态。
- 风险、证据、评分和 trace 不应写死。
- 如果暂时没有真实 PDF 高亮，也必须展示 page、block、bbox 和 quote，为视觉定位打基础。

### 4.2.3 Agent 标准

- Agent 调用必须进入 `ReviewTrace`。
- 每个工具 step 必须有 input_summary、output_summary、status。
- 工具失败不能导致整份简历审查失败，除非该工具是必要前置步骤。
- Agent 发现的风险必须先是 candidate，再经过 evidence gate。

### 4.2.4 存储标准

- job 状态必须重启后可查。
- 大对象必须写 artifact，不进入主 job payload。
- artifact 必须有类型、路径、hash 或大小信息。
- 后续迁移 PostgreSQL / 对象存储时，业务层不应大改。

## 4.3 产品主线检查表

每完成一天，都检查下面主线是否仍然连贯：

```text
岗位模板
  -> 简历输入
  -> 文档解析
  -> Agent 主流程
  -> 候选风险
  -> 证据校验
  -> 正式风险 / rejected candidate
  -> 评分和分层
  -> 可视化证据定位
  -> 持久化结果
  -> HR 决策辅助
```

如果某一天的改动不能增强这条主线，就要谨慎判断是否偏题。

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
## 9. 按天真实交付定义

本节用于补充第 5 节的 12 天安排，避免 AI 只按标题做表面实现。每一天都要有明确的产品意义、工程边界和验收方式。

### Day 1 真实交付定义：数据契约不是类型堆砌

Day 1 的目标不是单纯新增几个 Pydantic class，而是让后续所有链路围绕稳定对象协作。

交付后应该能回答：

- 一份简历在系统里如何表示？
- 一次审查任务如何表示？
- 一个岗位模板如何影响审查？
- 一个风险候选和正式风险有什么区别？
- trace 如何记录审查过程？
- 大对象未来如何通过 artifact 引用？

Day 1 不要求完整 UI，但必须有测试证明核心对象能序列化、校验、被 use case 使用。

### Day 2 真实交付定义：AgentOrchestrator 成为唯一主入口

Day 2 完成后，审查流程不能再散落在 API route、规则工具和前端里。

所有风险发现都应进入：

```text
AuditUseCase -> AgentOrchestrator.review(document, job_template, context)
```

如果新增工具，也必须由 orchestrator 调用，并进入 trace。

Day 2 的重点是路由干净，不是工具数量多。

### Day 3 真实交付定义：候选风险和正式风险分离

Day 3 完成后，系统必须清楚区分：

- `FindingCandidate`：Agent 或工具发现的可能问题。
- `AuditFinding`：经过 evidence gate 的正式风险。
- `rejected_candidates`：因为证据不足或置信度不足被拒绝的候选。

这一天是“靠谱”的关键。如果没有 evidence gate，AuditX 就会退化成 LLM 生成风险文案。

### Day 4 真实交付定义：评分必须来自真实 signal

Day 4 完成后，评分不能再依赖演示硬编码。

评分至少应读取：

- 岗位模板权重。
- 简历解析结果。
- 正式 findings。
- 优势词典命中。
- 风险数量和风险等级。

评分输出必须包含 calculation details，让 HR 知道分数怎么来的。

### Day 5 真实交付定义：详情页服务 HR 复核

Day 5 的前端不是“把 JSON 打印出来”，而是做单份简历复核工作台。

至少应展示：

- 审查状态。
- 总分和分层。
- 优势标签。
- 风险列表。
- 每个风险的 quote、page、block、bbox。
- rejected candidates。
- trace step。

如果还没有 PDF 高亮，也必须把定位字段展示出来，为后续视觉定位打基础。

### Day 6 真实交付定义：MVP 闭环验收

Day 6 不新增大功能，只做闭环验证和缺口修复。

必须验证：

- 后端全量测试通过。
- 前端 build 通过。
- 单份简历可以从 API 到前端完成审查。
- 任务结果重启后仍可查。
- trace 覆盖 Agent、工具、evidence gate、scoring。
- worklog 写清楚哪些仍是 mock。

Day 6 结束时必须给出 go / no-go：是否进入批量阶段。

### Day 7 真实交付定义：测试数据是产品资产

Day 7 不是随便造几份假简历，而是建立可回归的样本体系。

黄金集要覆盖：

- 最优候选。
- 次优但有潜力。
- 不建议。
- 信息缺失。
- 时间冲突。
- 学历不足但其他优势强。
- 岗位切换后分层变化。

这些样本后续用于防止规则和 Agent 改动导致结果漂移。

### Day 8 真实交付定义：简历库是批量能力基础

Day 8 的目标是从“临时文件审查”升级到“简历入库”。

完成后应该支持：

- 导入简历形成 `ResumeRecord`。
- 状态为 `new`、`reviewed`、`shortlisted`。
- 能按状态筛选。
- 已筛查简历可以复用历史解析结果。
- 当前岗位可以重新审查同一份简历。

这一天开始，存储就不能只围绕 audit job，要准备 resume repository。

### Day 9 真实交付定义：列表页让 HR 控制输入和结果

Day 9 要做 HR 可以使用的列表体验。

列表页至少支持：

- 查看简历库。
- 选择输入。
- 查看审查状态。
- 查看分层和分数。
- 查看优势标签和风险数量。
- 点击进入详情。

这一天不要追求复杂筛选，但要保证列表不是一次性写死数据。

### Day 10 真实交付定义：批量任务和 Top N 能跑小批量

Day 10 目标是让系统处理一批简历，而不是把单份流程循环调用后不管状态。

必须支持：

- batch 创建。
- batch item 状态。
- 单份失败不影响整批。
- 当前批次 Top N。
- N 可配置，默认 20。
- Top N 计算有可解释排序依据。

### Day 11 真实交付定义：证据库和分级压测

Day 11 开始验证系统强度。

本地证据库要模拟未来联网搜索：

- 有 evidence source。
- 有 artifact。
- 有命中摘要。
- 有未命中记录。

压测必须按 100、500、1000 分级，不稳定就停下来记录原因。

### Day 12 真实交付定义：5000 份压测或阻断报告

Day 12 不允许虚报。

如果 1000 份稳定，再跑 5000。

如果 5000 失败，也可以接受，但必须产出：

- 失败阶段。
- 失败原因。
- 数据库或 artifact 瓶颈。
- API 或前端瓶颈。
- 下一步修复建议。

真实的阻断报告比假的“完成 5000”更有价值。

## 10. 给 AI 的固定 Prompt 模板

后续每次让 AI 继续开发，可以使用下面模板：

```text
你是 AuditX 的高级工程师。请先阅读：

1. docs/plans/product_blueprint_resume_screening.md
2. docs/plans/12_day_execution_plan.md
3. docs/strategy/current_execution_focus.md
4. docs/worklog/worklog-5-20.md
5. 注意点.md

必须按照 12 天计划推进。开始前先声明当前执行 Day 几、本次范围、不做范围、真实交付、Mock 边界和验证方式。

本次只执行 Day X 的以下任务：[写清楚任务]

要求：
- 交付真实业务代码，不要只搭 demo。
- 可以用 mock 做测试，但必须标明替换点。
- 不要跳到后续 Day。
- 不要做真实联网搜索，除非当前 Day 明确要求。
- 不要做 5000 份压测，除非已经到 Day 12 且前置压测通过。
- 风险必须有 evidence gate。
- AgentOrchestrator 必须是审查主入口。
- 大对象必须进入 artifact，不要塞进 job payload。
- 先写测试，再实现。
- 更新 worklog。
- 完成后运行测试和构建，并汇报真实完成与遗留风险。
```

这个模板的目的是让 AI 始终按 12 天计划推进，而不是根据上下文随机发挥。
