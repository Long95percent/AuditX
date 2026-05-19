# 每日计划完成度代码审查

> 记录时间：2026-05-19  
> 审查范围：对照 `docs/plans/12_day_execution_plan.md`，检查当前代码是否全量完成每日计划，是否存在只做表面实现或绕开原设计的情况。

## 结论

- 当前代码不是 12 天计划的全量完成态，最多可以认为完成了 Day 2、Day 3 的主链路骨架，并部分完成 Day 4、Day 5。
- 不能直接说完全“偷懒”，因为确实新增了 `AgentOrchestrator`、`FindingCandidate`、`ReviewTrace`、LLM mock、规则工具、评分模型和测试，并且当前后端测试与前端构建通过。
- 但存在明显“交付口径放宽”的问题：部分每日计划只做了演示级/硬编码实现，未达到计划里“功能产出 + 对应测试 + 可记录结果”的完整定义。
- 如果同事声称 Day 1 到 Day 5 已全量完成，这个说法不准确；建议改为“Day 2/3 基本完成，Day 4/5 部分完成，Day 1 数据契约仍缺关键项”。

## 验证结果

本次已运行：

```text
python -m pytest backend\tests -q -p no:cacheprovider
结果：31 passed
```

```text
npm.cmd --prefix frontend run build
结果：成功，vite build completed
```

测试和构建通过说明当前代码没有明显破坏现有链路，但不能证明每日计划已全量完成。

## 对照每日计划

### Day 1：统一数据契约和岗位模板

完成度：不完整。

已完成：

- 已有 `JobTemplate`、`CandidateLayer`、`CandidateScoreInput`、`ScoreResult`，见 `backend/auditx/domain/scoring.py:13`、`backend/auditx/domain/scoring.py:68`、`backend/auditx/domain/scoring.py:98`。
- 已有前端和财务两个岗位模板样例，见 `backend/auditx/domain/scoring.py:28`、`backend/auditx/domain/scoring.py:48`。
- 已有 Top N 选择器和非法 N 校验，见 `backend/auditx/domain/scoring.py:162`、`backend/auditx/domain/scoring.py:168`。

缺口：

- 计划要求 3 个岗位模板样例：前端、财务、产品经理；当前只有前端和财务，没有产品经理模板。
- `JobTemplate` 只有 `weights` 和 `advantage_dictionary`，缺少计划明确要求的硬性要求、风险策略等字段，见 `backend/auditx/domain/scoring.py:13`。
- 没有简历库状态模型：新入库、已筛查、已入岗位候选库。
- 没有状态流转模型：新上传/导入 -> 新入库 -> 已筛查 -> 已入岗位候选库。
- 没有简历库输入筛选契约：按时间排序、只看新简历。
- Day 1 要求用 3 份伪简历人工检查分层、10 份伪简历检查 Top N；当前没有看到对应验收数据或记录。

判断：Day 1 不能算全量完成。这里有“把评分类当成完整数据契约”的嫌疑。

### Day 2：建立 Agent 主路由骨架

完成度：基本完成。

证据：

- 已建立 `AgentOrchestrator`，见 `backend/auditx/agent_core/orchestrator.py:15`。
- `AuditUseCase` 通过 orchestrator 执行 review，见 `backend/auditx/application/audit_use_case.py:31`。
- 已定义 `FindingCandidate` 和 `ReviewTrace`，见 `backend/auditx/domain/review.py:27`、`backend/auditx/domain/review.py:31`。
- orchestrator 会调用工具注册表中的工具，见 `backend/auditx/agent_core/orchestrator.py:97`、`backend/auditx/agent_core/orchestrator.py:193`。
- 规则/工具失败会写 trace 并不中断主流程，见 `backend/auditx/agent_core/orchestrator.py:198`。

保留意见：

- orchestrator 目前只接收 `document`，没有接收岗位模板、运行配置和历史上下文，见 `backend/auditx/agent_core/orchestrator.py:26`。
- 这会影响后续岗位模板、优势词典、历史复用和批量任务的接入。

