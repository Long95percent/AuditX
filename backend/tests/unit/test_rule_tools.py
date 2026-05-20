from auditx.agent_core.rule_tools import (
    AdvantageDictionaryTool,
    ContactMissingRuleTool,
    EducationMissingRuleTool,
    KeywordMatchRuleTool,
    YearsExperienceRuleTool,
)
from auditx.document_pipeline.fake_parser import FakeDocumentParser
from auditx.domain.scoring import JobTemplate


def test_advantage_dictionary_tool_returns_scoring_signals() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    result = AdvantageDictionaryTool().run(
        {"document": document, "job_template": JobTemplate.sample_frontend()}
    )

    assert result.ok is True
    assert "audit_trace" in result.data["advantage_signals"]
    assert "审查链路意识" in result.data["advantage_tags"]
    signal = result.data["scoring_signals"][0]
    assert signal.signal_id == "advantage:audit_trace"
    assert signal.category == "advantage"
    assert signal.source_step == "resume.job.advantage_dictionary"


def test_contact_missing_rule_returns_finding_candidate() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    result = ContactMissingRuleTool().run({"document": document})

    assert result.ok is True
    assert result.data["candidates"][0].candidate_id == "rule_contact_missing"
    assert result.data["candidates"][0].evidences == []


def test_education_missing_rule_returns_finding_candidate() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    result = EducationMissingRuleTool().run({"document": document})

    assert result.ok is True
    assert result.data["candidates"][0].candidate_id == "rule_education_missing"


def test_years_experience_rule_returns_scoring_signal() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    result = YearsExperienceRuleTool().run({"document": document})

    assert result.ok is True
    assert result.data["years_experience"] == 2
    signal = result.data["scoring_signals"][0]
    assert signal.signal_id == "experience:years"
    assert signal.category == "experience"
    assert signal.value == 2
    assert signal.source_step == "resume.rule.years_experience"


def test_keyword_match_rule_returns_scoring_signal() -> None:
    document = FakeDocumentParser().parse("demo_resume.pdf")
    result = KeywordMatchRuleTool(keywords=["合规审计", "React"]).run({"document": document})

    assert result.ok is True
    assert result.data["matched_keywords"] == ["合规审计"]
    signal = result.data["scoring_signals"][0]
    assert signal.signal_id == "keyword:合规审计"
    assert signal.category == "hard_requirement"
    assert signal.source_step == "resume.rule.keyword_match"
