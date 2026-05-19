# Day 5 / Day 6 单份简历 MVP 闭环验收

> 记录时间：2026-05-19  
> 范围：只收口单份简历 MVP，不进入批量、列表页、Top N 或压测。

## 1. 验收目标

本次闭环目标是让单份简历审查从后端到前端形成可演示产品视图：

```text
本地文件
  -> fake parser
  -> AgentOrchestrator
  -> extractor / LLM mock / resume tools
  -> evidence gate
  -> formal findings + rejected candidates
  -> ScoreResult + CandidateLayer
  -> ReviewTrace
  -> API response
  -> 前端 HR Review Summary / Findings / Rejected Candidates / Agent Trace
```

## 2. 已完成项

- 后端 `/api/audit-jobs` 返回单份审查完整数据：正式 findings、rejected candidates、score、trace。
- `AgentOrchestrator` 已接收并下传 `JobTemplate` 和 `ReviewContext`。
- 评分输入不再固定写死在 `AuditUseCase`，而是从 resume 工具输出的 scoring signals 汇总。
- 前端主工作区不再只依赖测试中心查看结果，新增正常产品视图：
  - HR Review Summary：总分、分层、模板版本、优势、风险数、维度分。
  - Findings：正式风险、证据 quote、页码、block、bbox、建议。
  - Rejected Candidates：未进入正式风险的候选项和原因。
  - Agent Trace：工具/Agent 步骤、evidence gate、scoring_engine.score、状态、输出摘要和失败计数。

## 3. 自动化验收命令

后端：

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run pytest backend\tests -q -p no:cacheprovider
```

前端：

```powershell
npm.cmd --prefix frontend run build
```

## 4. 手工验收步骤

1. 启动桌面应用。
2. 点击 `Choose Document` 选择本地测试 PDF。
3. 点击 `Run Fake Audit`。
4. 在主工作区确认：
   - HR Review Summary 出现 score、layer、dimension scores。
   - Findings 展示正式风险和 evidence bbox。
   - Rejected Candidates 展示缺少证据的候选风险。
   - Agent Trace 展示 extractor、LLM mock、resume tools、evidence gate、scoring_engine.score 的执行状态。
5. 打开“验收 / 测试中心”，各测试面板仍可独立查看 runtime、trace、candidates、score、evidence、OpenAI 设置。

## 5. 明确未做

- 未做简历库列表页。
- 未做批量任务和 Top N 当前批次排序。
- 未做真实 OCR、真实 PDF 渲染、真实网页搜索或公司信息库。
- 未把 `RunConfig.top_n`、`historical_context`、`reuse_parsed_result` 接入真实业务。
- scoring signals 目前仍通过 trace metadata 传递；后续建议拆成正式 `ReviewSignal` 或 `ScoringSignal`，避免 trace 同时承担审计记录和业务数据总线。

## 6. 验收结论

Day 5 / Day 6 的“单份简历 MVP 产品闭环”可以进入验收，但不能宣称批量能力、简历库能力或 Top N 已完成。

