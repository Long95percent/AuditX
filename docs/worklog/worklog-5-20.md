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
## Day4 评分 Signals 接入

- 当前执行 Day：Day4，范围限定为去掉演示评分硬编码、接入 scoring signals，不进入 Day5 前端详情页、批量、Top N 或真实联网搜索。
- 真实交付：新增 `ScoringSignal` 数据契约，规则工具输出结构化 scoring signals，`AuditUseCase` 从 trace metadata、正式 findings、候选和 rejected candidates 构建 `CandidateScoreInput`。
- 评分来源：岗位模板权重、简历解析完整度、关键词/硬性要求 signal、优势词典 signal、经验年限 signal、正式风险和 rejected candidate 数量。
- 计算明细：`ScoreResult.calculation_details` 写入 `signal:<id> source=<step>`，`scoring_engine.score` trace metadata 记录结构化 `scoring_signals`。
- Mock 边界：fake parser、LLM mock、规则工具仍可作为测试输入；评分 signal 聚合、score input 构建和计算明细为真实业务代码。
- Artifact 边界：本次没有新增大对象写入 job payload；LLM/OCR 大对象仍按 artifact 策略后续落地。
- TDD 红灯：新增规则 signal 和 score details 来源测试后，`uv run pytest backend/tests/unit/test_rule_tools.py backend/tests/integration/test_scored_audit_result.py -q -p no:cacheprovider` 先失败 4 项。
- 定向验证：同一命令修复后 9 passed。
- 最终验证：`uv run pytest backend/tests -q -p no:cacheprovider`，54 passed；`npm.cmd --prefix frontend run build`，TypeScript 与 Vite build 成功。
## Day5 单份简历 MVP 前端闭环

- 当前执行 Day：Day5，范围限定为单份简历审查详情页和验收说明，不进入 Day6 闭环总验收、批量、Top N、简历库或真实联网搜索。
- 真实交付：主工作台展示审查状态、score、layer、dimension scores、advantage tags、calculation details、正式 findings、evidence quote/page/block/bbox、rejected candidates 和完整 ReviewTrace。
- 类型对齐：前端 `FindingCandidate` 补齐 `rejection_reason`，与 Day3/Day4 API response 对齐。
- Trace 展示：主页面不再只展示前 6 条 trace，改为展示所有 step，并展示 input/output/error/metadata。
- Rejected candidate 展示：拒绝候选显示真实 `rejection_reason`，不再只写固定文案。
- Mock 边界：fake parser、LLM mock、规则工具仍作为本地审查输入；前端工作台和 API 字段消费是真实业务 UI，后续可承接真实 OCR/LLM。
- Artifact 边界：本次没有新增大对象写入 job payload；大对象仍按 artifact 策略后续落地。
- 新增验收文档：`docs/acceptance/day5-single-resume-mvp.md`。
- TDD 红灯：前端先引用 `candidate.rejection_reason` 后，`npm.cmd --prefix frontend run build` 失败于 TypeScript 类型缺口。
- API 验收：补强 `backend/tests/integration/test_audit_jobs_api.py`，断言 score/layer/dimensions/findings/evidence/rejected candidates/trace/scoring metadata。
- 最终验证：`uv run pytest backend/tests -q -p no:cacheprovider`，54 passed；`npm.cmd --prefix frontend run build`，TypeScript 与 Vite build 成功。
## Day6 MVP 闭环验收

