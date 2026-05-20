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
