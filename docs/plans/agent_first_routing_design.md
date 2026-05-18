# Agent 优先的审查路由设计

## 1. 背景问题

之前容易踩坑的点是：规则路由和 Agent 路由混在一起，规则层过早决定“该走哪个能力”，导致：

- Agent 能力被绕开，系统只能跑死规则。
- 链路分支过多，输入输出不统一。
- 某条规则失败后影响整个审查流程。
- 新增 Agent、工具或岗位模板时需要改很多路由代码。
- 规则和 Agent 都在产出结论，责任边界不清，报错难排查。

后续应改成 **Agent 编排优先，规则工具化 / 校验化**。先确保工程链路可用，再根据测试结果逐步加入稳定规则。

## 2. 核心原则

- **Agent 是主流程编排者**：负责理解岗位、简历、上下文，决定需要调用哪些能力。
- **规则是工具，不是总路由**：规则用于检查明确问题、补充分数、提供可解释证据，不负责决定整条链路怎么走。
- **LLM 可以先多做一点**：早期为了保证可用性和产品体验，可以让 LLM 承担结构理解、风险候选发现、摘要生成。
- **规则逐步收敛**：从测试中发现高频、稳定、可判定的逻辑，再沉淀为规则。
- **所有输出统一归一化**：无论来自 LLM、规则、工具还是本地文件，都必须归一成统一的候选发现和证据结构。
- **正式结论必须可校验**：Agent 可以提出候选风险，但正式风险仍要经过证据校验、结构校验和置信度标记。

## 3. 推荐链路

```text
ResumeLibrarySelection + ParsedDocument + JobProfile
  -> AgentOrchestrator
  -> ResumeUnderstandingAgent
  -> JobMatchingAgent
  -> RiskDiscoveryAgent
  -> Tool / Rule Calls
  -> EvidenceCollector
  -> FindingNormalizer
  -> ScoringAndLayering
  -> ReviewReport
```

其中 `AgentOrchestrator` 是唯一主路由入口。外层业务代码不直接判断“这条简历该走哪个规则”，而是把文档、岗位模板和可用工具交给 Orchestrator。

如果简历来自简历库，Orchestrator 还应接收简历状态和历史审查上下文。已筛查简历可以复用解析结果、结构化信息和历史证据，但当前岗位 / 当前批次的 rank、Top N 和分层必须重新计算。

## 4. 路由职责划分

### 4.1 AgentOrchestrator

职责：

- 接收文档、岗位模板、运行配置。
- 接收简历库输入选择、简历状态和可复用历史上下文。
- 决定调用哪些 Agent、工具和规则。
- 汇总中间结果。
- 捕获单个步骤失败，保证主流程尽量继续。
- 输出统一的 `ReviewReportDraft`。

不做：

- 不直接写具体岗位规则。
- 不直接依赖某个外部 LLM SDK。
- 不直接操作前端展示结构。

### 4.2 Agent

Agent 负责语义理解和分析：

- `ResumeUnderstandingAgent`：提取候选人基础信息、教育、工作、项目、技能。
- `JobMatchingAgent`：分析简历和岗位模板的匹配程度。
- `RiskDiscoveryAgent`：发现潜在风险和不确定点。
- `EvidenceAgent`：寻找简历原文、本地文件或工具返回的证据。
- `ReportAgent`：生成 HR 可读摘要、优势标签、复核建议。

Agent 产出的是候选分析，不直接绕过后续校验。

### 4.3 Rule Tool

规则应作为可调用工具存在：

- 输入：结构化简历、岗位模板、当前 Agent 上下文。
- 输出：规则命中、证据候选、分数影响、解释。
- 失败：返回错误状态，不中断整个审查。

规则适合沉淀这些稳定逻辑：

- 手机号 / 邮箱缺失。
- 工作时间重叠。
- 年限计算。
- 关键词命中。
- 公司名称模糊。
- OCR 低置信度提示。

规则不应负责：

- 判断整份简历是否通过。
- 决定是否调用 Agent。
- 拼接 LLM prompt。
- 直接生成最终报告。

### 4.4 Tool Registry

所有规则、公司信息、本地证据库、岗位词典都通过统一工具注册：

```text
AgentOrchestrator
  -> ToolRegistry.get("resume.rule.contact_missing")
  -> ToolRegistry.get("resume.company.mock_lookup")
  -> ToolRegistry.get("resume.job.advantage_dictionary")
```

这样 Agent 能力和规则能力都通过统一接口接入，避免代码里到处写 if/else 路由。

## 5. LLM 放权边界

