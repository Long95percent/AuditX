# WORKLOG

## 2026-05-17 14:21:53 +08:00
- 收到架构决策：AuditX / VeriDoc 定位为高确定性、工业级桌面审计应用。
- 后端采用 Python + FastAPI + Pydantic + pytest。
- 前端采用 React + Vite + TypeScript。
- 包管理统一采用 uv，禁止 Conda。
- 桌面架构采用 Tauri + Python Sidecar。
- 本阶段只初始化基础设施与项目框架，不实现 OCR、LLM、审计业务逻辑。

## 2026-05-17 14:22:17 +08:00
- 工具链检查完成：node/npm 可用，uv、rustc、cargo 未检测到。
- 因 uv 缺失，暂不执行 uv venv，避免用其它包管理器替代你的架构决策。
- 因 Rust/Cargo 缺失，暂不执行 Tauri 初始化，先创建 Tauri 目录骨架与配置占位。

## 2026-05-17 14:22:53 +08:00
- 已创建根目录规范文件：README.md、.gitignore、.env.example、pyproject.toml。
- 已创建后端、前端、Tauri sidecar 的基础目录结构。

## 2026-05-17 14:24:00 +08:00
- 已创建后端 Python 包骨架与分层目录。
- 已添加 Pydantic 强类型领域模型：BBox、ParsedDocument、Evidence、AuditFinding。
- 已添加 Tool/ToolRegistry、DocumentParser、EvidenceValidator 基础抽象。
- 已添加 FastAPI app 工厂与 /health 健康检查。
- 已添加 HR 领域包占位规则与 Prompt。
- 已添加 pytest 单元测试骨架，覆盖 bbox 与 evidence 强约束。

## 2026-05-17 14:25:26 +08:00
- 已创建 React + Vite + TypeScript 前端骨架。
- 已添加玻璃拟态基础样式与审计工作台占位组件。
- 已创建 Tauri v2 配置、Rust 入口与 Python sidecar 外部二进制占位配置。
- 未运行 npm install 或 tauri 构建，因为本阶段不强行下载依赖且本机缺少 Rust/Cargo。

## 2026-05-17 14:25:59 +08:00
- 已运行 Python 语法检查：python -m py_compile ...，退出码 0。
- 依赖可用性检查退出码：0。

## 2026-05-17 14:26:36 +08:00
- 已清理 Python 语法检查产生的 __pycache__ 缓存目录。
- 已运行最小单元测试：python -m pytest backend/tests/unit -q，退出码 4。

## 2026-05-17 14:27:16 +08:00
- 定位 pytest 失败根因：pyproject.toml 使用 UTF-8 BOM，TOML 解析器在 line 1 column 1 报错。
- 已将 pyproject.toml 以 UTF-8 无 BOM 重写，未改变配置语义。

## 2026-05-17 14:27:20 +08:00
- 重跑最小单元测试：python -m pytest backend/tests/unit -q，退出码 0。

## 2026-05-17 14:49:47 +08:00
- 已清理测试/语法检查产生的 __pycache__ 与 .pytest_cache 临时目录。
- 当前初始化阶段结束：保留基础框架、配置、类型模型、测试与桌面端占位结构。

## 2026-05-17 14:50:35 +08:00
- 尝试清理 pytest-cache-files-jr_j_hvf 时 Windows 返回访问拒绝；目录为空但当前进程无权删除。
- 按你的要求，遇到无法快速解决的环境/权限问题不死磕，保留该阻塞记录，后续可由你手动删除或调整目录权限。

## 2026-05-17 15:02:43 +08:00
- 用户请求：如果不复杂，协助安装 uv 与 Rust/Cargo，并写入 worklog。
- 开始检查本机可用安装器与当前工具链状态。

## 2026-05-17 15:37:19 +08:00
- 本机未检测到 winget/scoop/choco，已改用官方在线安装脚本。
- uv 官方安装脚本执行成功，安装位置：C:\Users\22641\.local\bin。
- 当前会话将临时追加该路径用于后续验证。

## 2026-05-17 15:40:19 +08:00
- Rust 官方 rustup-init 执行成功，安装 stable minimal 工具链。
- 当前会话临时追加 PATH：C:\Users\22641\.local\bin 与 C:\Users\22641\.cargo\bin。
- 已验证 uv/rustc/cargo 版本，并执行 uv venv，退出码 2。

