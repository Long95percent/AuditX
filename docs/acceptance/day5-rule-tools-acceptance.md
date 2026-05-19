# Day 5 验收说明：优势词典与基础规则工具

## 验收目标

确认稳定规则作为工具接入，而不是绕过 `AgentOrchestrator`：

- 每条规则有单测。
- 规则输出为 `FindingCandidate` 或 scoring signal。
- 规则调用写入 `ReviewTrace`。
- 规则失败不影响主审查链路。
- API route 不直接调用规则工具。

## 已实现规则工具

- `resume.job.advantage_dictionary`：岗位优势词典命中，输出 advantage signals/tags。
- `resume.rule.contact_missing`：联系方式缺失，输出 finding candidate。
- `resume.rule.education_missing`：教育经历缺失，输出 finding candidate。
- `resume.rule.years_experience`：年限计算，输出 scoring signal。
- `resume.rule.keyword_match`：关键词命中，输出 scoring signal。

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
   - `ReviewTrace` 包含 `resume.rule.contact_missing`。
   - `Candidates` 中能看到 `rule_contact_missing`。
   - `rule_contact_missing` 显示 rejected，因为没有原文 evidence，不能成为正式 finding。
   - 正式 `Evidence` 中不出现无 evidence 的规则候选。

## API 手工验收

`POST /api/audit-jobs` 响应中应包含：

- `candidates` 包含规则候选。
- `rejected_candidates` 包含 `rule_contact_missing`。
- `trace.steps` 包含 `resume.rule.contact_missing`。
- `findings` 不包含 `rule_contact_missing`。
