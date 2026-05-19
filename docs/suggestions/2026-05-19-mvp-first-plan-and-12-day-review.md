# 最小真实 MVP 优先规划与 12 天计划调整建议

> 记录时间：2026-05-19  
> 背景：当前代码已有 AgentOrchestrator、LLM mock、规则工具、评分雏形和前端展示，但 Day 1 数据契约不完整，Day 4 评分存在硬编码，Day 5 规则工具未完整接入主链路。本文建议后续不要直接追求 12 天全量铺开，而是先完成“最小但真实的 MVP”。

## 1. 总体判断

建议让同事先完成最小真实 MVP，不建议一口气全量完成 12 天计划。

原因：

- 当前问题不是“功能数量不够”，而是核心契约和主链路还没有完全稳定。
- 如果继续按原 12 天计划往后推，很容易出现页面、批量、压测都有文件，但评分、分层、规则和证据链并不可信。
- MVP 不是偷工减料，而是把范围砍小，但每条链路必须真实闭合。
- 先做真实 MVP，可以降低后续 Day 7、Day 10、Day 11 的返工风险。

一句话原则：

> 少做范围，多做真实闭环；宁愿只支持单岗位、单份简历，也不能用硬编码结果假装完成岗位匹配。

## 2. 当前 12 天计划是否合理

原 12 天计划方向是对的，但节奏偏激进，不适合当前实现状态继续硬推。

### 2.1 合理的部分

原计划有几个正确方向：

- 先 Agent 主链路，再逐步补规则。
- 规则工具化，不让规则绕过 `AgentOrchestrator`。
- 正式风险必须经过证据校验。
- HR 看到分层、优势、风险、证据和计算明细，不看黑箱结论。
- 12 天内不做真实网页搜索，证据先用本地文件。
- 测试分散到每 2-3 天，不压到最后一天。

这些原则建议保留。

### 2.2 不合理的部分

主要问题是计划把“产品契约、Agent 主链路、评分、规则、前端、证据库、测试数据、批量、压测”全部压进 12 天，依赖链过长。

不合理点：

1. Day 1 内容过大。岗位模板、简历状态、状态流转、输入筛选、评分维度、分层、Top N、结果对象都放在一天，实际很容易只写一部分模型就往后走。
2. Day 4 过早要求完整评分和 Top N。评分依赖结构化简历、岗位模板、优势词典、规则 signal 和风险结果，如果 Day 1-3 没稳，Day 4 很容易硬编码。
3. Day 5 规则工具和评分 signal 接入混在一起。写规则工具不难，难的是让规则输出进入统一候选、证据、评分、trace 链路。
4. Day 7 前端列表页依赖简历库状态和批量数据。如果 Day 1/10 没有数据模型，Day 7 只能做静态或单份演示页面。
5. Day 9 黄金测试集和 Day 10 批量任务安排太晚。没有测试数据和黄金集，Day 4/5 的评分和规则变化缺少回归保护。
6. Day 11 才做 5000 份压测太晚。如果批量模型在 Day 10 才出现，Day 11 基本只能发现问题，未必来得及修。

结论：

- 原计划适合作为“目标清单”，不适合作为当前阶段的严格每日执行计划。
- 建议改成“两阶段计划”：先 4-5 天完成最小真实 MVP，再决定是否进入批量和压测阶段。

## 3. 最小真实 MVP 的定义

最小真实 MVP 只做一条端到端链路：

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

MVP 范围内允许 mock：

- 允许 fake parser。
- 允许 LLM mock。
- 允许本地模拟证据。
- 允许只支持一个默认岗位模板。
- 允许只处理单份简历。

MVP 范围内不允许 mock 或硬编码：

- 不允许评分输入继续写死在 `AuditUseCase`。
- 不允许规则绕过 `AgentOrchestrator`。
- 不允许无证据风险进入正式 findings。
- 不允许前端只展示结果而没有 trace 和计算明细。
- 不允许只靠 worklog/acceptance 文档宣称完成，必须有测试证明。