## 2026-05-17 15:40:32 +08:00
- uv venv 首次失败：默认缓存目录 C:\Users\22641\AppData\Local\uv\cache 访问被拒绝。
- 不修改系统权限，改用项目内 UV_CACHE_DIR=.uv-cache 进行最小复测。

## 2026-05-17 15:40:33 +08:00
- 使用项目内 UV_CACHE_DIR=.uv-cache 重跑 uv venv，退出码 0。

## 2026-05-17 15:40:48 +08:00
- 已将 UV_CACHE_DIR=.uv-cache 写入 .env.example，并将 .uv-cache/ 加入 .gitignore。
- 最终验证：
  - uv 0.11.14 (3fdfdc7d4 2026-05-12 x86_64-pc-windows-msvc)
  - rustc 1.95.0 (59807616e 2026-04-14)
  - cargo 1.95.0 (f2d3ce0bd 2026-03-21)
  - Python 3.12.10

## 2026-05-17 16:54:12 +08:00
- 新增代码审查导览文档：docs/code_review_guide.md。
- 文档说明了后端、前端、Tauri 入口，各目录职责，核心模型/函数，以及后续人工审查红线。

## 2026-05-17 17:04:46 +08:00
- 用户确认开工 Phase 1A：后端审计任务最小闭环。
- 范围：fake parser、fake extractor、AuditUseCase、AuditJobService、audit jobs API、pytest、审计文档。
- 约束：继续记录 WORKLOG，不接真实 OCR/LLM/第三方 API，不扩展复杂前端。

## 2026-05-17 17:05:17 +08:00
- 已先写 Phase 1A 集成测试：AuditUseCase 最小闭环与 audit jobs API。
- 测试期望：fake parser -> fake extractor -> evidence validator -> normalized findings -> API 返回结果。

## 2026-05-17 17:05:34 +08:00
- 使用 uv run pytest backend/tests/integration/test_audit_use_case.py -q 验证 RED 阶段时失败。
- 失败原因不是业务测试断言，而是 uv 需要访问 PyPI 拉取依赖，当前网络/权限阻止访问 pypi.org。
- 为继续 TDD 红灯验证，改用系统已安装 pytest 执行同一测试。

## 2026-05-17 17:06:19 +08:00
- 已实现 Phase 1A 最小审计用例核心：AuditResult、FakeDocumentParser、FindingExtractor、FakeExtractor、FindingNormalizer、AuditUseCase。
- 当前仍是 fake 闭环，不接真实 OCR/LLM/外部 API。

## 2026-05-17 17:07:07 +08:00
- 已实现 audit jobs API 最小闭环：POST /api/audit-jobs、GET /api/audit-jobs/{job_id}、GET /api/audit-jobs/{job_id}/findings。
- 已添加 AuditJobService 内存任务存储，当前仅用于 MVP 骨架验证。

## 2026-05-17 17:07:53 +08:00
- 修复 audit jobs API 响应 schema：为 Pydantic 响应模型启用 from_attributes，允许从 AuditJob 对象转换。

## 2026-05-17 17:09:01 +08:00
- 新增审计文档：docs/audit_flow_phase_1a.md。
- 文档记录 Phase 1A 最小闭环 API、应用层、fake parser、fake extractor、证据校验和测试覆盖。

## 2026-05-17 17:09:29 +08:00
- 运行完整后端测试：python -m pytest backend/tests/unit backend/tests/integration -q -p no:cacheprovider，退出码 0。
- 使用 -p no:cacheprovider 避免 pytest 在当前 Windows 环境写缓存目录触发权限警告。

## 2026-05-17 17:09:50 +08:00
- 收尾检查发现当前目录不是 git repository，因此无法输出 git status 变更清单。
- 该情况不影响 Phase 1A 文件落地与测试验证。

## 2026-05-17 17:11:38 +08:00
- 用户要求：验证结果也必须写入 worklog，并说明如何启动应用查看效果。
- Phase 1A 最新验证结果：python -m pytest backend/tests/unit backend/tests/integration -q -p no:cacheprovider 输出 ...... [100%]，共 6 个测试通过，退出码 0。
- 当前可查看效果：后端 FastAPI health 与 audit jobs API；前端/Tauri 仅为骨架，需先安装前端依赖后运行 Vite。

## 2026-05-17 17:14:13 +08:00
- 根据用户要求更新 README：明确最终只验收 Tauri 桌面应用。
- README 已补充桌面启动方式 cargo tauri dev、前端仅作为 UI 源码、后端 API 仅作为开发调试入口。
- README 已记录当前测试命令与最新验证结果：6 passed。