为了先确保能用，早期可以给 LLM 更多职责：

- 简历结构理解。
- 岗位要求归纳。
- 优势标签提取。
- 风险候选发现。
- 复核建议生成。
- 对规则结果做解释整合。

但必须保留以下边界：

- LLM 不能直接写入最终 `AuditFinding`，只能写入候选发现。
- LLM 不能伪造 evidence，证据必须来自 `ParsedDocument` 或已注册工具。
- LLM 输出必须标记来源：模型判断、规则命中、工具结果、本地证据。
- 低置信度输出进入“待复核”，不要当作高风险事实。
- LLM 调用失败时，系统应降级到基础规则和解析结果，不让整个任务崩掉。

## 6. 数据结构建议

### 6.1 中间候选发现

Agent 和规则都先输出 `FindingCandidate`：

```text
FindingCandidate
  id
  source_type: llm | rule | tool
  source_name
  category
  title
  description
  confidence
  severity_hint
  evidence_candidates
  scoring_impact
  uncertainty_notes
  debug_trace_id
```

候选发现可以不完全满足正式 finding 要求，但必须带来源和不确定性。

### 6.2 正式风险

只有通过归一化和证据校验后，才转成正式 `AuditFinding`：

```text
FindingCandidate
  -> EvidenceCollector
  -> EvidenceValidator
  -> FindingNormalizer
  -> AuditFinding
```

不能通过校验的候选发现不丢弃，可以放到“待人工确认 / 未采纳原因”里，供调试和产品评估。

### 6.3 调试轨迹

为了避免后续链路不稳定时难排查，每次审查都保留 trace：

```text
ReviewTrace
  job_id
  document_id
  resume_status
  input_selection_source
  job_template_version
  reused_context
  agent_steps
  tool_calls
  rule_calls
  failed_steps
  rejected_candidates
  final_findings
```

HR 默认不看完整 trace，但产品和开发可以用它定位“为什么没用上 Agent”或“为什么某条风险没出现在结果里”。

## 7. 错误隔离与降级

主流程必须允许局部失败：

| 失败点 | 降级策略 |
|---|---|
| LLM 不可用 | 只跑基础规则和本地工具，报告标记“智能分析不可用” |
| 某个规则报错 | 记录 failed rule，继续其它规则和 Agent |
| 本地公司库查询失败 | 风险降级为“不确定”，不作为高风险事实 |
| evidence 校验失败 | 候选发现进入 rejected_candidates，不进入正式风险 |
| OCR 低置信度 | 标记低置信度，降低相关结论置信度 |

核心目标是：**任何单个 Agent、规则或工具失败，都不应导致整份简历审查失败。**

## 8. 测试策略

### 8.1 路由测试

必须测试 Agent 是否真的被调用：

- Orchestrator 收到简历和岗位模板后，会调用指定 Agent。
- 规则工具失败时，Agent 流程仍继续。
- LLM mock 返回候选风险后，能进入 evidence 校验。
- 未通过 evidence 校验的候选不会成为正式风险。

### 8.2 回归测试

每次新增规则前，先用黄金测试集确认：

- 是否提升了稳定性。
- 是否误伤了“次优但有潜力”候选人。
- 是否改变了已有岗位模板下的分层结果。
- 是否导致 Agent 分析被绕开。

### 8.3 Trace 测试

需要断言 trace 中包含：

- 调用了哪些 Agent。
- 调用了哪些规则。
- 哪些候选被采纳。
- 哪些候选被拒绝以及原因。

这比只断言最终风险列表更重要，因为它能防止“结果看似有，实际没走 Agent”的问题。

## 9. 实施顺序建议

1. 先建立 `AgentOrchestrator` 作为唯一审查路由入口。
2. 把现有 fake / rule extractor 适配成 Orchestrator 可调用工具。
3. 引入 `FindingCandidate`，让 Agent 和规则都先产出候选发现。
4. 建立 `ReviewTrace`，记录 Agent、规则、工具调用路径。
5. 接入 LLM mock，实现端到端 Agent 路径。
6. 再逐步沉淀稳定规则，不要一开始让规则决定主流程。
7. 每加一条规则，都补一条“不会绕开 Agent”的路由测试。

## 10. 审查红线

- 不允许在 API route 里写规则分发逻辑。
- 不允许在前端决定走哪个 Agent 或规则。
- 不允许规则层直接跳过 AgentOrchestrator。
- 不允许 LLM 输出无证据正式风险。
- 不允许单个工具失败导致整份简历审查失败。
- 不允许新增规则但没有路由 trace 测试。
