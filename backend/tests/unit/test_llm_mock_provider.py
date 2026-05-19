from auditx.agent_core.llm_mock_provider import LLMMockProvider
from auditx.agent_core.llm_candidate_normalizer import LLMCandidateNormalizer
from auditx.document_pipeline.fake_parser import FakeDocumentParser


def test_llm_mock_provider_returns_structured_candidates() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    output = LLMMockProvider().analyze(document)

    assert output.summary
    assert len(output.candidates) == 2
    assert output.candidates[0].evidence_quote == "任职于 A 公司"
    assert output.candidates[1].evidence_quote is None


def test_llm_candidate_normalizer_converts_mock_output_to_candidates() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    output = LLMMockProvider().analyze(document)
    candidates = LLMCandidateNormalizer().normalize(output, document)

    assert len(candidates) == 2
    assert candidates[0].candidate_id == "llm_candidate_company_a"
    assert candidates[0].evidences[0].block_id == "p1_b1"
    assert candidates[1].candidate_id == "llm_candidate_unverified_gap"
    assert candidates[1].evidences == []
