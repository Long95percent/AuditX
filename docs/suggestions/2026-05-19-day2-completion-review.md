# Day 2 完成度审查：AgentOrchestrator 输入和上下文

> 记录时间：2026-05-19  
> 审查范围：对照 `docs/plans/12_day_execution_plan.md` 的 Day 2，检查当前实现是否基本完成。

## 结论

Day 2 可以认为 **基本完成**。

理由：

- `AgentOrchestrator.review()` 已从只接收 `document`，扩展为接收 `document`、`job_template`、`context`。
- Orchestrator 已统一向 extractor tool、LLM mock tool、rule tools 传入 `document`、`job_template`、`context`。
- 已有测试证明 LLM tool 和 rule tool 能通过 orchestrator 拿到 `JobTemplate` 和 `ReviewContext`。
- 工具失败不中断主流程的测试仍然通过。
- API route 仍通过 service/use case 进入审查流程，没有看到 route 直接调用规则、Agent 或工具。

## 代码观察

### Orchestrator 输入已扩展

- `backend/auditx/agent_core/orchestrator.py:28` 定义 `review()`。
- `backend/auditx/agent_core/orchestrator.py:31` 接收 `job_template`。
- `backend/auditx/agent_core/orchestrator.py:32` 接收 `context`。
- `backend/auditx/agent_core/orchestrator.py:35` 到 `backend/auditx/agent_core/orchestrator.py:37` 将模板和上下文传入 extractor、LLM、rule 三类步骤。

### 工具输入已统一

- `backend/auditx/agent_core/orchestrator.py:330` 定义 `_tool_input()`。
- `backend/auditx/agent_core/orchestrator.py:336` 返回 `document`、`job_template`、`context`。
- `backend/auditx/agent_core/orchestrator.py:155` LLM mock tool 使用统一输入。
- `backend/auditx/agent_core/orchestrator.py:216` rule tools 使用统一输入。
- `backend/auditx/agent_core/orchestrator.py:288` extractor tool 使用统一输入。

### AdvantageDictionaryTool 已具备上下文能力

- `backend/auditx/agent_core/rule_tools.py:20` 定义 `AdvantageDictionaryTool.run()`。
- `backend/auditx/agent_core/rule_tools.py:22` 读取 `job_template`。
- `backend/auditx/agent_core/rule_tools.py:23` 校验 `document` 和 `job_template` 类型。

### 测试覆盖

- `backend/tests/unit/test_agent_orchestrator.py:113` 覆盖 orchestrator 传递模板和上下文给工具。
- `backend/tests/unit/test_agent_orchestrator.py:97` 到 `backend/tests/unit/test_agent_orchestrator.py:99` 断言 rule tool 拿到 `JobTemplate` 和 `ReviewContext`。
- `backend/tests/unit/test_agent_orchestrator.py:107` 到 `backend/tests/unit/test_agent_orchestrator.py:109` 断言 LLM tool 拿到 `JobTemplate` 和 `ReviewContext`。
- `backend/tests/integration/test_rule_tool_flow.py:25` 覆盖规则失败不中断主链路。

## 实际验证

已运行 Day 2 相关测试：

```text
python -m pytest backend\tests\unit\test_agent_orchestrator.py backend\tests\integration\test_rule_tool_flow.py backend\tests\integration\test_llm_candidate_flow.py backend\tests\integration\test_audit_use_case.py -q -p no:cacheprovider
结果：12 passed
```

已运行后端全量测试：

```text
python -m pytest backend\tests -q -p no:cacheprovider
结果：45 passed
```

## 保留意见

Day 2 基本完成，但还有几个后续 Day 3/Day 4 需要继续处理的问题：

- `job_template` 和 `context` 在 `AgentOrchestrator.review()` 中仍是可选参数；如果后续进入真实评分和规则链路，建议明确哪些场景允许为空，哪些场景必须传入。
- `AdvantageDictionaryTool` 虽然能通过统一输入拿到 `job_template`，但还需要确认默认 registry 是否注册它，以及它的输出是否进入 Day 4 的 scoring signal。
- `AuditUseCase` 是否已经完全去掉评分硬编码属于 Day 4，不应算作 Day 2 的阻断项。
- 当前 Day 2 主要验证主路由和上下文传递，尚未验证完整候选 evidence gate 和真实 scoring signal。

## 审查结论

- 可以允许进入 Day 3。
- 不建议再回头质疑 Day 2 是否只是表面完成；当前有实现、有测试、有全量回归结果。
- 下一步审查重点应转向 Day 3：候选发现、evidence gate、rejected candidates 的来源和拒绝原因是否完整。
