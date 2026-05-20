import pytest

from auditx.document_pipeline.paddleocr_parser import PaddleOCRDocumentParser
from auditx.infrastructure.storage.artifact_store import FileSystemArtifactStore


def test_paddleocr_parser_reports_missing_dependency_clearly() -> None:
    parser = PaddleOCRDocumentParser(ocr_factory=lambda: None)

    with pytest.raises(RuntimeError, match="PaddleOCR is not installed"):
        parser.parse("resume.pdf")


class FakeOCR:
    def ocr(self, file_path: str, cls: bool = True):
        return [
            [
                (
                    [[10, 20], [110, 20], [110, 50], [10, 50]],
                    ("候选人负责合规审计项目", 0.98),
                )
            ]
        ]


class FakePaddleOCR3:
    def predict(self, input, **kwargs):
        return [
            {
                "rec_texts": ["真实OCR文本"],
                "rec_polys": [
                    [[10, 20], [110, 20], [110, 50], [10, 50]],
                ],
            }
        ]


def test_paddleocr_parser_writes_raw_and_parsed_artifacts() -> None:
    store = FileSystemArtifactStore("backend/tests/.artifact_tmp")
    parser = PaddleOCRDocumentParser(ocr_factory=lambda: FakeOCR())

    document, artifacts = parser.parse_with_artifacts(
        file_path="backend/tests/fixtures/demo_resume.png",
        artifact_store=store,
        owner_id="job_ocr",
    )

    assert document.pages[0].blocks[0].text == "候选人负责合规审计项目"
    artifact_types = {artifact.artifact_type for artifact in artifacts}
    assert artifact_types == {"ocr_raw", "parsed_document"}
    assert all(artifact.size_bytes > 0 for artifact in artifacts)


def test_paddleocr_parser_supports_paddleocr_3_predict_result() -> None:
    parser = PaddleOCRDocumentParser(ocr_factory=lambda: FakePaddleOCR3())

    document = parser.parse("backend/tests/fixtures/demo_resume.png")

    assert document.pages[0].blocks[0].text == "真实OCR文本"
    assert document.pages[0].blocks[0].bbox.x0 == 10


def test_paddleocr_parser_uses_page_dimensions_from_rendered_image() -> None:
    parser = PaddleOCRDocumentParser(ocr_factory=lambda: FakePaddleOCR3())

    pages = parser._raw_result_to_pages(
        [
            {
                "rec_texts": ["真实OCR文本"],
                "rec_polys": [[[10, 20], [110, 20], [110, 50], [10, 50]]],
                "page_width": 893,
                "page_height": 1263,
            }
        ]
    )

    assert pages[0].width == 893
    assert pages[0].height == 1263


def test_paddleocr_parser_renders_pdf_pages_before_ocr(monkeypatch) -> None:
    parser = PaddleOCRDocumentParser(ocr_factory=lambda: FakePaddleOCR3())
    rendered_paths: list[str] = []

    class FakeBitmap:
        def to_pil(self):
            class FakeImage:
                size = (893, 1263)

                def save(self, path):
                    rendered_paths.append(str(path))
                    path.write_bytes(b"fake image")

            return FakeImage()

    class FakePage:
        def render(self, scale: float):
            return FakeBitmap()

    class FakePdfDocument:
        def __init__(self, path: str) -> None:
            self.pages = [FakePage()]

        def __len__(self) -> int:
            return len(self.pages)

        def __getitem__(self, index: int):
            return self.pages[index]

    import auditx.document_pipeline.paddleocr_parser as parser_module

    monkeypatch.setattr(
        parser_module,
        "pdfium",
        type("FakePdfium", (), {"PdfDocument": FakePdfDocument}),
        raising=False,
    )

    document = parser.parse("backend/tests/fixtures/demo_resume.pdf")

    assert rendered_paths
    assert document.pages[0].blocks[0].text == "真实OCR文本"
    assert document.pages[0].width == 893
    assert document.pages[0].height == 1263