- 当前执行 Day：Day6，范围限定为 Day1-Day5 单份 MVP 闭环验证和缺口修复，不进入批量、Top N、简历库、压测或真实联网搜索。
- 基线验证：先运行 `uv run pytest backend/tests -q -p no:cacheprovider`，54 passed；`npm.cmd --prefix frontend run build` 成功。
- 缺口修复：补充同一份简历在不同岗位模板下匹配结果不同的集成测试 `test_same_resume_gets_different_match_results_across_job_templates`。
- 验收报告：新增 `docs/acceptance/day6-mvp-closure.md`，逐条核对 MVP 门槛、mock 边界、自动化命令、手工验收和 go/no-go。
- Mock 边界：fake parser 和 LLM mock 仍保留；AgentOrchestrator、EvidenceValidator、scoring signal、API 任务持久化和前端复核工作台为真实业务链路。
- 遗留风险：真实 OCR/parser、真实 LLM provider、PDF bbox 高亮和 artifact 大对象拆分仍待后续 Day/阶段处理。
- 最终验证：`uv run pytest backend/tests -q -p no:cacheprovider`，55 passed；`npm.cmd --prefix frontend run build`，TypeScript 与 Vite build 成功。
- Go/No-Go：Go，允许进入 Day7 测试数据和黄金集阶段。
## 遗留链路补强：Artifact、PaddleOCR 接口、PDF 预览

- 本轮范围：补齐 artifact 大对象拆分基础、PaddleOCR parser seam、源 PDF artifact、受控 PDF endpoint、前端 PDF preview 和 evidence bbox 高亮信息卡。
- Artifact：新增 `ArtifactRef` 与 `FileSystemArtifactStore`，审查任务运行时把源 PDF 写为 `source_document` artifact，job/API 只保存 artifact refs。
- OCR：新增 `PaddleOCRDocumentParser`，使用懒加载；未安装 PaddleOCR 时明确报错。`pyproject.toml` 增加 optional `ocr` 依赖组，真实启用时运行 `uv sync --extra ocr`。
- PDF 展示：新增 `GET /api/audit-jobs/{job_id}/document` 受控返回源 PDF；前端用 PDF object preview 展示源文件，并显示 evidence page/block/bbox 高亮信息。
- LLM/API：LLM 仍先放着，API key 由用户填写；没有把真实 LLM 接入主链路。
- 后续已闭环：默认 parser 已切换 PaddleOCR；PDF 精准 overlay 已引入 `pdfjs-dist`；真实 OCR 已写入 `ocr_raw` 与 `parsed_document` artifacts。
- 验证：定向 artifact/service/parser/API 测试 4 passed；`uv run pytest backend/tests -q -p no:cacheprovider`，58 passed；`npm.cmd --prefix frontend run build` 成功。
## 真实 OCR 默认链路切换

- 默认 OCR provider 已从占位切换为 `paddleocr`，依赖层新增 `build_document_parser()`，测试可通过 `AUDITX_OCR_PROVIDER=fake` 使用 fake parser。
- 已执行 `uv sync --extra ocr` 安装 PaddleOCR/PaddlePaddle optional 依赖。
- 修复 PaddleX 默认缓存目录无权限问题：`PaddleOCRDocumentParser` 在导入前设置 `PADDLE_PDX_CACHE_HOME=.data/paddlex_cache`。
- 验证 PaddleOCR 实例化成功，并下载模型到 `.data/paddlex_cache`。
- 回归验证：`$env:AUDITX_OCR_PROVIDER='fake'; uv run pytest backend/tests -q -p no:cacheprovider`，60 passed；`npm.cmd --prefix frontend run build` 成功。
- 注意：常规自动化测试仍用 fake parser 避免真实 OCR 下载/耗时；真实运行默认走 PaddleOCR。
## OCR Raw 与 ParsedDocument Artifact 闭环

- 新增 `PaddleOCRDocumentParser.parse_with_artifacts()`，真实 OCR 路径会写入 `ocr_raw` 和 `parsed_document` artifacts。
- `AuditJobService` 现在把 `job_id` 和 `artifact_store` 传入 `AuditUseCase.run()`，同时兼容旧测试 stub。
- `AuditUseCase` 检测 parser 支持 `parse_with_artifacts` 时使用 artifact-aware parse，并把 artifacts 写回 `AuditResult`。
- `FileSystemArtifactStore` 新增 `write_json()`，用于保存 OCR raw JSON。
- 验证：parser/artifact/dependency 定向测试 5 passed；`$env:AUDITX_OCR_PROVIDER='fake'; uv run pytest backend/tests -q -p no:cacheprovider`，62 passed；`npm.cmd --prefix frontend run build` 成功。
## 真实 PDF OCR 验证

