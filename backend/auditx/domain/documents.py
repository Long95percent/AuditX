from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class BlockType(StrEnum):
    title = "title"
    paragraph = "paragraph"
    table = "table"
    image = "image"
    header = "header"
    footer = "footer"


class BBox(BaseModel):
    x0: Annotated[float, Field(ge=0)]
    y0: Annotated[float, Field(ge=0)]
    x1: Annotated[float, Field(ge=0)]
    y1: Annotated[float, Field(ge=0)]

    @field_validator("x1")
    @classmethod
    def x1_must_be_right_of_x0(cls, value: float, info) -> float:
        x0 = info.data.get("x0")
        if x0 is not None and value <= x0:
            raise ValueError("x1 must be greater than x0")
        return value

    @field_validator("y1")
    @classmethod
    def y1_must_be_below_y0(cls, value: float, info) -> float:
        y0 = info.data.get("y0")
        if y0 is not None and value <= y0:
            raise ValueError("y1 must be greater than y0")
        return value


class LayoutBlock(BaseModel):
    block_id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    block_type: BlockType
    text: str = ""
    bbox: BBox


class DocumentPage(BaseModel):
    page_number: int = Field(ge=1)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    blocks: list[LayoutBlock] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    document_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    pages: list[DocumentPage] = Field(default_factory=list)
