from auditx.agent_core.extractor import FindingExtractor
from auditx.domain.documents import ParsedDocument
from auditx.tool_registry.base import Tool, ToolResult


class ExtractorTool(Tool):
    name = "agent.extractor.fake"
    description = "Adapts the current finding extractor for AgentOrchestrator tool calls."

    def __init__(self, extractor: FindingExtractor) -> None:
        self.extractor = extractor

    def run(self, input_data: dict) -> ToolResult:
        document = input_data["document"]
        if not isinstance(document, ParsedDocument):
            return ToolResult(
                tool_name=self.name,
                ok=False,
                error="document must be a ParsedDocument",
            )
        findings = self.extractor.extract(document)
        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={"findings": findings},
        )