## 4. MVP 必须完成的功能

### 4.1 数据契约

必须补齐：

- `ResumeStatus`：`new`、`reviewed`、`shortlisted`。
- `ResumeRecord` 或等价模型：简历 ID、文件名、入库时间、状态、解析结果引用。
- `JobTemplate` 扩展字段：硬性要求、优势词典、权重、风险策略、模板版本。
- `ReviewContext` 或等价对象：岗位模板、运行配置、历史上下文、是否复用解析结果。
- `ReviewResult` 或扩展后的 `AuditResult`：分数、分层、优势、风险、证据、计算明细、trace、rejected candidates。

最低要求：这些字段可以先在内存中使用，但必须是明确类型，不要用散乱 dict。

### 4.2 Orchestrator 主链路

必须做到：

- `AgentOrchestrator.review()` 不只接收 `document`，还要接收 `job_template` 和 `context`。
- 所有 LLM mock、规则工具、证据校验都由 orchestrator 编排。
- API route 不直接调用具体规则、具体 Agent 或具体工具。
- 每个步骤写入 `ReviewTrace`。
- 工具失败时返回 failed trace step，但不导致整份简历失败。

建议目标接口：

```python
orchestrator.review(
    document=document,
    job_template=job_template,
    context=review_context,
)
```

### 4.3 规则和评分连接

必须做到：

- 规则输出统一归一成 `FindingCandidate` 或 `ScoringSignal`。
- 优势词典工具必须能拿到岗位模板。
- 联系方式缺失、教育缺失等规则必须进入 trace。
- 评分输入必须来自结构化简历、规则输出、LLM mock 输出或 evidence-backed findings。
- `AuditUseCase` 中不能继续出现固定的 `hard_requirement_match=0.75`、`ability_match=0.8`、`advantage_signals=[...]` 这类演示硬编码。

### 4.4 Evidence gate

必须做到：

- LLM mock 和规则提出的风险候选都先进入候选层。
- 有证据且校验通过的候选才能进入正式 findings。
- 无证据或证据不匹配的候选进入 rejected candidates。
- rejected candidates 必须保留来源、原因和 trace，不只统计数量。

### 4.5 前端最小展示

只做单份简历详情页即可，不做批量列表。

必须展示：

- 分层。
- 总分和维度分。
- 优势标签。
- 正式风险。
- rejected candidates。
- evidence quote / block / bbox。
- 计算明细。
- ReviewTrace。

不要求：

- 批量分页。
- 复杂筛选。
- 真实 PDF 高亮。
- 企业协作。

### 4.6 测试要求

MVP 不算完成，除非以下测试通过：

- 调用审查流程必然产生 `ReviewTrace`。
- 工具失败不影响整份审查。
- 无证据候选不会进入正式 findings。
- 同一份简历在不同岗位模板下 score 或 advantage tags 不同。
- 优势词典工具通过 orchestrator 拿到 job template 并影响评分或优势标签。
- API 返回 score、layer、findings、rejected candidates、trace。
- 前端 build 通过。

## 5. 建议的新计划

### Phase A：MVP 补契约和主链路，建议 2 天

目标：先把 Day 1 和 Day 2 的缺口补齐。

任务：

- 补 `ResumeStatus`、`ResumeRecord`、`ReviewContext`。
- 扩展 `JobTemplate`：硬性要求、风险策略、模板版本。
- 补产品经理岗位模板，满足原 Day 1 三个模板要求。
- 修改 `AgentOrchestrator.review()` 输入，接收岗位模板和上下文。
- 修改规则工具调用，让所有工具拿到统一 input：document、job_template、context。
- 增加测试：orchestrator 不传 job_template 时应失败或明确降级；传入时规则可读到岗位模板。

验收：

- Day 1 契约不再缺关键项。
- Day 2 orchestrator 不再只是 `document -> draft` 的薄管道。

### Phase B：MVP 真实评分，建议 2 天

目标：去掉 Day 4 的硬编码评分。

任务：

