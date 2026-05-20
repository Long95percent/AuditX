# OCR、PDF 预览高亮与 Artifact 链路说明

## 本轮目标

补齐 Day1-Day6 后的关键遗留链路：artifact 大对象拆分、PaddleOCR 接入点、PDF 文件受控展示、evidence 定位闭环、风险显式复核。

## 已落地能力

- 新增 `ArtifactRef`，用于保存 artifact URI、类型、content type、hash、大小和创建时间。
- 新增 `FileSystemArtifactStore`，本地写入 `.data/artifacts/jobs/{job_id}/...`，返回轻量引用。
- `AuditJob`、`AuditResult`、API response 增加 `artifacts`，只保存引用，不保存 artifact 内容。
- 审查任务运行时保存源 PDF 为 `source_document` artifact。
- 新增 `GET /api/audit-jobs/{job_id}/document`，通过 artifact store 受控返回源 PDF。
- 新增 `GET /api/audit-jobs/{job_id}/parsed-document`，从 `parsed_document` artifact 读取 OCR layout，不把大对象塞进 job payload。
- 前端主工作台使用 `pdfjs-dist` canvas 渲染源 PDF，并按 parsed document page width/height 与 evidence bbox 计算精准 overlay 高亮。
- Finding evidence 可点击 `Highlight in PDF`，驱动 PDF 跳转到对应页并显示高亮框。
- 新增 `PaddleOCRDocumentParser`，懒加载 PaddleOCR，未安装时明确报错。
- `pyproject.toml` 增加 optional OCR 依赖组：`.[ocr]`。

## PaddleOCR 使用方式

当前不强制默认安装 PaddleOCR，避免所有开发/测试环境都下载大依赖。

需要启用真实 OCR 时运行：

```powershell
uv sync --extra ocr
```

然后在依赖层把 parser 从 `FakeDocumentParser()` 切换为 `PaddleOCRDocumentParser()`。

## Mock 边界

- LLM 仍先放着，不接真实 API。
- 当前 API key 配置继续由你填写。
- 默认 `AUDITX_OCR_PROVIDER` 已切换为 `paddleocr`，真实 OCR parser seam 已接入依赖层。测试/回归可显式设置 `AUDITX_OCR_PROVIDER=fake`。
- `LLMCandidateTool` / `LLMMockProvider` 仍是候选发现 mock。
- artifact store、source document artifact、受控 PDF endpoint、前端 PDF preview/evidence 定位展示是真实链路。

## 尚未完全闭环的点

- PaddleOCR 依赖已通过 `uv sync --extra ocr` 安装，并已验证 `PaddleOCRDocumentParser` 可实例化。
- PDF 精准 overlay 已使用 `pdfjs-dist` 渲染坐标层；如果 parsed artifact 缺失，前端会提示 precise viewer unavailable 并保留打开源 PDF 的降级入口。
- `PaddleOCRDocumentParser.parse_with_artifacts()` 已写入 `ocr_raw` 和 `parsed_document` artifacts；任务运行会把 job id 和 artifact store 传给 use case。
- PDF 页面尺寸已改为优先使用 PDF 渲染图片的真实尺寸，避免只用 bbox 最大值导致 overlay 比例漂移。
- SQLite 仍保存结构化 job 和 artifact refs；源 PDF、OCR raw、ParsedDocument 已具备 artifact 写入路径，LLM response 后续也应复用同一接口。

## 验证命令

```powershell
$env:UV_CACHE_DIR='.uv-cache'
uv run pytest backend/tests -q -p no:cacheprovider
npm.cmd --prefix frontend run build
```
