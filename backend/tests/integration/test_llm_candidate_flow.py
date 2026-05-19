from auditx.agent_core.extractor_tool import ExtractorTool
from auditx.agent_core.fake_extractor import FakeExtractor
from auditx.agent_core.llm_candidate_tool import LLMCandidateTool
from auditx.agent_core.orchestrator import AgentOrchestrator
from auditx.document_pipeline.fake_parser import FakeDocumentParser
from auditx.tool_registry.registry import ToolRegistry


def test_orchestrator_accepts_evidence_backed_llm_candidate_and_rejects_unverified_one() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=FakeExtractor()))
    registry.register(LLMCandidateTool())
    orchestrator = AgentOrchestrator(tool_registry=registry)

    draft = orchestrator.review(document)

    finding_ids = {finding.finding_id for finding in draft.findings}
    assert "llm_candidate_company_a" in finding_ids
    assert "llm_candidate_unverified_gap" not in finding_ids
    assert draft.rejected_count == 1
    assert any(step.name == "agent.llm_mock.candidate_discovery" for step in draft.trace.steps)
    assert any(
        step.metadata.get("candidate_id") == "llm_candidate_unverified_gap"
        and step.status == "rejected"
        for step in draft.trace.steps
    )
