# Day 6 MVP 闭环验收报告

## 当前执行 Day

Day6：MVP 集成测试和缺口修复。

## 本次范围

- 验证 Day1-Day5 单份简历真实 MVP 闭环。
- 检查后端全量测试和前端构建。
- 检查正式风险 evidence gate、ReviewTrace 覆盖、scoring、前端展示能力。
- 检查任务结果重启后仍可查。
- 补齐发现的门槛覆盖缺口。

## 不做范围

- 不新增批量任务。
- 不做 Top N 页面或批量排序。
- 不做简历库入库和状态流转。
- 不做压测和真实联网搜索。
- 不做 PDF bbox 高亮 overlay。

## Mock 边界

- `FakeDocumentParser` 仍是当前本地解析替身，后续替换真实 OCR / parser。
- `LLMCandidateTool` / `LLMMockProvider` 仍是 LLM 候选发现替身，后续替换真实 LLM provider。
- 本地规则工具、`AgentOrchestrator`、`EvidenceValidator`、scoring signal 聚合、API 任务持久化和前端工作台是真实业务链路。

## MVP 门槛核对

| 门槛 | 结果 | 证据 |
| --- | --- | --- |
| 单份简历输出分层、优势、风险、证据和计算明细 | 通过 | `test_audit_use_case_includes_score_result_and_calculation_details`、Day5 前端构建 |
| ReviewTrace 说明调用 Agent、规则和工具 | 通过 | `test_audit_job_api_creates_job_task_and_returns_findings` 断言 LLM mock、规则工具、evidence gate、scoring trace |
| 无证据候选不会进入正式风险 | 通过 | `test_orchestrator_accepts_evidence_backed_llm_candidate_and_rejects_unverified_one`、`test_evidence_validator_rejects_finding_without_evidence` |
| 同一简历在不同岗位模板下结果不同 | 通过 | Day6 新增 `test_same_resume_gets_different_match_results_across_job_templates` |
| 评分输入不再硬编码在 AuditUseCase | 通过 | `test_audit_use_case_score_details_include_signal_sources`、规则 `scoring_signals` 测试 |
| 前端展示 score、layer、findings、rejected candidates、evidence、trace | 通过 | Day5 工作台改造 + `npm.cmd --prefix frontend run build` |
| 任务结果重启后仍可查 | 通过 | `test_sqlite_repository_loads_saved_job_from_new_instance`、`test_audit_job_service_reads_jobs_persisted_by_previous_service`、API service cache 重建测试 |

## 自动化验证命令

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run pytest backend/tests -q -p no:cacheprovider
npm.cmd --prefix frontend run build
```

## 手工验收建议

1. 启动后端和桌面应用。
2. 点击 `Check Backend`，确认后端在线。
3. 选择一份本地简历并运行审查。
4. 确认任务状态完成。
5. 确认主工作台展示 score、layer、dimension scores、advantage tags、calculation details。
6. 确认正式 findings 均有 quote、page、block、bbox。
7. 确认 rejected candidates 展示 `rejection_reason`。
8. 确认 Agent Trace 展示 LLM mock、规则工具、candidate evidence gate、scoring。
9. 重启后端后用同一个 job id 查询，确认结果仍可查。

## Go / No-Go

Go：允许进入 Day7 测试数据和黄金集阶段。

理由：Day1-Day5 的单份简历闭环已具备可验证链路：任务化 API、持久化 job、AgentOrchestrator 主入口、候选发现、evidence gate、scoring signals、前端复核工作台和验收文档。

## 遗留风险

- OCR/parser 仍是 fake，需要后续替换真实解析能力。
- LLM 仍是 mock provider，需要后续接真实 LLM 并把 prompt/response 作为 artifact 保存。
- PDF bbox 目前只展示坐标，尚未做视觉高亮。
- 现有 SQLite job 快照仍包含完整 job result，后续大对象必须继续拆入 artifact，避免 payload 膨胀。
