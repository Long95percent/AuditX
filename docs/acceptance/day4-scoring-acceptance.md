# Day 4 验收说明：岗位匹配与评分引擎第一版

## 验收目标

确认审查结果不只列出风险，也能输出可解释评分：

- 维度分包含完整性、硬性要求、能力匹配、经历相关性。
- 岗位模板控制权重和优势词典。
- 硬性要求低分不会自动淘汰，可能进入“次优但有潜力”。
- 优势信号加分，风险数量扣分。
- Top N 支持默认值和 HR 自定义 N，并按分数、风险更少、优势更多、入库时间更新排序。
- 结果包含计算明细。

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
   - `Score & Layer` 显示总分。
   - 能看到 `frontend_engineer@v1`。
   - 能看到维度分。
   - 能看到优势标签。
   - 能看到计算明细，例如 `advantage_bonus`、`risk_penalty`。

## API 手工验收

`POST /api/audit-jobs` 响应中应包含：

- `score.total_score`
- `score.layer`
- `score.dimension_scores`
- `score.advantage_tags`
- `score.calculation_details`
