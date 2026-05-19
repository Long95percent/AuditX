# Day 2 验收说明：Agent 主路由骨架

## 验收目标

确认当前审查链路已经进入 Day 2 要求的 Agent-first 骨架：

- API route 只调用 application service。
- `AuditUseCase` 统一进入 `AgentOrchestrator`。
- 现有 fake extractor 被适配为 Orchestrator 可调用工具。
- 每次审查都会输出 `ReviewTrace`。
- 工具失败时主流程不中断，trace 中能看到失败原因。

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
2. 点击 `Check Backend`，确认 Backend 显示在线。
3. 点击 `Choose Document` 选择一份本地文件。
4. 点击 `Run Fake Audit`。
5. 点击 `Day 2 验收面板`。
6. 在面板中确认：
   - `Status` 为 `completed`。
   - `Document ID` 为 `fake_doc_001`。
   - `ReviewTrace` 至少包含 `agent.extractor.fake`。
   - trace step 的类型为 `tool`，状态为 `accepted`。
   - `Evidence` 能看到 quote、page、block、bbox。

## API 手工验收

启动后端后，用接口工具请求：

```text
POST http://127.0.0.1:8765/api/audit-jobs
```

请求体示例：

```json
{
  "file_path": "backend/tests/fixtures/demo_resume.pdf"
}
```

响应中应包含：

- `status: "completed"`
- `findings`
- `rejected_count`
- `trace.steps`
- `trace.steps[0].metadata.tool_name: "agent.extractor.fake"`
