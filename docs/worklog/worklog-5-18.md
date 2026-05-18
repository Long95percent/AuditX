# Worklog - 2026-05-18

## 只读项目梳理
- 已确认根目录 `AGENTS.md` 约束：所有读写按 UTF-8，不转换编码，不必要时不整文件重写，保留现有换行；本次未改动业务代码。
- 当前项目定位：AuditX / VeriDoc 是 Tauri 桌面壳 + React/Vite UI + Python FastAPI 后端的桌面审计应用。
- 当前可用能力：后端已有 Phase 1A fake audit loop，包含 fake document parser、fake extractor、evidence validator、normalizer、job API 和 6 个已记录通过的测试。
- 当前前端状态：`frontend/src/app/App.tsx` 仍是玻璃拟态 UI 骨架，占位区包括 Document Viewer、Findings、Audit Timeline，尚未连接后端 API。
- 当前桌面状态：`src-tauri` 配置已转向项目本地 Tauri CLI，Rust 编译层此前已通过；但运行时仍阻塞在 `Failed to setup app: 拒绝访问。 (os error 5)`。

## 当前风险与阻塞
- 首要阻塞不是审计业务逻辑，而是 Windows/Tauri 运行时权限问题；日志位置：`tauri_runtime_error.log`。
- 仓库中存在多个 `pytest-cache-files-*` 目录读权限异常，`rg`/Git 会提示 Permission denied；这些目录也可能干扰后续遍历与状态检查。
- Git 状态显示根部旧 `WORKLOG.md` 被删除，新增 `docs/worklog/`，需要确认这是预期迁移还是误删后再整理提交。
- Python sidecar 尚未真正打包进 Tauri，README 也明确目前桌面只加载 React UI。

## 建议下一步优先级
1. 先定位并解决 Tauri runtime `os error 5`，确保验收入口能稳定打开桌面窗口。
2. 清理或排除无权限的 `pytest-cache-files-*` 临时目录，避免工具链扫描报错。
3. 确认 worklog 迁移策略：保留 `docs/worklog/WORKLOG.md` 为总日志，并使用每日文件如本文件记录当天决策。
4. 桌面壳稳定后，再把前端 UI 接到后端 fake audit API，形成桌面内可点击的最小审计闭环。
5. 最后再推进真实文件上传、PDF 渲染/OCR、规则引擎和 Python sidecar 打包，避免在桌面入口未稳定前扩大复杂度。

## 推荐立即执行的排查动作
- 用普通 PowerShell 和“以管理员身份运行”各启动一次 `启动AuditX桌面应用.bat`，对比是否都是 `os error 5`。
- 检查 Windows 安全软件/受控文件夹访问是否拦截 `src-tauri/target/debug/auditx-veridoc-desktop.exe` 或 WebView2/Tauri 写入用户数据目录。
- 尝试临时修改 Tauri app identifier 或清理对应 AppData 用户数据目录，验证是否是旧应用数据目录权限损坏。
- 在桌面运行时问题解决前，不建议先接入 sidecar 或真实 OCR/LLM。

## 2026-05-18 启动权限修复
- 现象：普通权限启动 Tauri 会在窗口 setup 阶段报 `Failed to setup app: 拒绝访问。 (os error 5)`，管理员权限可运行。
- 根因判断：Tauri/Wry 在 Windows 会为 WebView2 创建/使用本地数据目录；默认目录可能已被管理员运行创建或 ACL 异常污染，导致普通用户无法访问。
- 修复：在 `src-tauri/tauri.conf.json` 为主窗口显式设置 `label: main` 与 `dataDirectory: auditx-dev-webview-data`，让 WebView2 使用新的用户态隔离数据目录。
- 追加修复：普通权限探测时发现 `127.0.0.1:5173` 已被其他 Node 进程占用，导致 Vite `EACCES`；已统一开发端口为 `127.0.0.1:1420`，并同步 README。
- 追加修复：根目录 `启动AuditX桌面应用.bat` 原先仍调用 `npx tauri dev`，已改为调用 `scripts/start_desktop.ps1`，确保使用项目本地 Tauri CLI。
- 验证：`python -m pytest scripts\checks\test_tauri_config.py -q -p no:cacheprovider` 通过；`cargo check` 通过；普通权限短时运行 `.\frontend\node_modules\.bin\tauri.cmd dev --no-watch` 45 秒未再报 `os error 5` 或端口权限错误。
- 补充验证中发现 Vite/PostCSS 会误读带 BOM 的 `frontend/package.json` 并导致生产构建失败；未转换现有文件编码。
- 已新增 `frontend/vite.config.mjs`，用无外部依赖导入的 Vite 配置固定 dev server 端口并内联空 PostCSS 配置，避免 PostCSS 搜索读取 `package.json`。
- 已新增 `frontend/postcss.config.cjs` 作为显式空 PostCSS 配置占位。
- 最终验证：配置检查通过、前端生产构建通过、Tauri `cargo check` 通过、普通权限 Tauri dev 探测 45 秒稳定运行。

