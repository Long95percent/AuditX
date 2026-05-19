# MVP 人工验收指南

> 适用范围：单份简历审查 MVP。  
> 本指南只用于人工验收，不代表批量、简历库、Top N 或压测已经完成。

## 1. 验收前准备

确认你在项目根目录：

```text
D:\github_desktop\AuditX
```

建议使用项目根目录的启动脚本：

```text
启动AuditX桌面应用.bat
```

如果依赖已经装过，也可以用快速启动：

```text
快速启动AuditX桌面应用.bat
```

启动后预期看到一个 Tauri 桌面窗口，页面标题为 `AuditX / VeriDoc`。

## 2. 最短验收路径

1. 点击 `Check Backend`。
2. 确认右侧状态显示 `Backend: ok (...)` 或类似在线状态。
3. 点击 `Choose Document`。
4. 选择一个本地 PDF 文件。可以使用：

```text
backend\tests\fixtures\demo_resume.pdf
```

5. 确认页面显示已选择的文件名和文件路径。
6. 点击 `Run Fake Audit`。
7. 等待按钮恢复，确认 `Audit: completed`。

## 3. 主页面必须看到的内容

### 3.1 HR Review Summary

在主页面顶部工作区，应看到 `HR Review Summary` 卡片。

需要检查：

- `Match Score` 有数字。
- 有候选人分层，例如 `best`、`potential` 或 `not recommended`。
- 有模板信息，例如 `frontend_engineer@v1`。
- 有优势标签，或者明确显示 `none`。
- 有风险数量。
- 有多个维度分，例如完整性、硬性要求、能力匹配、经历相关性。

验收判断：有分数、有分层、有维度分，说明评分结果已经从后端进入前端展示。

### 3.2 Findings

在 `Findings` 区域，应看到正式风险/提示卡片。

每个 finding 至少要检查：

- 标题。
- 风险级别。
- 描述。
- 规则 ID。
- 置信度。
- 来源 Agent / Tool。
- 建议。

重点检查 evidence：

- 有 `Evidence quote`。
- 有 `Page`。
- 有 `Block`。
- 有 `BBox` 坐标。

验收判断：正式 finding 必须有 evidence quote 和 bbox；如果没有证据，不应该出现在正式 findings 中。

### 3.3 Rejected Candidates

在 `Rejected Candidates` 区域，应看到未进入正式风险的候选项。

需要检查：

- 有 candidate 标题。
- 有 risk level。
- 有 candidate ID。
- 有 source。
- 有 evidence 数量。
- 有“未进入正式风险”的说明。

验收判断：没有证据或无法验证的候选风险，应保留在 rejected candidates，而不是进入正式 findings。

### 3.4 Agent Trace

在 `Agent Trace` 区域，应看到审查链路执行摘要。

需要检查：

- 有总步骤数 `Steps`。
- 有 `Accepted` 数量。
- 有 `Failed` 数量。
- trace 列表里能看到类似：
  - `agent.extractor.fake`
  - `agent.llm_mock.candidate_discovery`
  - `resume.rule.*` 或 `resume.job.*`
  - `evidence_validator.validate`
  - `scoring_engine.score`

验收判断：trace 覆盖 extractor、LLM mock、规则/岗位工具、evidence gate 和 scoring，说明不是前端硬编码结果。

## 4. 验收 / 测试中心

点击主页面的 `验收 / 测试中心`。

建议按顺序打开这些面板：

1. `Runtime`：检查 backend、audit job、document ID、rejected count。
2. `Agent / Tool Trace`：查看完整 trace step。
3. `Candidates`：查看所有候选风险和 rejected 状态。
4. `Score / Layer`：查看分数、分层、维度分、计算明细。
5. `Evidence`：查看正式 finding 的证据 quote、page、block、bbox。
6. `OpenAI 设置 / JD 模板`：只检查入口存在即可；没有 API key 时不应 fallback 到规则解析。

验收判断：测试中心用于辅助核对，主页面才是 HR 正常产品视图。

## 5. 通过标准

一次 MVP 人工验收可以认为通过，需要同时满足：

- 桌面应用能启动。
- backend 状态在线。
- 能选择本地文件。
- 能点击 `Run Fake Audit` 并完成审查。
- 主页面显示 score、layer、dimension scores、advantage tags。
- 主页面显示正式 findings。
- 正式 findings 有 evidence quote、page、block、bbox。
- 主页面显示 rejected candidates。
- Agent Trace 覆盖 extractor、LLM mock、resume tools、evidence gate、scoring。
- 验收 / 测试中心各面板能打开，不影响主流程。

## 6. 不通过情况

以下任一情况应视为不通过：

- 桌面窗口打不开。
- backend 一直 offline。
- 无法选择本地文件。
- 点击 `Run Fake Audit` 后报错或长时间不返回。
- 有正式 finding 但没有 evidence quote 或 bbox。
- score 区域为空。
- trace 中看不到 `scoring_engine.score`。
- trace 中看不到 Agent / Tool 执行步骤，只显示静态文本。
- rejected candidates 为空但同时存在明显无证据候选进入正式 findings。

## 7. 当前已知限制

这些不属于本次 MVP 人工验收失败：

- 仍然使用 fake parser。
- 仍然使用 LLM mock。
- 暂不做真实 OCR。
- 暂不做真实 PDF 页面渲染。
- 暂不做真实网页搜索。
- 暂不做简历库列表页。
- 暂不做批量任务。
- 暂不做 Top N 当前批次排序。
- OpenAI 岗位模板功能只是接口骨架；没有 API key 时应明确失败，不应 fallback 到规则解析。

## 8. 建议记录方式

人工验收时建议记录：

```text
验收时间：
启动方式：启动AuditX桌面应用.bat / 快速启动AuditX桌面应用.bat / 手动命令
测试文件：
Backend 状态：
Audit 状态：
Score：
Layer：
Findings 数量：
Rejected candidates 数量：
Trace 是否包含 scoring_engine.score：是 / 否
是否通过：是 / 否
问题截图或备注：
```