## 2026-05-17 17:15:50 +08:00
- 新增桌面启动脚本：scripts/start_desktop.ps1。
- 脚本职责：进入项目根目录、设置 PATH、设置 UV_CACHE_DIR、检查 uv/npm/cargo、必要时创建 .venv、安装前端依赖、安装 Tauri CLI、启动 cargo tauri dev。

## 2026-05-17 17:16:31 +08:00
- 更新 README：不再只列命令，明确说明使用 Windows PowerShell/PowerShell 7、先 cd 到 D:\github_desktop\AuditX，再运行脚本或命令。
- README 已强调验收入口是 Tauri 桌面应用，浏览器前端和后端 Swagger 仅用于开发调试。

## 2026-05-17 17:16:49 +08:00
- 已验证 scripts/start_desktop.ps1 PowerShell 语法，未发现解析错误。
- 未实际运行桌面启动脚本，避免自动安装依赖或打开桌面窗口。

## 2026-05-17 17:20:13 +08:00
- 新增双击启动脚本：启动AuditX桌面应用.bat。
- 新增快速双击启动脚本：快速启动AuditX桌面应用.bat，内部调用 start_desktop.ps1 -SkipInstall。
- bat 文件使用 ASCII 编码，降低 Windows 双击执行时的兼容风险。

## 2026-05-17 17:20:43 +08:00
- 更新 README：验收启动方式改为优先双击 启动AuditX桌面应用.bat。
- README 同时保留 PowerShell 手动启动方式作为 fallback。

## 2026-05-17 17:21:04 +08:00
- 已确认双击启动 bat 文件存在。
- 已复验 scripts/start_desktop.ps1 PowerShell 语法，无解析错误。
- 未实际双击运行，避免自动安装依赖或打开桌面窗口。

## 2026-05-17 17:44:24 +08:00
- 定位 Tauri 启动失败根因：启动脚本从项目根目录 D:\github_desktop\AuditX 执行 cargo tauri dev，Tauri 的 beforeDevCommand 
pm --prefix ../frontend run dev 被解析为 D:\github_desktop\frontend，导致找不到 package.json。
- 已修正 src-tauri/tauri.conf.json：beforeDevCommand 改为 
pm --prefix frontend run dev，beforeBuildCommand 改为 
pm --prefix frontend run build，frontendDist 改为 rontend/dist。

## 2026-05-17 17:44:47 +08:00
- 更新 scripts/start_desktop.ps1：启动前检查 frontend/package.json 与 src-tauri/tauri.conf.json 是否存在，提前暴露目录结构问题。

## 2026-05-17 17:45:08 +08:00
- 已验证 src-tauri/tauri.conf.json JSON 可解析，且 build 路径为项目根相对路径：frontend。
- 已验证 frontend/package.json 存在。
- 已验证 scripts/start_desktop.ps1 PowerShell 语法无解析错误。
- 未实际运行 cargo tauri dev，避免打开桌面窗口；建议用户重新双击启动脚本验证。

## 2026-05-17 17:51:20 +08:00
- 用户反馈 Tauri 构建失败：unable to parse JSON Tauri config file ... expected value at line 1 column 1。
- 定位根因：src-tauri/tauri.conf.json 文件开头包含 UTF-8 BOM 字节 EF BB BF，Rust/Tauri JSON 解析器不接受 BOM。
- 已将 src-tauri/tauri.conf.json 以 UTF-8 无 BOM 重写，配置语义不变。

## 2026-05-17 17:51:50 +08:00
- 验证 src-tauri/tauri.conf.json：首字节为 7B 0A 20，不再是 UTF-8 BOM。
- 验证 Tauri 配置 JSON 可被 PowerShell 解析，beforeDevCommand 为 
pm --prefix frontend run dev。
- 验证 scripts/start_desktop.ps1 语法无解析错误。

## 2026-05-17 17:58:10 +08:00
- 用户反馈 Tauri 新错误：resource path inaries\auditx-sidecar-x86_64-pc-windows-msvc.exe doesn't exist。
- 定位根因：src-tauri/tauri.conf.json 中提前声明了 bundle.externalBin=["binaries/auditx-sidecar"]，Tauri 会在构建时强制查找平台后缀 sidecar 二进制，但当前 Phase 1A 尚未生成 Python sidecar exe。
- 已移除 bundle.externalBin 占位配置，保留 Tauri 桌面壳优先启动；真实 Python sidecar 打包将在后续阶段实现。

