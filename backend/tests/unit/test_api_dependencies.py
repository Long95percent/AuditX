from auditx.api.dependencies import build_document_parser
from auditx.document_pipeline.fake_parser import FakeDocumentParser
from auditx.document_pipeline.paddleocr_parser import PaddleOCRDocumentParser


def test_build_document_parser_defaults_to_paddleocr() -> None:
    parser = build_document_parser("paddleocr")

    assert isinstance(parser, PaddleOCRDocumentParser)


def test_build_document_parser_allows_fake_for_tests() -> None:
    parser = build_document_parser("fake")

    assert isinstance(parser, FakeDocumentParser)