- 使用用户提供的 `简历.pdf` 进行 PaddleOCR 端到端验证。
- 发现并修复 PaddleOCR 3.5 调用兼容问题：改用 `predict()` 并兼容 `rec_texts`/`rec_polys` 输出。
- 发现 PDF 直传 PaddleOCR 超时/执行异常，改为先用 `pypdfium2` 渲染 PDF 页面为 `.data/ocr_tmp/<pdf>_page_N.png`，再对图片运行 OCR。
- 将 PaddlePaddle 锁定为 `3.0.0`，规避 `3.3.1` 在当前 Windows 环境下的 `ConvertPirAttribute2RuntimeAttribute` 执行错误。
- 真实 OCR 结果：1 页，52 个 OCR blocks，成功写入 `ocr_raw` artifact 约 12014 bytes、`parsed_document` artifact 约 10162 bytes。
- 回归验证：`$env:AUDITX_OCR_PROVIDER='fake'; uv run pytest backend/tests -q -p no:cacheprovider`，64 passed；`npm.cmd --prefix frontend run build` 成功。

## PDF 展示与精准高亮闭环

- 本次范围：只补 PDF 展示、parsed artifact 读取、evidence bbox overlay 高亮，不接真实 LLM，不进入批量/Top N/简历库。
- 后端新增 `GET /api/audit-jobs/{job_id}/parsed-document`，从 `parsed_document` artifact 返回 OCR layout；job payload 仍只保留 artifact refs。
- PaddleOCR PDF 渲染链路现在把 `pypdfium2` 输出图片的真实 `page_width/page_height` 写入 parsed document，避免前端 overlay 使用 bbox 最大值导致比例误差。
- 前端新增 `PdfEvidenceViewer`，使用 `pdfjs-dist` canvas 展示 PDF，并按 parsed page 尺寸缩放 evidence bbox 生成精准高亮层。
- Finding evidence 增加 `Highlight in PDF` 操作，点击后更新主 PDF 视图、跳到 evidence 页并显示高亮框。
- Mock 边界：测试可继续用 `AUDITX_OCR_PROVIDER=fake`；真实 OCR/PDF layout artifact 由 PaddleOCR 链路生成，LLM 仍保持关闭等待 API 配置。
- 已运行验证：`$env:AUDITX_OCR_PROVIDER='fake'; $env:UV_CACHE_DIR='.uv-cache'; uv run pytest backend/tests/integration/test_audit_jobs_api.py -q -p no:cacheprovider`，6 passed；`$env:UV_CACHE_DIR='.uv-cache'; uv run pytest backend/tests/unit/test_paddleocr_parser.py -q -p no:cacheprovider`，5 passed；`npm.cmd --prefix frontend run build` 成功。

## 批量筛选系统体系计划

- 本次范围：只做系统体系梳理、下一阶段模块边界设计和代码改造清单，不改后端/前端业务代码，不落数据库表。
- 新增计划文档：`docs/plans/batch_system_architecture_plan.md`，明确单份审查、简历库、候选人画像、证据索引、批量任务、排名筛选、前端工作台、Agent 插槽边界。
- 当前判断：AuditX 已完成单份 PDF/OCR/artifact/evidence/score/trace/PDF 高亮闭环，但仍不是大批量并行筛选系统。
- 下一阶段顺序：先领域契约和 repository seam，再简历库 service、候选人查询 service、批次 service、API 边界、前端信息架构，最后再进入 SQLite schema 和 Agent 插槽。
- 红线：不把批量逻辑塞进 `AuditJob.payload`，不把大对象塞进数据库主表，不在没有批次、队列、失败隔离、Top N、压测证据前宣称支持大批量并行。
- Mock/延后边界：LLM 真实接入、复杂 Agent、自主 tool runtime、并发 worker、压测报告均延后；后续代码阶段必须遵守 TDD。
- 验证：本轮为文档设计交付，未运行后端测试和前端构建；进入代码修改阶段后再运行 `uv run pytest backend/tests -q -p no:cacheprovider` 与 `npm.cmd --prefix frontend run build`。