判断：Day 2 主体完成，但接口设计偏薄，需要尽早扩展为 `review(document, job_template, context/config)` 或等价输入对象。

### Day 3：LLM Mock 与候选发现链路

完成度：基本完成。

证据：

- 代码中已出现 `llm_mock_provider.py`、`llm_candidate_tool.py`、`llm_candidate_normalizer.py`。
- orchestrator 会调用 `agent.llm_mock.candidate_discovery`，见 `backend/auditx/agent_core/orchestrator.py:140`。
- LLM candidate 会经过 evidence validator 后才转成正式 finding，见 `backend/auditx/agent_core/orchestrator.py:58`、`backend/auditx/agent_core/orchestrator.py:60`。
- 无证据候选会进入 rejected，并写 trace，见 `backend/tests/integration/test_llm_candidate_flow.py:25`。

判断：Day 3 可以认为基本达标。

### Day 4：岗位匹配与评分引擎第一版

完成度：部分完成，存在演示级硬编码。

已完成：

- 维度分、岗位模板权重、优势加分、风险扣分、硬性要求低分不直接淘汰都有实现，见 `backend/auditx/domain/scoring.py:112`、`backend/auditx/domain/scoring.py:139`。
- 同一候选人在不同岗位模板下得分不同有测试，见 `backend/tests/unit/test_scoring_engine.py:34`。
- Top N 自定义 N、输入小于 N、非法 N 都有单测，见 `backend/tests/unit/test_scoring_engine.py:52`、`backend/tests/unit/test_scoring_engine.py:83`、`backend/tests/unit/test_scoring_engine.py:90`。
- API 返回 score，前端类型也已扩展，见 `backend/auditx/api/schemas.py:24`、`frontend/src/types/audit.ts:63`。

缺口：

- `AuditUseCase` 里的评分输入是硬编码，不是从真实结构化简历、岗位模板或 Agent 分析结果计算出来的：`hard_requirement_match=0.75`、`ability_match=0.8`、`experience_relevance=0.78`、`advantage_signals=["react", "typescript", "audit_trace"]`，见 `backend/auditx/application/audit_use_case.py:44`、`backend/auditx/application/audit_use_case.py:47`。
- `TopNSelector` 只有单元测试，没有接入 API、批次任务或 HR 输入 N；所以“HR 自定义 N 的挑选逻辑”还只是库函数，不是产品链路。
- 分层结果目前是单份审查里的 score.layer，不是批量候选人分层，也没有当前批次 rank。

判断：Day 4 不能算全量完成。评分引擎本身有了，但产品链路仍是 mock/硬编码。

### Day 5：优势词典与基础规则工具

完成度：部分完成。

已完成：

- 已实现多个规则工具：优势词典、联系方式缺失、教育经历缺失、年限计算、关键词命中，见 `backend/auditx/agent_core/rule_tools.py:16`、`backend/auditx/agent_core/rule_tools.py:44`、`backend/auditx/agent_core/rule_tools.py:70`、`backend/auditx/agent_core/rule_tools.py:95`、`backend/auditx/agent_core/rule_tools.py:113`。
- orchestrator 会运行 `resume.rule.*` 工具，见 `backend/auditx/agent_core/orchestrator.py:193`。
- 规则失败不影响主链路有测试，见 `backend/tests/integration/test_rule_tool_flow.py:25`。

缺口：

- 默认 API 只注册了联系方式缺失和教育经历缺失两个规则，未注册优势词典、年限计算、关键词命中，见 `backend/auditx/api/dependencies.py:21`、`backend/auditx/api/dependencies.py:22`。
- `AdvantageDictionaryTool` 要求输入 `job_template`，见 `backend/auditx/agent_core/rule_tools.py:22`，但 orchestrator 调用规则工具时只传了 `document`，见 `backend/auditx/agent_core/orchestrator.py:197`。这意味着优势词典工具即使注册到 orchestrator，也会因为缺少岗位模板而失败。
- 规则输出“scoring signal”目前没有真正接入 `ScoringEngine`；评分仍使用 `AuditUseCase` 的硬编码 advantage signals。
- 联系方式/教育缺失规则的 evidence 由于 fake parser 文本限制，很多情况下只能成为 rejected candidate，而不是稳定可展示的正式风险。

