from auditx.domain.documents import BBox, BlockType, DocumentPage, LayoutBlock, ParsedDocument
from auditx.document_pipeline.base import DocumentParser


class FakeDocumentParser(DocumentParser):
    def parse(self, file_path: str) -> ParsedDocument:
        return ParsedDocument(
            document_id="fake_doc_001",
            filename=file_path,
            pages=[
                DocumentPage(
                    page_number=1,
                    width=800,
                    height=1000,
                    blocks=[
                        LayoutBlock(
                            block_id="p1_b1",
                            page_number=1,
                            block_type=BlockType.paragraph,
                            text="候选人 2022.03 - 2024.05 任职于 A 公司，负责合规审计项目。",
                            bbox=BBox(x0=96, y0=180, x1=720, y1=224),
                        )
                    ],
                )
            ],
        )
