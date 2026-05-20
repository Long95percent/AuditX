# AuditX 当前执行焦点梳理

这份文档不是新的宏大规划，而是用来帮你在当前阶段判断：**现在该做什么、暂时不要做什么、存储应该怎么先落地**。

当前项目最容易混乱的原因，是产品目标、Agent 能力、存储设施、LLM 联网搜索、5000 份压测同时出现了。它们都重要，但不能同时进入实现主线。

## 1. 当前一句话目标

先把 **单份简历审查 MVP** 做成真实可用闭环，再扩展到简历库、批量、Top N 和压测。

当前阶段不要追求“最终企业级架构”，而是追求：

- 路由清楚。
- 数据契约稳定。
- Agent 主流程不乱。
- 结果能长期保存。
- 后续可以自然扩展，不推倒重来。

## 2. 现在只看哪些计划文档

当前执行时优先看：

1. `docs/plans/README.md`
   - 用来确认产品方向和计划入口。

2. `docs/plans/12_day_execution_plan.md`
   - 当前唯一执行排期。
   - 每次开发只从这里取一个最小任务。

3. `docs/plans/agent_first_routing_design.md`
   - 只在改 Agent、工具、trace、evidence gate 时参考。

4. `docs/plans/resume_review_scoring_and_presentation_design.md`
   - 只在改评分、分层、Top N、列表页时参考。

不要同时打开所有设计文档然后一起实现。这样会把 Day 1、Day 8、Day 12 的事情混在一起。

## 3. 阶段划分

### Phase 1：Day 1-6，单份简历真实 MVP

目标：一份简历可以完成完整审查闭环。

必须完成：

- 简历输入。
- 文档解析。
- AgentOrchestrator 主流程。
- LLM mock / 规则工具候选发现。
- Evidence gate。
- 正式 findings。
- scoring。
- trace。
- 前端详情页展示。
- 审计任务长期保存。

这个阶段不要做：

- 批量任务。
- Top N。
- 5000 份压测。
- 真实网页搜索。
- 完整企业级权限。
- 复杂数据库选型。

### Phase 2：Day 7-10，简历库和小批量

目标：从“单份审查”扩展为“简历库 + 当前批次”。

开始引入：

- `resumes`。
- 简历状态：新入库、已筛查、已入岗位候选库。
- 批量任务。
- batch item。
- 列表页。
- 当前批次 Top N。
- 分页、筛选、排序。

这个阶段仍然不要做：

- 真实联网搜索。
- 大规模外部服务依赖。
- 10 万级架构。

### Phase 3：Day 11-12，证据库和压测

目标：证明系统能稳定处理更大样本，而不是靠假 demo。

开始做：

- 本地模拟证据库。
- 100 / 500 / 1000 分级压测。
- 5000 份累计压测。
- 压测报告。
- 失败原因记录。

如果 1000 份不稳定，不要硬上 5000。应该先记录阻断原因，然后修基础设施。

## 4. 存储现在怎么想

现在不要纠结“最终到底用 SQLite、PostgreSQL、向量库还是对象存储”。

当前正确思路是：**先定义数据分层**。

### SQLite 存什么

SQLite 适合存结构化、小而关键的数据：

- audit job 状态。
- resume 元信息。
- batch 元信息。
- score 摘要。
- finding 摘要。
- trace 摘要。
- artifact 引用。
- 创建时间、更新时间、错误信息。

### 文件 artifact 存什么

大对象不要直接塞进 SQLite 主表。

这些应该放到本地 artifact 目录：

- LLM prompt。
- LLM response。
- 网页搜索原文。
- 搜索结果快照。
- OCR 文本。
- 简历解析中间产物。
- 压测报告。
- 大型 trace 明细。

SQLite 只保存类似这样的引用：

```text
artifact_uri = local://artifacts/2026-05-20/job_xxx/llm_response_001.json
artifact_type = llm_response
sha256 = ...
size_bytes = ...
created_at = ...
```

这样未来即使迁移到 PostgreSQL + 对象存储，也不需要重写业务逻辑。

## 5. 当前存储最低可用方案

当前阶段建议先做到这个程度：

```text
.data/
  auditx.sqlite3
  artifacts/
    jobs/
    resumes/
    llm_runs/
    web_search_runs/
    pressure_tests/
```

SQLite 里先有这些概念即可：

- `audit_jobs`
- `job_artifacts`
- 后续再加 `resumes`
- 后续再加 `batches`
- 后续再加 `batch_items`

不要一开始就把所有表做完。先保证 Day 1-6 的 job 和 result 可恢复。

## 6. LLM 和联网搜索先怎么放

LLM 和联网搜索现在先不要进入主链路。

当前只需要预留位置：

- LLM 调用记录以后属于 `llm_runs`。
- 联网搜索以后属于 `web_search_runs`。
- 两者的大内容都应该是 artifact。
- 正式 finding 只能引用经过 evidence gate 的证据。

当前不要让“未来可能联网搜索”影响 Day 1-6 的实现节奏。

## 7. 5000 份压测先怎么想

5000 份压测不是现在立刻要实现的功能，而是后面验证架构的手段。

现在只需要避免明显会阻塞压测的设计：

- 不要把所有任务存在内存里。
- 不要让 POST 请求同步处理完整审查。
- 不要把所有大文本塞进一个 JSON 字段。
- 不要让单份失败导致整个批次失败。
- 不要让列表页一次性加载全部数据。

真正做压测时，再关注：

- 每份简历处理耗时。
- 单批失败率。
- 查询分页响应。
- artifact 总大小。
- SQLite 写入瓶颈。
- 是否需要 worker 队列。

## 8. 每次开发前的判断问题

每次开工前先问这 5 个问题：

1. 这个任务属于 Day 1-6、Day 7-10，还是 Day 11-12？
2. 它是否阻塞单份简历 MVP？
3. 它是否会让路由更清楚，还是更混乱？
4. 它的数据是结构化状态，还是大对象 artifact？
5. 它有没有测试能证明不会破坏主链路？

如果一个任务不属于当前阶段，就先写到“暂缓”，不要现在实现。

## 9. 当前推荐执行顺序

接下来建议按这个顺序推进：

1. 稳定 `audit_jobs` 持久化。
2. 增加 artifact store 最小接口。
3. 把大 trace / LLM mock 输出预留为 artifact，而不是继续膨胀 job payload。
4. 完成 Day 1-6 的单份详情页闭环。
5. 再开始设计 `resumes` 和简历库状态。
6. 再做 batch / Top N。
7. 最后做压测。

## 10. 当前不要做的事

为了避免工作流继续混乱，当前不要做：

- 不要立刻换 PostgreSQL。
- 不要立刻接真实网页搜索。
- 不要立刻做 5000 份压测。
- 不要一口气设计所有最终表结构。
- 不要把 LLM 上下文和网页搜索结果塞进 `audit_jobs.payload`。
- 不要为了未来复杂场景牺牲当前 MVP 闭环。

## 11. 总结

现在的关键不是马上选一个“最终存储方案”，而是建立一个不会走偏的工作流：

```text
单份真实 MVP
  -> 最小持久化
  -> artifact 分层
  -> 简历库
  -> 批量任务
  -> Top N
  -> 分级压测
  -> 再决定是否升级数据库设施
```

这样项目不会因为未来需求太大而停在设计阶段，也不会因为 MVP 太简陋导致后面全部推倒重来。