## 批量筛选领域与存储边界切片

- 本次范围：按 TDD 先做批量系统最小领域契约、内存 repository seam 和 application service 边界，不接 Agent，不落 SQLite，不改前端。
- 新增领域对象：`CandidateProfile`、`CandidateScoreRecord`、`CandidateFindingRecord`、`EvidenceIndexRecord`、`BatchRecord`、`BatchCandidate`，明确候选人画像、分数、风险、证据索引、批次和批次候选人职责。
- 新增存储 seam：`InMemoryResumeRepository`、`InMemoryCandidateRepository`、`InMemoryEvidenceRepository`、`InMemoryBatchRepository`，当前只保存结构化摘要和 artifact uri，不保存 OCR raw、parsed document 或 PDF 内容。
- 新增服务边界：`ResumeLibraryService`、`CandidateQueryService`、`BatchReviewService`，分别负责简历入库元信息、候选人查询/Top N、批次创建/候选人状态隔离。
- 红线保持：批量状态不进入 `AuditJob.payload`；批次失败隔离先体现在 `BatchCandidate.status/error`，不影响 `BatchRecord` 主状态；大对象继续留在 artifact store。
- TDD 记录：先写 `test_batch_domain_contracts.py`、`test_batch_repository_contracts.py`、`test_batch_application_services.py`，均先因模块不存在失败，再实现最小代码通过。
- 当前仍未完成：SQLite 落表、API routes、前端简历库/候选人表格/批次 UI、并发 worker、真实批量运行、压测证据。

## 批量筛选 API 边界切片

- 本次范围：在已有领域/service/repository seam 上新增最小 API 边界，仍使用内存 repository，不落 SQLite，不接 Agent，不声明批量并行能力。
- 新增依赖注入：`get_resume_library_service()`、`get_candidate_query_service()`、`get_batch_review_service()`，为后续 SQLite repository 替换保留清晰 seam。
- 新增路由：`routes_resumes.py` 提供简历元信息入库和列表；`routes_candidates.py` 提供候选人列表和 Top N 查询；`routes_batches.py` 提供批次创建、添加候选人、候选人失败标记和批次详情。
- API 边界：返回结构化摘要和 artifact uri，不返回 PDF、OCR raw、parsed document 大对象；批次候选人失败只写 item 状态和 error。
- TDD 记录：先写 `test_batch_system_api.py`，先因依赖/路由不存在失败，再实现路由和依赖，定向 API 测试通过。
- 当前仍未完成：API 持久化、分页/筛选完整参数、候选人详情、evidence lookup、前端工作台、真实批量 worker 和失败重试。

## 批量筛选 SQLite 持久化切片

- 本次范围：把批量系统 repository seam 补上 SQLite 实现，并将简历/候选人/批次 API 依赖切到同一个 `auditx.sqlite3`，不接 Agent，不做 worker。
- 存储设计：按职责拆表为 `resumes`、`candidate_profiles`、`candidate_scores`、`candidate_findings`、`evidence_index`、`batches`、`batch_candidates`，不复用 `audit_jobs.payload` 承载批量状态。
- 表内容边界：SQLite 表保存结构化索引字段和 Pydantic payload；PDF、OCR raw、parsed document 等大对象仍只通过 artifact uri 引用。
- 新增测试：`test_batch_sqlite_repositories.py` 验证新 repository 实例可读取旧实例写入的简历、候选人分数、证据索引、批次和批次候选人状态。
- API 接入：`get_resume_library_service()`、`get_candidate_query_service()`、`get_batch_review_service()` 现在使用 `SQLiteResumeRepository`、`SQLiteCandidateRepository`、`SQLiteBatchRepository`。
- 当前仍未完成：把单份审查完成结果自动沉淀到 resume/candidate/evidence 表、候选人详情/evidence lookup API、前端批量工作台、并发队列和压测证据。