判断：Day 5 不能算全量完成。规则类写了不少，但规则与岗位模板、评分、正式链路的连接还不完整。

### Day 6 及之后

完成度：未开始或无足够证据完成。

缺少：

- Day 6 的端到端集成测试日：混合新入库和已筛查简历、历史复用、trace 完整性、evidence 校验一致性。
- Day 7 的 HR 列表页和详情页：当前是单份 fake audit 验收面板，不是简历库列表页。
- Day 8 的本地公司信息与 `local://evidence/company_mock_db.json#...` 证据链接。
- Day 9 的批量简历数据生成器和黄金测试集。
- Day 10 的批量任务、任务状态、失败重试、分页筛选和 5000 份测试数据。
- Day 11 的 5000 份压测报告。
- Day 12 的完整回归、黄金集回归、演示数据和已知问题清单。

## 是否存在偷懒

我的判断：存在局部“交付缩水”，但不是完全没干活。

比较明显的缩水点：

1. Day 1 数据契约没有完整落地，却开始往 Day 4/5 走。简历状态、输入筛选、产品经理模板、硬性要求和风险策略都缺。
2. Day 4 用硬编码评分输入支撑 API 展示，容易造成“看起来有评分，实际上没有岗位匹配分析”的假象。
3. Day 5 写了多个 rule tool，但默认链路只接入两个；优势词典工具和 orchestrator 输入不匹配，实际无法通过主路由正常使用。
4. `TopNSelector` 有测试但没接产品入口，不能声称 HR 自定义 N 链路完成。
5. acceptance 文档和 worklog 写得比较完整，但部分内容是“验收说明”而不是实际产品闭环。

## 风险

- 如果继续在 `AuditUseCase` 中硬编码评分输入，后续岗位匹配会变成假评分，HR 看到的分层不可信。
- 如果 `AgentOrchestrator` 不接收岗位模板和运行上下文，规则工具、优势词典、历史复用、批量任务都会继续绕路。
- 如果先做 UI 展示而不补简历库状态和批量模型，Day 7 之后会形成演示页面而不是实际 HR 列表页。
- 如果只依赖现有 31 个测试，无法发现“计划要求未完成”的问题，因为测试主要覆盖当前实现，而不是完整验收标准。

## 建议

优先级从高到低：

1. 回补 Day 1：补 `ResumeStatus`、状态流转、输入筛选契约、产品经理模板、`JobTemplate.hard_requirements`、`JobTemplate.risk_strategy`。
2. 扩展 orchestrator 输入：不要只传 `document`，应传岗位模板、运行配置和审查上下文。
3. 移除或隔离 `AuditUseCase` 中的硬编码评分输入，改为从结构化简历、规则 signal、Agent output 汇总生成 `CandidateScoreInput`。
4. 把 `AdvantageDictionaryTool`、`YearsExperienceRuleTool`、`KeywordMatchRuleTool` 接入默认 registry，并确保 orchestrator 传入它们需要的上下文。
5. 为 Day 4 增加产品链路测试：API 或 service 层能处理 HR 自定义 N，并返回当前批次 Top N。
6. 在继续 Day 6 之前，先补一份“Day 1-5 缺口修复清单”，否则后续会在不稳的契约上继续堆功能。

## 审查结论

- 不建议接受“Day 1 到 Day 5 已全量完成”的说法。
- 可以接受“Day 2/3 已基本完成，Day 4/5 有可运行雏形，但仍有关键缺口”。
- 如果这是同事阶段性提交，建议有条件通过，但必须把上述缺口列为下一步阻断项，尤其是 Day 1 数据契约和 Day 4 硬编码评分。