## 2026-05-17 17:58:30 +08:00
- 更新 README：说明当前 Tauri 配置暂未启用 Python sidecar 打包，桌面验收先启动 Tauri shell + React UI。

## 2026-05-17 17:58:56 +08:00
- 验证 src-tauri/tauri.conf.json：无 BOM、JSON 可解析、externalBin 已移除、beforeDevCommand 路径正确。
- 验证 scripts/start_desktop.ps1 语法无解析错误。
- 未实际启动 Tauri 窗口；请用户重新双击启动脚本验证。

## 2026-05-17 18:04:01 +08:00
- 用户反馈 Tauri 构建错误：package.metadata does not exist。
- 定位根因：Windows 资源生成依赖 tauri-winres 会读取 Cargo.toml 的 [package.metadata.tauri-winres]；当前 Cargo.toml 过于精简，缺少 [package.metadata]。
- 已补充 src-tauri/Cargo.toml 的 description 与 [package.metadata.tauri-winres]，用于 Windows 资源元数据。

## 2026-05-17 18:05:20 +08:00
- 执行 Tauri Rust 验证：在 src-tauri 下运行 cargo check，退出码 101。

## 2026-05-17 18:05:55 +08:00
- cargo check 继续验证时发现新错误：icons/icon.ico not found; required for generating a Windows Resource file during tauri-build。
- 已创建最小 Tauri Windows 图标：src-tauri/icons/icon.ico，用于满足 Windows resource 构建要求。

## 2026-05-17 18:06:36 +08:00
- 补充 icon.ico 后重新执行 cargo check，退出码 0。

## 2026-05-17 18:06:59 +08:00
- Tauri 配置链路验证通过：cargo check 在 src-tauri 目录执行成功，输出 Finished dev profile，退出码 0。
- 当前已连续修复 Tauri 启动链路问题：frontend 相对路径、tauri.conf.json BOM、未生成 sidecar externalBin、Cargo package metadata、缺失 icons/icon.ico。
- 下一步请重新双击 启动AuditX桌面应用.bat 验证真实桌面窗口启动。

## 2026-05-17 18:08:24 +08:00
- 启动链路预检：按 start_desktop.ps1 同样方式临时追加 PATH 后，验证 uv/cargo/rustc/npm 可用。
- 执行前端生产构建：
pm --prefix frontend run build，退出码 0。

## 2026-05-17 18:08:58 +08:00
- 启动链路预检发现 PowerShell 直接执行 npm 会命中 C:\Program Files\nodejs\npm.ps1，受 ExecutionPolicy 限制。
- 已将 Tauri beforeDevCommand/beforeBuildCommand 改为 npm.cmd，启动脚本中的依赖安装和命令检查也改为 npm.cmd，避免 PowerShell 脚本策略问题。

## 2026-05-17 18:09:14 +08:00
- 重跑前端生产构建：
pm.cmd --prefix frontend run build，退出码 1。

## 2026-05-17 18:09:31 +08:00
- 前端生产构建失败根因：TypeScript 版本较新，tsconfig 的 moduleResolution=Node 被解释为已废弃 node10。
- 已将 frontend/tsconfig.json 的 moduleResolution 调整为 Vite/现代 bundler 场景推荐的 Bundler。

## 2026-05-17 18:09:46 +08:00
- 修复 tsconfig 后重跑前端生产构建：
pm.cmd --prefix frontend run build，退出码 1。

## 2026-05-17 18:09:56 +08:00
- 前端构建继续失败：TypeScript 找不到 CSS side-effect import 的类型声明。
- 已新增 frontend/src/vite-env.d.ts，引用 vite/client 类型以支持 CSS 模块/资源导入声明。

## 2026-05-17 18:10:11 +08:00
- 补充 vite-env.d.ts 后重跑前端生产构建：
pm.cmd --prefix frontend run build，退出码 1。

## 2026-05-17 18:10:55 +08:00
- 前端构建失败根因转移到 Vite 加载 vite.config.ts 时 externalize-deps spawn EPERM。
- 已将 Vite 配置从 TypeScript 改为 JavaScript：frontend/vite.config.js，并删除 frontend/vite.config.ts，减少配置加载阶段转译/子进程路径问题。