## 2026-05-18 Plan execution start
- Started executing `docs/plans/plan-2026-05-18.md`.
- First task: clean workspace signals and prepare the desktop fake audit loop implementation.
- Added typed frontend audit job API client at `frontend/src/api/auditJobs.ts`.
- Updated frontend audit types to match backend JSON field names.
- Connected `frontend/src/app/App.tsx` to the fake audit API with loading, status, findings, evidence bbox, and error states.
- Frontend production build passed after UI wiring.

## 2026-05-18 Desktop fake audit loop
- Executed `docs/plans/plan-2026-05-18.md` through the desktop fake audit loop milestone.
- Added `.gitignore` pattern for `pytest-cache-files-*/` to keep local pytest temp directories out of commits.
- Added `frontend/src/api/auditJobs.ts` as the typed client for `POST /api/audit-jobs`.
- Updated `frontend/src/types/audit.ts` to match backend response field names exactly.
- Replaced the static React placeholder with a clickable fake audit UI: run button, job status, document metadata, rejected count, finding cards, evidence quote/bbox, and backend error state.
- Added supporting CSS for action rows, status pills, finding cards, risk badges, evidence boxes, and responsive layout.
- Verified backend unit/integration tests: `python -m pytest backend/tests/unit backend/tests/integration -q -p no:cacheprovider` passed with 6 tests.
- Verified temporary FastAPI health and fake audit API calls returned `health=ok`, `document_id=fake_doc_001`, and one finding.
- Verified frontend production build: `npm.cmd --prefix frontend run build` completed successfully.
- Verified Tauri build layer: `cargo check` in `src-tauri` completed successfully.
- Verified normal-permission desktop startup probe with temporary backend: Tauri dev stayed running for 45 seconds and was stopped by the probe.
- Manual click-through in the native window still needs a human visual check because the automated probe cannot click the UI.

## 2026-05-18 Failed to fetch debugging
- User reported the frontend shows `Failed to fetch` after clicking the fake audit action.
- Starting systematic debugging: check whether the backend is running, whether the browser/Tauri origin is blocked by CORS, and whether the frontend API base URL is correct.
- Reproduced the browser/Tauri `Failed to fetch` root cause with a failing CORS preflight regression test: `OPTIONS /api/audit-jobs` returned 405 without CORS middleware.
- Added FastAPI `CORSMiddleware` for the Vite/Tauri dev origins `http://127.0.0.1:1420` and `http://localhost:1420`.
- Added `backend/tests/integration/test_cors.py` to verify preflight behavior for `POST /api/audit-jobs`.
- Verified backend tests now pass with 7 tests.
- Verified frontend build still passes.
- Verified real preflight against temporary uvicorn returns `preflight_status=200` and `Access-Control-Allow-Origin=http://127.0.0.1:1420`.

## 2026-05-18 Desktop Failed to fetch follow-up
- User reported the native desktop app still shows `Failed to fetch` after the CORS fix.
- New hypothesis: the desktop startup script launches only Vite/Tauri and does not start the FastAPI backend, so the browser fetch has no server at `127.0.0.1:8765`.
- Checking startup scripts and planning to make the desktop launcher start a development backend process before Tauri.
- Follow-up root cause confirmed: the desktop launcher started Vite/Tauri but did not start the FastAPI backend, so the desktop UI had no server at `127.0.0.1:8765` and still showed `Failed to fetch` even after CORS was fixed.
- Updated `scripts/start_desktop.ps1` to start the backend API on `127.0.0.1:8765` when `/health` is not already available, wait until it is ready, then start Tauri.
- Added cleanup logic so the script stops the backend it started when the desktop process exits normally.
- Added a startup guard for frontend port `127.0.0.1:1420`; if an old AuditX/Vite window is still running, the script now fails with a clear message instead of a confusing Vite port error.
- Added `scripts/checks/test_desktop_start_script.py` to prevent regressing the backend startup integration.
- Verification: startup script check passed; normal-permission `scripts/start_desktop.ps1 -SkipInstall` probe started backend, reported `backend_health=ok`, started Vite on `127.0.0.1:1420`, compiled Tauri, and stayed running for 55 seconds.
- Final verification after desktop launcher backend integration: backend tests passed with 7 tests, script checks passed with 3 tests, frontend build passed, and Tauri `cargo check` passed.
- User action required: close any already-open AuditX desktop/Vite windows, then relaunch with `启动AuditX桌面应用.bat` so the updated startup script can start the backend before the desktop UI.

