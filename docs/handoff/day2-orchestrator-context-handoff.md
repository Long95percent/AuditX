# Day 2 交接文件：扩展 AgentOrchestrator 输入和上下文

## 当前状态

Day 1 和 Day 1.5 已收束完成。下一阶段不要继续做 Day 6+，应进入 Day 2：把主路由输入从 `document -> draft` 升级为：

```text
ParsedDocument + JobTemplate + ReviewContext -> ReviewReportDraft
```

## Day 2 目标

- `AgentOrchestrator.review()` 接收 `document`、`job_template`、`context`。
- 所有工具输入统一包含：`document`、`job_template`、`context`。
- `AuditUseCase` 只负责 parser、构造/接收 `ReviewContext`、调用 `AgentOrchestrator`、result assembly。
- API route 不直接调用规则、Agent、LLM provider 或具体工具。
- 评分输入不能继续硬编码在 `AuditUseCase`。

## Day 2 必改文件建议

- `backend/auditx/agent_core/orchestrator.py`
- `backend/auditx/agent_core/llm_candidate_tool.py`
- `backend/auditx/agent_core/rule_tools.py`
- `backend/auditx/agent_core/extractor_tool.py`
- `backend/auditx/application/audit_use_case.py`
- `backend/auditx/api/dependencies.py`
- `backend/tests/unit/test_agent_orchestrator.py`
- `backend/tests/integration/test_audit_use_case.py`
- `backend/tests/integration/test_audit_jobs_api.py`

## 输入契约

使用 Day 1 已补齐的：

- `JobTemplate`：`backend/auditx/domain/scoring.py`
- `ReviewContext`：`backend/auditx/domain/resume_library.py`
- `RunConfig`：`backend/auditx/domain/resume_library.py`
- `ResumeRecord` / `ResumeStatus`：`backend/auditx/domain/resume_library.py`

建议 Day 2 后的入口形态：

```python
AgentOrchestrator.review(
    document: ParsedDocument,
    job_template: JobTemplate,
    context: ReviewContext,
) -> ReviewReportDraft
```

## 工具输入统一格式

所有工具统一接收：

```python
{
    "document": document,
    "job_template": job_template,
    "context": context,
}
```

不能再出现某些工具只收 `document`，某些工具临时收 `job_template` 的分裂形态。

## 评分重构要求

当前 `AuditUseCase` 中仍有临时评分输入：

- `hard_requirement_match=0.75`
- `ability_match=0.8`
- `experience_relevance=0.78`
- `advantage_signals=[...]`

Day 2 或 Day 2 后续必须移除这类硬编码，让评分输入来自：

- `JobTemplate`
- `ReviewContext`
- LLM candidates
- rule tools 的 scoring signal
- findings / rejected candidates

## OpenAI 岗位模板注意事项

- 岗位 JD 创建模板必须走 LLM provider。
- 不允许规则解析 fallback。
- 无 API key 时要明确失败。
- `FakeJobTemplateLLMProvider` 只能用于测试。
- 真正联网调用 OpenAI Responses API 可以作为 Day 1.5 后续小任务，但不要混入 Day 2 Orchestrator 输入重构，避免范围膨胀。

## Day 2 建议测试清单

### Orchestrator 输入测试

- `AgentOrchestrator.review(document, job_template, context)` 能运行。
- trace 中记录 template_id 和 context reuse flag。
- 缺少 context 或 job_template 时不走临时默认模板。

### 工具统一输入测试

- `ExtractorTool` 收到 `document/job_template/context`。
- `LLMCandidateTool` 收到 `document/job_template/context`。
- `ContactMissingRuleTool` 等规则工具收到统一输入。
- 工具失败仍不影响主链路。

### 不绕路测试

- API route 只调用 application service。
- application service 只调用 orchestrator，不直接调用具体规则工具。
- 新增规则工具必须通过 `ToolRegistry` 被 orchestrator 调用。

### 评分输入测试

- `AuditUseCase` 不再硬编码评分输入。
- 同一 document 在不同 `JobTemplate` 下 score / advantage_tags 不同。
- `ReviewContext.run_config.top_n` 可被后续 Top N 流程使用。

## Day 2 验收命令

```powershell
python -m pytest backend\tests -q -p no:cacheprovider
npm.cmd --prefix frontend run build
```

## Day 2 完成定义

Day 2 完成必须同时满足：

- Orchestrator 输入升级完成。
- 工具输入统一完成。
- API route 不绕过 orchestrator。
- trace 可见 job_template/context 信息。
- 后端测试全通过。
- 前端 build 通过。
- worklog 记录完整。