## 2026-05-17 18:11:10 +08:00
- 改用 vite.config.js 后重跑前端生产构建：
pm.cmd --prefix frontend run build，退出码 1。

## 2026-05-17 18:11:56 +08:00
- 重新验证 Tauri Rust 构建层：cargo check，退出码 0。

## 2026-05-17 18:12:30 +08:00
- 短时探测 cargo tauri dev --no-watch：运行 18 秒后仍在运行则视为启动链路已越过配置/构建阶段并主动停止；探测退出码 。

## 2026-05-17 18:13:49 +08:00
- 预检发现 cargo tauri 不可用，且 cargo install --list 访问 C:\Users\22641\.cargo\.crates.toml 被拒绝，不适合依赖全局 Tauri CLI。
- 已改为项目本地 Tauri CLI：在 frontend/package.json devDependencies 添加 @tauri-apps/cli，并将启动脚本改为 
pm.cmd --prefix frontend run tauri -- dev。

## 2026-05-17 18:15:21 +08:00
- 安装/同步前端依赖以包含项目本地 Tauri CLI：
pm.cmd --prefix frontend install，退出码 1。

## 2026-05-17 18:17:56 +08:00
- 使用提升权限/联网许可重试前端依赖同步：
pm.cmd --prefix frontend install，退出码 0。

## 2026-05-17 18:18:16 +08:00
- 验证项目本地 Tauri CLI：
pm.cmd --prefix frontend run tauri -- --version，退出码 0。
- 验证 Tauri Rust 构建层：cargo check，退出码 0。

## 2026-05-17 18:18:58 +08:00
- 短时探测项目本地 Tauri 启动：
pm.cmd --prefix frontend run tauri -- dev --no-watch。
- 25 秒后进程仍在运行则说明已越过前端命令/Tauri 配置/Rust 编译的即时失败阶段，本次主动停止；探测退出码 。

## 2026-05-17 18:19:28 +08:00
- 启动探测发现 
pm.cmd --prefix frontend run tauri -- dev 会让 Tauri CLI 从 frontend 目录运行，无法识别项目根下的 src-tauri。
- 已改为从项目根直接调用本地 CLI：.rontend
ode_modules\.bin\tauri.cmd dev，保持 Tauri 能发现 src-tauri/tauri.conf.json。

## 2026-05-17 18:20:20 +08:00
- 验证根目录本地 Tauri CLI：.rontend
ode_modules\.bin\tauri.cmd --version，退出码 0。
- 短时探测 .rontend
ode_modules\.bin\tauri.cmd dev --no-watch：35 秒后仍运行则主动停止，探测退出码 。

## 2026-05-17 19:07:17 +08:00
- Tauri 启动探测发现 Vite 加载 frontend/vite.config.js 时仍触发 externalize-deps spawn EPERM。
- 已移除 frontend/vite.config.js，将 dev server 配置改为 package.json 脚本参数：ite --host 127.0.0.1 --port 5173 --strictPort，避免 Vite 配置文件打包加载路径。

## 2026-05-17 19:07:38 +08:00
- 短时探测前端 dev：
pm.cmd --prefix frontend run dev，8 秒后仍运行则主动停止，探测退出码 0。

## 2026-05-17 19:08:34 +08:00
- 短时探测 Tauri 桌面启动：.rontend\node_modules\.bin\tauri.cmd dev --no-watch，45 秒后仍运行则主动停止，探测退出码 。

## 2026-05-17 19:09:05 +08:00
- 为定位 Tauri runtime Failed to setup app: 拒绝访问，在 src-tauri 下执行 RUST_BACKTRACE=1 cargo run --no-default-features --color never --，退出码 101，日志写入 tauri_runtime_error.log。

## 2026-05-17 19:09:36 +08:00
- 启动链路深度预检结论：npm/cargo 职责没有冲突。npm 负责启动 Vite 前端；Tauri CLI 负责调用 cargo 编译/运行 Rust 桌面壳。
- 已改为项目本地 Tauri CLI：.\frontend\node_modules\.bin\tauri.cmd dev，避免依赖全局 cargo tauri。
- 前端 dev 预检通过：
pm.cmd --prefix frontend run dev 能启动 Vite。
- Tauri Rust 编译层通过：cargo check 成功。
- Tauri 运行时仍失败：Failed to setup app: 拒绝访问 (os error 5)，当前判断是运行时访问 Windows 本地应用目录/系统资源的权限问题，不是 npm 与 cargo 命令混用问题。