## 单份审查结果沉淀切片

- 本次范围：完成单份审查结果到简历库/候选人/证据索引表的最小自动沉淀，不改变单份审查主链路，不接 Agent，不做批量 worker。
- 新增 `ReviewResultIndexer`：只在 `AuditJobStatus.completed` 后把 `AuditJob` 投影为 `ResumeRecord`、`CandidateProfile`、`CandidateScoreRecord`、`CandidateFindingRecord`、`EvidenceIndexRecord`。
- 存储边界：indexer 只写结构化摘要和 artifact uri；source PDF、OCR raw、parsed document 仍在 artifact store，不复制到候选人或证据表。
- `AuditJobService` 增加可选 `result_indexer`，无 indexer 时保持旧行为；依赖层将单份审查服务注入同一个 `auditx.sqlite3` 的 resume/candidate/evidence repositories。
- TDD 记录：先写 `test_review_result_indexer.py` 和单份审查到候选人 API 可见的集成测试，先失败再实现 indexer 与依赖注入。
- 当前仍未完成：候选人详情 API、按 evidence id 查询、前端批量工作台、批次运行时从候选人库选取 Top N、并发和失败重试。

## 候选人详情与 Evidence Lookup API 切片

- 本次范围：补候选人详情和 evidence lookup API，服务前端后续复核；不新增 Agent、不做批次 worker、不改变 artifact 大对象边界。
- 新增查询能力：`CandidateQueryService.get_candidate()` 返回候选人画像、分数记录、finding 记录，保持候选人详情只来自结构化查询表。
- 新增 API：`GET /api/candidates/{candidate_id}` 返回候选人详情；`GET /api/candidates/{candidate_id}/evidence` 返回候选人 evidence index 列表；缺失候选人返回 404。
- 新增依赖：`get_batch_evidence_repository()` 暴露独立 evidence repository，避免把证据查询塞进 candidate repository。
- 存储边界：evidence API 返回 page/block/text excerpt/bbox/artifact uri，不返回 parsed document 或 OCR raw 内容。
- TDD 记录：先扩展 `test_batch_system_api.py`，因依赖缺失失败，再实现 service/route 后通过。
- 当前仍未完成：前端候选人详情页、PDF evidence 复核联动、批次 Top N 重算、并发 worker 和压测证据。

## 前端批量工作台骨架切片

- 本次范围：新增前端批量工作台信息架构骨架，读取真实 API / SQLite 数据；不伪装并发 worker、自动批量运行或压测能力。
- 新增类型：`frontend/src/types/resumeLibrary.ts` 定义简历、候选人、分数、finding、evidence index、批次和批次候选人类型。
- 新增 API client：`frontend/src/api/resumeLibrary.ts` 调用简历列表、候选人列表/详情/evidence、批次创建、添加候选人和批次详情接口。
- 新增 UI：`BatchScreeningWorkspace` 显示简历库、候选人表格、候选人详情/evidence index、草稿批次；主 `App` 增加 Single Review / Batch Workspace 切换。
- UI 边界：工作台文案明确当前只展示真实数据和草稿批次，尚未接并发 worker、自动批量运行、Top N 重算或压测证明。
- 验证：前端无测试框架配置，本切片用 TypeScript + Vite build 验证类型和构建；后续如增加前端测试框架再补组件测试。
- 当前仍未完成：PDF evidence 高亮与候选人详情联动、批次 Top N 重算、批量运行状态机前端、失败重试和压测报告展示。

## 批次 Top N 排名切片

