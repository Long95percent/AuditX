from auditx.agent_core.llm_candidate_normalizer import LLMCandidateNormalizer
from auditx.agent_core.llm_mock_provider import LLMMockProvider
from auditx.domain.documents import ParsedDocument
from auditx.tool_registry.base import Tool, ToolResult


class LLMCandidateTool(Tool):
    name = "agent.llm_mock.candidate_discovery"
    description = "Runs the local LLM mock provider and returns normalized finding candidates."

    def __init__(
        self,
        provider: LLMMockProvider | None = None,
        normalizer: LLMCandidateNormalizer | None = None,
    ) -> None:
        self.provider = provider or LLMMockProvider()
        self.normalizer = normalizer or LLMCandidateNormalizer()

    def run(self, input_data: dict) -> ToolResult:
        document = input_data["document"]
        if not isinstance(document, ParsedDocument):
            return ToolResult(
                tool_name=self.name,
                ok=False,
                error="document must be a ParsedDocument",
            )
        output = self.provider.analyze(document)
        candidates = self.normalizer.normalize(output, document)
        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={
                "summary": output.summary,
                "candidates": candidates,
            },
        )
