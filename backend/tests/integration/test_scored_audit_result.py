from auditx.agent_core.extractor_tool import ExtractorTool
from auditx.agent_core.fake_extractor import FakeExtractor
from auditx.agent_core.finding_normalizer import FindingNormalizer
from auditx.agent_core.llm_candidate_tool import LLMCandidateTool
from auditx.agent_core.rule_tools import AdvantageDictionaryTool, KeywordMatchRuleTool, YearsExperienceRuleTool
from auditx.application.audit_use_case import AuditUseCase
from auditx.document_pipeline.fake_parser import FakeDocumentParser
from auditx.domain.scoring import CandidateLayer, JobTemplate
from auditx.tool_registry.registry import ToolRegistry


def test_audit_use_case_includes_score_result_and_calculation_details() -> None:
    extractor = FakeExtractor()
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=extractor))
    registry.register(LLMCandidateTool())
    registry.register(AdvantageDictionaryTool())
    registry.register(YearsExperienceRuleTool())
    registry.register(KeywordMatchRuleTool(keywords=["合规审计"]))
    use_case = AuditUseCase(
        parser=FakeDocumentParser(),
        extractor=extractor,
        normalizer=FindingNormalizer(),
        tool_registry=registry,
        job_template=JobTemplate.sample_frontend(),
    )

    result = use_case.run(file_path="demo_resume.pdf")

    assert result.score is not None
    assert result.score.template_id == "frontend_engineer"
    assert result.score.layer in {CandidateLayer.best, CandidateLayer.potential}
    assert result.score.dimension_scores["completeness"] > 0
    assert result.score.calculation_details


def test_audit_use_case_builds_score_from_rule_signals_not_hardcoded_advantages() -> None:
    extractor = FakeExtractor()
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=extractor))
    registry.register(AdvantageDictionaryTool())
    use_case = AuditUseCase(
        parser=FakeDocumentParser(),
        extractor=extractor,
        normalizer=FindingNormalizer(),
        tool_registry=registry,
        job_template=JobTemplate.sample_frontend(),
    )

    result = use_case.run(file_path="demo_resume.pdf")

    assert result.score is not None
    assert result.score.advantage_tags == ["审查链路意识"]


def test_audit_use_case_records_scoring_in_review_trace() -> None:
    extractor = FakeExtractor()
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=extractor))
    registry.register(AdvantageDictionaryTool())
    registry.register(YearsExperienceRuleTool())
    use_case = AuditUseCase(
        parser=FakeDocumentParser(),
        extractor=extractor,
        normalizer=FindingNormalizer(),
        tool_registry=registry,
        job_template=JobTemplate.sample_frontend(),
    )

    result = use_case.run(file_path="demo_resume.pdf")

    scoring_steps = [step for step in result.trace.steps if step.name == "scoring_engine.score"]
    assert len(scoring_steps) == 1
    assert scoring_steps[0].status == "accepted"
    assert scoring_steps[0].metadata["template_id"] == "frontend_engineer"
    assert scoring_steps[0].metadata["total_score"] == result.score.total_score


def test_audit_use_case_score_details_include_signal_sources() -> None:
    extractor = FakeExtractor()
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=extractor))
    registry.register(AdvantageDictionaryTool())
    registry.register(YearsExperienceRuleTool())
    registry.register(KeywordMatchRuleTool(keywords=["合规审计"]))
    use_case = AuditUseCase(
        parser=FakeDocumentParser(),
        extractor=extractor,
        normalizer=FindingNormalizer(),
        tool_registry=registry,
        job_template=JobTemplate.sample_frontend(),
    )

    result = use_case.run(file_path="demo_resume.pdf")

    assert result.score is not None
    assert "signal:advantage:audit_trace source=resume.job.advantage_dictionary" in result.score.calculation_details
    assert "signal:experience:years source=resume.rule.years_experience" in result.score.calculation_details
    assert "signal:keyword:合规审计 source=resume.rule.keyword_match" in result.score.calculation_details
    scoring_step = next(step for step in result.trace.steps if step.name == "scoring_engine.score")
    assert "scoring_signals" in scoring_step.metadata
    assert scoring_step.metadata["scoring_signals"][0]["source_step"]


def test_same_resume_gets_different_match_results_across_job_templates() -> None:
    frontend_result = _run_scored_audit(JobTemplate.sample_frontend())
    finance_result = _run_scored_audit(JobTemplate.sample_finance())

    assert frontend_result.score is not None
    assert finance_result.score is not None
    assert frontend_result.score.template_id == "frontend_engineer"
    assert finance_result.score.template_id == "finance_specialist"
    assert frontend_result.score.total_score != finance_result.score.total_score
    assert frontend_result.score.advantage_tags != finance_result.score.advantage_tags


def _run_scored_audit(job_template: JobTemplate):
    extractor = FakeExtractor()
    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=extractor))
    registry.register(LLMCandidateTool())
    registry.register(AdvantageDictionaryTool())
    registry.register(YearsExperienceRuleTool())
    registry.register(KeywordMatchRuleTool(keywords=["合规审计"]))
    use_case = AuditUseCase(
        parser=FakeDocumentParser(),
        extractor=extractor,
        normalizer=FindingNormalizer(),
        tool_registry=registry,
        job_template=job_template,
    )
    return use_case.run(file_path="demo_resume.pdf")
