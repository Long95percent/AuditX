# Day 3 验收说明：LLM Mock 与候选发现链路

## 验收目标

确认 LLM mock 只能提出候选，不能绕过证据校验直接生成正式风险：

- `LLMMockProvider` 返回结构化候选。
- LLM 输出被转换为 `FindingCandidate`。
- 有原文 evidence 的候选可进入正式 findings。
- 无 evidence 的候选进入 `rejected_candidates`，不进入正式 findings。
- trace 中能看到 LLM candidate discovery 和 accepted/rejected 原因。

## 自动化验收

在项目根目录运行：

```powershell
python -m pytest backend\tests -q -p no:cacheprovider
npm.cmd --prefix frontend run build
```

期望结果：

- 后端测试全部通过。
- 前端 TypeScript 编译和 Vite build 成功。

## 桌面 UI 手工验收

1. 双击项目根目录的 `启动AuditX桌面应用.bat`。
2. 点击 `Check Backend`。
3. 点击 `Choose Document` 选择文件。
4. 点击 `Run Fake Audit`。
5. 点击 `Day 2 验收面板`。
6. 在面板中确认：
   - `ReviewTrace` 包含 `agent.llm_mock.candidate_discovery`。
   - `LLM Mock Candidates` 中有 2 条候选。
   - `llm_candidate_company_a` 有 evidence count。
   - `llm_candidate_unverified_gap` 显示 rejected: missing verified evidence。
   - `Evidence` 中不应出现无证据候选。

## API 手工验收

`POST /api/audit-jobs` 响应中应包含：

- `candidates`，长度为 2。
- `rejected_candidates`，包含 `llm_candidate_unverified_gap`。
- `trace.steps`，包含 `agent.llm_mock.candidate_discovery`。
- `findings`，不包含 `llm_candidate_unverified_gap`。