- 定义 `ScoringSignal` 或等价结构。
- 让 LLM mock、优势词典、基础规则输出 scoring signals。
- 从 signals 和正式 findings 生成 `CandidateScoreInput`。
- 删除 `AuditUseCase` 里的固定匹配度和固定优势信号。
- 增加测试：不同岗位模板下 signals 影响不同；风险数量影响扣分；硬性要求低分但不自动淘汰。

验收：

- API 返回的 score 能解释其来源。
- 计算明细能对应到规则或 Agent 输出。

### Phase C：MVP 前端和验收闭环，建议 1 天

目标：让单份简历可演示、可解释。

任务：

- 前端详情区按 MVP 必须展示项整理。
- 明确区分正式 findings 和 rejected candidates。
- trace 中展示 Agent、规则、工具、evidence gate 状态。
- 补 API 集成测试。
- 跑后端全量测试和前端 build。

验收：

- 单份简历从选择到审查结果完整闭环。
- HR 能看到为什么这个分数、为什么这个风险成立、为什么某些候选被拒绝。

### Phase D：再进入批量前置，不建议立刻做完整 Day 7-12

MVP 通过后，再决定是否做批量。

下一阶段建议顺序：

1. 测试数据生成器和小型黄金集。
2. 简历库状态和输入筛选 UI。
3. 批量任务模型。
4. Top N 当前批次排序。
5. 500-1000 份小压测。
6. 再考虑 5000 份压测。

不要直接跳到 5000 份，因为当前系统还没有持久化任务、批量状态、失败重试和分页索引。

## 6. 建议给同事的新执行口径

建议这样要求同事：

> 暂停继续铺 Day 6 之后的功能。先用 4-5 天完成最小真实 MVP。MVP 可以只支持单份简历和一个默认岗位，但必须去掉评分硬编码，必须由 AgentOrchestrator 编排，必须有岗位模板上下文，必须有 evidence gate、score、layer、trace 和前端展示。完成后再评估是否进入批量和 5000 压测。

## 7. 对原 12 天计划的调整建议

建议不要废弃原计划，而是改名为“完整目标路线图”，再新增一个“MVP 阶段计划”。

推荐调整：

- 原 Day 1 拆成两天：数据契约一天，岗位模板和样例验收一天。
- 原 Day 4 的 Top N 从单份评分中拆出去，放到批量阶段。
- 原 Day 5 的规则工具分成两步：先写工具，再接 scoring signal。
- 原 Day 7 前端列表页推迟到简历库状态和批量模型之后。
- 原 Day 9 黄金测试集提前到 MVP 后立刻做。
- 原 Day 10/11 的 5000 压测改成分级压测：100、500、1000、5000。

新的阶段节奏建议：

```text
Phase 1：最小真实 MVP，4-5 天
Phase 2：黄金测试集 + 小批量，2-3 天
Phase 3：HR 列表页 + Top N，2-3 天
Phase 4：批量任务 + 1000 份压测，2-3 天
Phase 5：5000 份压测 + 演示验收，2 天
```

这样总时长可能仍接近 12-15 天，但每个阶段都有可验收闭环，不会出现“计划写满、链路不真”的问题。

## 8. 审查门槛

后续我审查同事代码时，建议按以下门槛判断是否通过：

- 如果继续新增前端页面，但评分仍硬编码：不通过。
- 如果新增规则，但规则绕过 orchestrator：不通过。
- 如果新增批量任务，但没有简历状态和失败隔离：不通过。
- 如果新增 Top N，但没有当前批次上下文：不通过。
- 如果新增 evidence 展示，但无证据候选能进入正式风险：不通过。
- 如果只有 worklog/acceptance 文档，没有自动化测试或可运行验证：不通过。

## 9. 最终建议

- 决策上选“先完成最小真实 MVP”。
- 管理上不要允许“全量铺开但核心硬编码”。
- 节奏上先修 Day 1/4/5 缺口，再进入 Day 6。
- 原 12 天计划保留为目标路线图，但不要再作为当前严格每日交付表。
