from collections.abc import Callable
import os
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from auditx.document_pipeline.base import DocumentParser
from auditx.domain.artifacts import ArtifactRef
from auditx.domain.documents import BBox, BlockType, DocumentPage, LayoutBlock, ParsedDocument
from auditx.infrastructure.storage.artifact_store import FileSystemArtifactStore

pdfium = None


class PaddleOCRDocumentParser(DocumentParser):
    def __init__(self, ocr_factory: Callable[[], object | None] | None = None) -> None:
        self.ocr_factory = ocr_factory or self._default_ocr_factory

    def parse(self, file_path: str) -> ParsedDocument:
        raw_result = self._run_ocr(file_path)
        path = Path(file_path)
        pages = self._raw_result_to_pages(raw_result)
        return ParsedDocument(
            document_id=f"ocr_{uuid5(NAMESPACE_URL, str(path.resolve()))}",
            filename=str(path),
            pages=pages,
        )

    def parse_with_artifacts(
        self,
        file_path: str,
        artifact_store: FileSystemArtifactStore,
        owner_id: str,
    ) -> tuple[ParsedDocument, list[ArtifactRef]]:
        raw_result = self._run_ocr(file_path)
        path = Path(file_path)
        document = ParsedDocument(
            document_id=f"ocr_{uuid5(NAMESPACE_URL, str(path.resolve()))}",
            filename=str(path),
            pages=self._raw_result_to_pages(raw_result),
        )
        raw_artifact = artifact_store.write_json(
            owner_type="job",
            owner_id=owner_id,
            artifact_type="ocr_raw",
            filename="ocr_raw.json",
            payload=raw_result,
        )
        parsed_artifact = artifact_store.write_bytes(
            owner_type="job",
            owner_id=owner_id,
            artifact_type="parsed_document",
            filename="parsed_document.json",
            content=document.model_dump_json().encode("utf-8"),
            content_type="application/json",
        )
        return document, [raw_artifact, parsed_artifact]

    def _run_ocr(self, file_path: str):
        ocr = self.ocr_factory()
        if ocr is None:
            raise RuntimeError(
                "PaddleOCR is not installed. Install paddlepaddle and paddleocr to enable OCR."
            )
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            return self._run_pdf_ocr(ocr, path)
        if hasattr(ocr, "predict"):
            return ocr.predict(str(path))  # type: ignore[attr-defined]
        return ocr.ocr(str(path), cls=True)  # type: ignore[attr-defined]

    def _run_pdf_ocr(self, ocr: object, path: Path):
        global pdfium
        if pdfium is None:
            try:
                import pypdfium2 as pdfium_module
            except ImportError as exc:
                raise RuntimeError("pypdfium2 is required to render PDF pages for OCR") from exc
            pdfium = pdfium_module
        temp_root = Path(".data/ocr_tmp").resolve()
        temp_root.mkdir(parents=True, exist_ok=True)
        pdf = pdfium.PdfDocument(str(path))
        results = []
        for page_index in range(len(pdf)):
            page = pdf[page_index]
            image_path = temp_root / f"{path.stem}_page_{page_index + 1}.png"
            image = page.render(scale=1.5).to_pil()
            image_width, image_height = image.size
            image.save(image_path)
            if hasattr(ocr, "predict"):
                page_result = ocr.predict(str(image_path))  # type: ignore[attr-defined]
            else:
                page_result = ocr.ocr(str(image_path), cls=True)  # type: ignore[attr-defined]
            results.extend(
                self._attach_page_dimensions(page_result or [], image_width, image_height)
            )
        return results

    def _default_ocr_factory(self) -> object | None:
        os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(Path(".data/paddlex_cache").resolve()))
        try:
            from paddleocr import PaddleOCR  # type: ignore[import-not-found]
        except ImportError:
            return None
        return PaddleOCR(
            lang="ch",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    def _raw_result_to_pages(self, raw_result) -> list[DocumentPage]:
        pages: list[DocumentPage] = []
        for page_index, page_result in enumerate(raw_result or [], start=1):
            blocks: list[LayoutBlock] = []
            max_x = 1.0
            max_y = 1.0
            page_items = self._page_items(page_result)
            for block_index, item in enumerate(page_items, start=1):
                points, text = self._extract_points_and_text(item)
                bbox = self._points_to_bbox(points)
                max_x = max(max_x, bbox.x1)
                max_y = max(max_y, bbox.y1)
                blocks.append(
                    LayoutBlock(
                        block_id=f"p{page_index}_ocr_{block_index}",
                        page_number=page_index,
                        block_type=BlockType.paragraph,
                        text=text,
                        bbox=bbox,
                    )
                )
            page_width, page_height = self._page_dimensions(page_result, max_x, max_y)
            pages.append(
                DocumentPage(
                    page_number=page_index,
                    width=page_width,
                    height=page_height,
                    blocks=blocks,
                )
            )
        return pages

    def _page_items(self, page_result) -> list:
        if isinstance(page_result, dict):
            texts = page_result.get("rec_texts") or []
            polygons = page_result.get("rec_polys") or page_result.get("dt_polys") or []
            return list(zip(polygons, texts))
        return page_result or []

    def _page_dimensions(self, page_result, max_x: float, max_y: float) -> tuple[float, float]:
        if isinstance(page_result, dict):
            page_width = page_result.get("page_width")
            page_height = page_result.get("page_height")
            if page_width and page_height:
                return float(page_width), float(page_height)
        return max_x, max_y

    def _attach_page_dimensions(self, page_result, page_width: int, page_height: int) -> list:
        results = list(page_result or [])
        for item in results:
            if isinstance(item, dict):
                item.setdefault("page_width", page_width)
                item.setdefault("page_height", page_height)
        return results

    def _extract_points_and_text(self, item) -> tuple[list[list[float]], str]:
        points = item[0]
        text_payload = item[1]
        text = text_payload[0] if isinstance(text_payload, tuple | list) else str(text_payload)
        return points, text

    def _points_to_bbox(self, points: list[list[float]]) -> BBox:
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        return BBox(x0=min(xs), y0=min(ys), x1=max(xs), y1=max(ys))