- 本次范围：为已创建的批次增加基于候选人分数的 `rerank/top-n` 能力，不接 Agent，不做并发 worker，不处理大对象。
- 排名规则：批次候选人按最新 `CandidateScoreRecord.total_score` 降序、`risk_count` 升序、`candidate_id` 稳定排序；Top N 标记为 `shortlisted`，其余标记为 `eliminated`。
- 写回结果：`BatchCandidate` 写入 `rank`、`score_id`、`included_reason` 或 `eliminated_reason`；`BatchRecord.status` 更新为 `completed`。
- 新增 API：`POST /api/batches/{batch_id}/rerank` 和 `GET /api/batches/{batch_id}/top-n`；依赖层把 batch service 接入同库 candidate repository。
- 前端更新：批量工作台新增 `Rerank Top 10`，显示 rank、score_id、入围/淘汰原因和当前 Top N。
- TDD 记录：先写 service/API 排名测试，因构造参数/路由缺失失败，再实现服务、路由和前端 client。
- 当前仍未完成：真正批量运行审查、并发队列、失败 retry、候选人详情 PDF 高亮联动、压测报告。

## 批量工作台系统骨架补强

- 本次范围：按用户要求先跳过新增测试，继续补系统搭建骨架；保留现有回归和构建验证。
- 后端补强：`BatchReviewService.list_batches()` 与 `GET /api/batches`，让前端可以选择已有批次，而不是只操作当前新建批次。
- 候选人查询补强：`GET /api/candidates` 增加 `min_score`、`max_risk_count` 查询参数，继续保持查询只基于结构化 `candidate_scores`。
- 前端补强：批量工作台新增批次列表/选择、候选人 layer/min score/max risk 筛选、已有批次加载、rerank 后 Top N 展示。
- 边界：仍不接 Agent、不做并发 worker、不伪装批量自动运行；系统现在是“可查询、可建批次、可加候选人、可排名”的批量骨架。
- 当前仍未完成：文件级批量导入、批量审查 worker、失败 retry、候选人 PDF evidence 联动、压测报告。

## 批量系统剩余骨架补齐

- 本次范围：除压测报告外，补齐文件级批量导入、同步批量审查运行、失败 retry、候选人 evidence 与 PDF 高亮联动；继续跳过新增测试，只跑现有回归和前端构建。
- 批量导入：新增 `POST /api/batches/{batch_id}/import-files`，把多个本地文件路径登记为候选人画像并加入批次，保留 `source_file_path`，不复制文件内容到数据库。
- 批量运行：新增 `POST /api/batches/{batch_id}/run`，同步复用现有 `AuditJobService.create_and_run()` 逐个处理 pending/failed 候选人，单个失败写入 `BatchCandidate.error`。
- 失败 retry：新增 `POST /api/batches/{batch_id}/retry-failed`，把 failed 候选人重置为 pending，供再次运行。
- 结果合并：批量运行完成后把审查产生的 profile/score/finding/evidence 投影合并回导入候选人的 `candidate_id`，便于批次 rerank 和详情复核。
- PDF 联动：候选人 profile 新增 `review_session_id`、`source_file_path`；新增候选人 document/parsed-document API；前端候选人详情可点击 evidence 并复用 `PdfEvidenceViewer` 做高亮。
- 前端补强：批量工作台新增 Import Files、Run Pending、Retry Failed 按钮；候选人详情显示 PDF evidence 高亮入口。
- 边界：当前是同步本地批量运行，不是并发队列；仍未做压测报告，也未接 Agent 自主评估。

## 前端批量工作台验收文档

- 新增 `docs/acceptance/frontend-batch-workspace-acceptance.md`，说明如何启动后端/前端并验收 Single Review 与 Batch Workspace。
- 文档覆盖：单份审查、结果沉淀、候选人筛选、批次创建、Top N、批量文件导入、同步运行、失败 retry、候选人 PDF evidence 高亮。
- 文档明确当前边界：不验收压测报告、不验收并发 worker、不验收 Agent 自主规划、不验收真实 LLM 评估闭环。
