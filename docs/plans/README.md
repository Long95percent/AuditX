# AuditX 简历审查工具规划入口

当前规划已收敛为 **简历审查效率工具**，近期目标是先完成最小真实 MVP，再扩展到小批量、Top N、分级压测和演示验收。

## 1. 当前产品方向

AuditX 面向 HR / 招聘团队，核心目标是提升简历初筛效率：

- 按岗位模板审查简历。
- 支持从简历库选择输入，也支持新上传简历。
- 简历有状态标记：新入库、已筛查、已入岗位候选库。
- HR 可用预定义筛选选择输入：按入库时间排序、只看新简历。
- 支持 HR 输入 `N`，系统自动挑选当前岗位 / 当前批次最适合的 `N` 份简历；默认 `N = 20`。
- 将候选人分为最优、次优但有潜力、不建议。
- 展示每份简历的优势、风险、匹配分、证据、计算明细和 Agent trace。
- 当前阶段采用分级压测：100 -> 500 -> 1000 -> 5000；长期可扩展到更大量级历史库。

## 2. 规划文档

建议按以下顺序审查：

1. `12_day_execution_plan.md`
   - 当前唯一执行排期。
   - 先最小真实 MVP，再小批量、列表页、Top N、分级压测。
   - 每天包含任务、建议文件、测试和产出。

2. `agent_first_routing_design.md`
   - Agent 优先的审查路由。
   - 规则工具化。
   - LLM 放权边界。
   - `FindingCandidate`、`ReviewTrace`、降级策略。
   - 防止规则路由绕开 Agent 能力。

3. `resume_review_scoring_and_presentation_design.md`
   - 指标归类。
   - 评分方式。
   - 候选人分层。
   - HR 列表页和详情页呈现。
   - 测试数据和 5000 份压测目标。

4. `resume_review_product_flow.drawio`
   - 产品流程图。
   - 用于理解 HR 输入、审查结果、列表页和详情页之间的关系。

5. `docs/suggestions/2026-05-19-architecture-review-baseline.md`
   - 架构审查基线。
   - 后续代码偏离设计时的判断标准。

6. `docs/suggestions/2026-05-19-mvp-first-plan-and-12-day-review.md`
   - 为什么先做最小真实 MVP。
   - 为什么旧版全量铺开的 12 天计划需要调整。

## 3. 当前明确架构原则

- `AgentOrchestrator` 是唯一审查主路由入口。
- LLM / Agent 先负责理解、发现、解释，保证产品链路可用。
- 规则作为工具和校验器逐步沉淀，不提前接管主流程。
- 正式风险必须经过证据校验。
- 单个 Agent、规则或工具失败，不应导致整份简历审查失败。
- 岗位模板控制权重、优势词典、硬性要求和风险策略。
- HR 看到的是分层、优势、风险、证据、计算明细和 trace，不是黑箱机器裁决。

## 4. 12 天计划优先级

1. 补齐 MVP 数据契约：简历状态、岗位模板、ReviewContext、结果对象。
2. 扩展 `AgentOrchestrator`：接收 document、job_template、context，并统一工具输入。
3. 打通 candidate -> evidence gate -> formal finding / rejected candidate。
4. 去掉评分硬编码，让 scoring signal 进入真实评分链路。
5. 完成单份简历详情页 MVP。
6. 建立小型黄金集，再做简历库、列表页、批量任务和 Top N。
7. 最后做本地证据库和分级压测。

## 5. 已删除或不再作为当前主线的旧方向

以下内容不作为当前执行主线：

- 泛化审计系统定位。
- 只围绕 fake audit demo 的旧执行计划。
- 过早以规则路由主导审查流程。
- 一口气铺完整 Day 1-Day 12 但核心链路硬编码。
- 12 天计划内实现真实网页搜索或生产级公司调查。
- 12 天计划内按 10 万份实时处理做压测。
