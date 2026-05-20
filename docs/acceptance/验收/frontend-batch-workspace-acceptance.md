# AuditX 前端批量工作台验收说明

## 1. 验收目标

本说明用于验收 AuditX 当前前端是否已经从单份简历审查扩展到批量筛选工作台骨架。

当前应能验证：

- 单份审查仍可运行。
- 审查完成后结果会沉淀到简历库、候选人列表和 evidence index。
- 前端可以切换 Single Review / Batch Workspace。
- 批量工作台可以查看简历库、候选人、候选人详情、evidence、批次、Top N 排名。
- 可以创建批次、添加候选人、导入本地文件路径、同步运行 pending 候选人、retry failed 候选人。

当前不验收：

- 压测报告。
- 大规模并发 worker。
- Agent 自主规划。
- 真实 LLM 评估闭环。

## 2. 启动后端

推荐先用 fake OCR 快速验收，避免 PaddleOCR 初始化和模型下载影响前端验收节奏。

```powershell
$env:AUDITX_OCR_PROVIDER='fake'
$env:UV_CACHE_DIR='.uv-cache'
uv run uvicorn auditx.main:app --app-dir backend --host 127.0.0.1 --port 8765
```

后端启动后，浏览器访问下面地址应返回健康状态：

```text
http://127.0.0.1:8765/health
```

预期返回类似：

```json
{"status":"ok","env":"development"}
```

## 3. 启动前端

另开一个 PowerShell 窗口运行：

```powershell
npm.cmd --prefix frontend run dev
```

打开 Vite 输出的地址，通常是：

```text
http://localhost:5173
```

如果端口被占用，以终端实际输出为准。

## 4. 单份审查验收

进入页面后默认在 `Single Review`。

### 操作步骤

1. 点击 `Check Backend`。
2. 确认右侧状态显示 backend online。
3. 点击 `Choose Document`。
4. 选择一个本地 PDF 简历。
5. 点击 `Run Fake Audit`。
6. 等待任务完成。

### 预期结果

- 页面显示审查状态为 `completed`。
- `HR Review Summary` 显示 score、layer、risk count、evidence anchors。
- `Document` 区域能显示 PDF 预览。
- `Findings` 区域能看到风险 finding。
- 点击 finding 内的 `Highlight in PDF` 后，PDF 页面出现高亮框。
- `Agent Trace` 区域能看到 trace steps。

### 验收边界

- 当前按钮仍叫 `Run Fake Audit`，因为 LLM 真实接入仍延后。
- fake OCR 模式用于快速验收系统闭环，不代表 PaddleOCR 真实 OCR 未接入。

## 5. 审查结果沉淀验收

单份审查完成后，切换到 `Batch Workspace`。

### 操作步骤

1. 点击顶部 `Batch Workspace`。
2. 点击 `Refresh`。

### 预期结果

- `Resume Library` 中出现刚刚审查过的简历记录。
- `Candidates` 表格中出现候选人记录。
- 候选人应显示 name、layer、score、risk。
- 点击候选人行的 `Detail`。
- `Candidate Detail` 显示候选人摘要、scores、findings、evidence index。

### 验收边界

- 候选人画像当前是系统投影出的最小画像，姓名和摘要可能还比较粗。
- 后续可以继续增强 OCR/LLM 字段抽取，但当前验收重点是数据链路和 UI 骨架。

## 6. 候选人筛选验收

### 操作步骤

1. 在 `Candidates` 表格上方选择 layer，例如 `Best`。
2. 输入 `Min score`，例如 `60`。
3. 输入 `Max risks`，例如 `3`。
4. 点击 `Apply`。

### 预期结果

- 候选人列表按筛选条件刷新。
- 结果来自后端 `GET /api/candidates`，不是前端假过滤。

## 7. 批次创建和添加候选人验收

### 操作步骤

1. 点击 `Create Draft Batch`。
2. 在候选人表格中点击某个候选人的 `Add`。
3. 查看 `Draft Batch` 区域。

### 预期结果

- `Draft Batch` 显示批次名称、模板、候选人数。
- 被添加候选人显示在批次候选人列表中。
- 候选人初始状态通常是 `pending`。

## 8. Top N 排名验收

### 操作步骤

1. 确保批次中已有候选人，且候选人已有 score。
2. 点击 `Rerank Top 10`。

### 预期结果

- 批次状态更新为 `completed`。
- 批次候选人出现 `rank`。
- Top N 候选人状态为 `shortlisted`。
- 非 Top N 候选人状态为 `eliminated`。
- 页面展示 included / eliminated reason。
- `Current Top N` 区域显示当前入围候选人。

### 排名规则

当前排名规则为：

```text
total_score 降序 -> risk_count 升序 -> candidate_id 稳定排序
```

## 9. 批量文件导入验收

### 操作步骤

1. 创建或选择一个批次。
2. 点击 `Import Files`。
3. 选择多个本地简历文件。
4. 导入完成后点击 `Refresh`。

### 预期结果

- 选中的文件会作为候选人加入当前批次。
- 候选人画像会记录本地文件路径。
- 数据库只保存结构化元信息和路径/引用，不复制 PDF 大对象到主表。

## 10. 同步批量运行验收

### 操作步骤

1. 确保批次中存在通过 `Import Files` 导入的 pending 候选人。
2. 点击 `Run Pending`。

### 预期结果

- 系统会同步逐个复用单份审查链路处理候选人。
- 成功候选人状态变为 `reviewed`。
- 失败候选人状态变为 `failed`，并显示 error。
- 单个候选人失败不应导致整个批次页面不可用。

### 验收边界

- 当前是同步运行，不是并发 worker。
- 大批量运行时 UI 可能等待较久；正式并发队列属于后续能力。

## 11. 失败 Retry 验收

### 操作步骤

1. 如果批次中存在 failed 候选人，点击 `Retry Failed`。
2. 再点击 `Run Pending`。

### 预期结果

- failed 候选人会被重置为 `pending`。
- 再次运行后，成功则变为 `reviewed`，失败则重新写入 error。

## 12. 候选人 PDF Evidence 高亮验收

### 操作步骤

1. 在 `Batch Workspace` 中点击候选人的 `Detail`。
2. 在 evidence 列表中点击 `Highlight PDF`。

### 预期结果

- 候选人详情区域展示 PDF viewer。
- PDF viewer 加载候选人的 source document artifact。
- 使用候选人的 parsed document artifact 进行坐标缩放。
- 选中的 evidence bbox 被高亮。

### 验收边界

- 只有已经完成审查并产生 source document / parsed document artifact 的候选人才支持 PDF 高亮。
- 纯手动 import 但尚未 run 的候选人没有可高亮 PDF artifact。

## 13. 当前已知边界

- 当前没有压测报告。
- 当前没有真正并发 worker。
- 当前没有 Agent 自主评估。
- 当前 LLM 真实接入仍延后。
- 当前批量运行是系统骨架级同步运行，适合功能验收，不适合大批量性能验收。

## 14. 验收通过标准

可以认为当前前端批量工作台验收通过，当以下全部满足：

- 单份审查能跑通。
- 审查结果能在 Batch Workspace 中看到。
- 候选人列表、详情、evidence index 能读取。
- 可以创建批次并添加候选人。
- 可以导入多个文件路径到批次。
- 可以运行 pending 候选人。
- failed 候选人可以 retry。
- 可以 rerank 并看到 Top N。
- 已完成审查的候选人可以从 evidence 打开 PDF 高亮。
