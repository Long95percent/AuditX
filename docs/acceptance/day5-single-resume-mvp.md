# Day 5 单份简历 MVP 前端闭环验收

## 当前执行 Day

Day5：单份简历 MVP 前端闭环。

## 本次范围

- 前端展示审查状态、score、layer、dimension scores、advantage tags。
- 前端展示正式 findings、rejected candidates、evidence quote、page、block、bbox。
- 前端展示 ReviewTrace，包括 Agent、规则工具、candidate evidence gate、scoring 状态和 metadata。
- 前端类型与 API response schema 对齐，包含 `rejection_reason`。

## 不做范围

- 不做 PDF 高亮或 bbox overlay，只展示定位字段。
- 不做批量、Top N、简历库、压测、真实联网搜索。
- 不把 LLM prompt、OCR 文本、搜索快照等大对象塞进 job payload。

## Mock 边界和替换点

- 当前简历解析仍使用 fake parser。
- 当前 LLM 候选发现仍使用 `LLMCandidateTool` / `LLMMockProvider`。
- 当前规则工具是真实业务链路中的本地规则实现，可继续扩展。
- 后续替换真实 OCR / LLM provider 时，前端继续消费同一套 API 字段：`findings`、`rejected_candidates`、`score`、`trace`、`evidence`。

## API 自动验收

在项目根目录运行：

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run pytest backend/tests/integration/test_audit_jobs_api.py::test_audit_job_api_creates_job_task_and_returns_findings -q -p no:cacheprovider
```

期望：

- 返回 `score.total_score`、`score.layer`、`score.dimension_scores`、`score.advantage_tags`、`score.calculation_details`。
- 返回正式 `findings`，且每条正式风险包含至少一个 evidence。
- evidence 包含 `quote`、`page_number`、`block_id`、`bbox.x0/y0/x1/y1`。
- 返回 `rejected_candidates`，并包含 `rejection_reason`。
- `trace.steps` 包含 LLM mock、规则工具、`candidate_evidence_gate`、`scoring_engine.score`。

## 前端构建验收

```powershell
npm.cmd --prefix frontend run build
```

期望：TypeScript 编译和 Vite build 成功。

## 桌面 UI 手工验收

1. 启动后端和桌面应用。
2. 点击 `Check Backend`，确认 Backend 显示 online。
3. 点击 `Choose Document` 选择本地简历文件。
4. 点击 `Run Fake Audit`，等待状态变为 completed。
5. 在主工作台确认：
   - `HR Review Summary` 展示 Match Score、layer、模板、优势、风险数量、evidence anchors。
   - dimension scores 和 calculation details 可见。
   - `Findings` 列表展示正式风险、rule、confidence、agent。
   - 每条正式风险展示 evidence quote、page、block、bbox。
   - `Agent Trace` 展示所有 trace step，不只展示前几条。
   - trace metadata 可见，包括 tool name、candidate id、rejection reason、scoring signals 或 calculation details。
   - `Rejected Candidates` 展示候选标题、来源、证据数和 `rejection_reason`。
6. 打开 `验收 / 测试中心`，分别查看 Trace、Candidates、Score、Evidence 面板，确认与主工作台一致。

## 通过标准

- 单份简历从选择文件、创建审查任务、后台执行、轮询结果到前端复核形成闭环。
- HR 能看到为什么进入正式风险、为什么候选被拒绝、证据定位在哪里、评分如何计算。
- 无证据风险不进入正式 findings。
- 页面不是 JSON dump，而是面向 HR 复核的结构化工作台。