## 2026-05-18 Next step after desktop loop success
- User confirmed the desktop fake audit loop is now running successfully.
- Next step chosen: improve demo robustness by exposing backend health in the desktop UI before running an audit, so connection/backend issues are visible instead of surfacing only as `Failed to fetch`.
- Added desktop UI backend health visibility after the fake audit loop was confirmed working.
- Added `getHealthStatus()` in `frontend/src/api/auditJobs.ts` for `GET /health`.
- Updated `frontend/src/app/App.tsx` to auto-check backend health on load, expose a `Check Backend` action, and check health before running fake audit.
- Added online/offline status styling and updated README desktop acceptance notes.
- Verification after backend health UI: backend tests passed, script checks passed, frontend build passed, Tauri `cargo check` passed, and `start_desktop.ps1 -SkipInstall` probe reported `backend_health=ok` while Tauri stayed running for 45 seconds.

## 2026-05-18 MVP Step 1: desktop file picker
- User approved technical choice B: use the Tauri Dialog plugin for real desktop file selection.
- Goal for this step: let the desktop UI choose a local document path and pass that selected path into the existing fake audit job creation flow.
- This intentionally does not implement real PDF parsing/OCR yet; it upgrades the MVP input from hardcoded `demo_resume.pdf` to a user-selected desktop file path.
- Implementing MVP Step 1 after user approval of Tauri Dialog plugin technical choice.
- Added Tauri dialog integration points: Rust dependency, plugin registration, default capability permission, and frontend package dependency declaration.
- Updated desktop UI to choose a local document with the native Tauri file dialog and pass that selected path to the existing fake audit API.
- The audit remains fake/parser-free for this step; this upgrades the MVP input from hardcoded demo path to user-selected local path.
- Tauri capability parser rejected the newly-created `src-tauri/capabilities/default.json` when it was written with PowerShell's default UTF-8 BOM.
- User approved rewriting only this newly-created capability file as UTF-8 without BOM; no existing project file encoding was converted for this step.
- Installed/synced frontend npm dependency `@tauri-apps/plugin-dialog` after user-approved technical choice.
- Synced Rust dependency `tauri-plugin-dialog` and updated `src-tauri/Cargo.lock` through `cargo check`.
- Verification for MVP Step 1: backend tests passed, script checks passed, frontend build passed, Tauri `cargo check` passed, and `start_desktop.ps1 -SkipInstall` probe reported `backend_health=ok` while the desktop stayed running for 45 seconds.
- Manual user check still needed: click `Choose Document` in the desktop app, select a local PDF/DOC/TXT, then click `Run Fake Audit` and confirm the selected path is shown in the UI.

## 2026-05-18 MVP Step 2: backend file path validation
- User confirmed MVP Step 1 desktop native file picker works.
- Next step chosen without new technical dependencies: validate selected local file paths on the backend before creating fake audit jobs.
- Goal: if the selected path does not exist or is not a file, API returns a clear client error instead of silently auditing a bad path.
- Implemented MVP Step 2: backend file path validation before fake audit job creation.
- Updated API tests to use a real fixture file and added missing-file plus directory rejection coverage.
- `POST /api/audit-jobs` now returns `400 Selected document does not exist` for missing files and `400 Selected document is not a file` for directories.
- Improved frontend API error parsing so FastAPI JSON `detail` messages are displayed clearly in the desktop UI.
- Verification after MVP Step 2: backend tests passed with 9 tests, script checks passed with 4 tests, frontend build passed, and Tauri `cargo check` passed.

## 2026-05-18 File parsing plan
- User requested scheme C-level file parsing/rendering/OCR planning and explicitly asked to write a plan document before implementation.
- Created `docs/文件解析plan.md` with a full implementation plan, technical decision gates, task breakdown, tests, and verification steps.
- No production code was changed for this planning step.
