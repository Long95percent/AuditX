# Day 1 验收说明：MVP 数据契约

## 验收目标

确认后续 Agent、规则、评分、前端展示依赖的数据结构已经稳定：

- `ResumeStatus` 状态枚举固定为 `new`、`reviewed`、`shortlisted`。
- `ResumeRecord` 能记录简历 ID、文件名、入库时间、状态、解析结果引用。
- `ReviewContext` 能携带岗位模板、运行配置、历史上下文、是否复用解析结果。
- `JobTemplate` 包含硬性要求、优势词典、权重、风险策略、模板版本。
- 已有前端、财务、产品经理 3 个岗位模板样例，且 ID、权重、优势词典不同。
- `AuditResult` 暴露 score、findings、candidates、rejected_candidates、trace 等结果字段。

## 自动化验收

在项目根目录运行：

```powershell
python -m pytest backend\tests\unit\test_day1_data_contracts.py -q -p no:cacheprovider
python -m pytest backend\tests -q -p no:cacheprovider
npm.cmd --prefix frontend run build
```

期望结果：

- Day 1 契约测试全部通过。
- 后端全量测试通过。
- 前端 TypeScript 编译和 Vite build 成功。

## 重点测试文件

- `backend/tests/unit/test_day1_data_contracts.py`

## 后续约束

Day 2 之后扩展 `AgentOrchestrator` 输入时，应优先使用 `ReviewContext`，而不是继续把岗位模板、运行配置、历史上下文散落在 use case 或工具参数中。
