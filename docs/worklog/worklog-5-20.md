# Worklog 2026-05-20

## 架构审查与风险修复

- 审查 FastAPI 路由挂载、前端 API 调用、Tauri/Vite 启动配置，确认主路由没有明显混乱。
- 将审计任务创建与执行拆开：`POST /api/audit-jobs` 只创建任务并交给后台任务执行，避免真实 OCR/LLM 接入后请求长时间阻塞。
- 新增 `AuditJobService.create()` 与 `AuditJobService.run()`，保留 `create_and_run()` 兼容现有内部调用。
- 增加文档路径白名单配置 `AUDITX_ALLOWED_DOCUMENT_ROOTS`，后端只接受允许目录内的文件路径。
- 前端新增 `frontend/src/config.ts`，把 API base URL 收敛到 `VITE_AUDITX_API_BASE_URL` + 默认值，避免硬编码扩散。
- 前端提交审计任务后改为通过 `GET /api/audit-jobs/{job_id}` 短轮询获取最终结果，匹配任务化 API。
- 增加回归测试覆盖任务创建/运行拆分、API 创建任务、非法路径拒绝。

## 验证记录

- `uv run pytest backend/tests/integration/test_audit_jobs_api.py backend/tests/unit/test_audit_job_service.py`：6 passed。
- `uv run pytest`：51 passed。
- 测试时需设置 `UV_CACHE_DIR=.uv-cache`，否则当前机器默认 uv 缓存目录存在权限问题。
- Pytest 仍提示 `.pytest_cache` 写入权限警告，不影响测试结果，但建议后续清理本地权限异常目录。
## 持久化设施补强

- 根据产品要求补齐审计任务长期存储，不再把任务状态仅放在进程内内存。
- 新增 `SQLiteAuditJobRepository`，使用 Python 标准库 SQLite 保存 `AuditJob` 完整 JSON 快照。
- `AuditJobService` 改为依赖 repository 接口，默认仍可用内存仓储，API 依赖层接入 `.data/audit_jobs.sqlite3`。
- 后台任务在进入 `running` 和最终 `completed/failed` 时都会保存状态，进程重建后可通过 job_id 继续查询。
- 新增单元测试和 API 集成测试，覆盖新 repository 实例读取旧任务、service 重建读取旧任务、API service cache 重建后读取旧任务。
## Day3 候选发现与 Evidence Gate

- 当前执行 Day：Day3，范围限定为候选发现链路和 evidence gate，不进入 Day4 评分、批量、Top N 或真实联网搜索。
- 真实交付：`EvidenceValidator` 显式拒绝无 evidence 的正式风险，`AgentOrchestrator` 对 LLM/规则候选统一执行 evidence gate。
- 拒绝可追踪：`FindingCandidate` 增加 `rejection_reason`，`rejected_candidates` 和 trace metadata 保留 `candidate_id`、`source_agent`、`rejection_reason`、`evidence_count`。
- Mock 边界：当前 LLM 候选仍由 `LLMCandidateTool`/`LLMMockProvider` 提供，替换点是未来真实 LLM provider；证据门禁和 orchestrator 主入口为真实业务代码。
- Artifact 边界：本次没有新增大对象写入 job payload；LLM prompt/response、OCR 中间产物等大对象仍按策略进入后续 artifact 设施。
- 新增/修改测试：`backend/tests/unit/test_evidence_validator.py`、`backend/tests/integration/test_llm_candidate_flow.py`、`backend/tests/integration/test_rule_tool_flow.py`、`backend/tests/integration/test_audit_jobs_api.py`。
- 已运行定向验证：`uv run pytest backend/tests/unit/test_evidence_validator.py backend/tests/integration/test_llm_candidate_flow.py -q -p no:cacheprovider`，先红后绿，最终 4 passed。
- 已运行链路验证：`uv run pytest backend/tests/unit/test_evidence_validator.py backend/tests/integration/test_llm_candidate_flow.py backend/tests/integration/test_rule_tool_flow.py backend/tests/integration/test_audit_jobs_api.py -q -p no:cacheprovider`，11 passed。
- 最终验证：`uv run pytest backend/tests -q -p no:cacheprovider`，53 passed；`npm.cmd --prefix frontend run build`，TypeScript 与 Vite build 成功。