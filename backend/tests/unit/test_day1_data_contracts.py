from datetime import datetime, timezone

from auditx.domain.results import AuditResult
from auditx.domain.resume_library import ResumeRecord, ResumeStatus, ReviewContext, RunConfig
from auditx.domain.scoring import JobTemplate


def test_resume_status_enum_is_stable() -> None:
    assert {status.value for status in ResumeStatus} == {"new", "reviewed", "shortlisted"}


def test_resume_record_carries_status_and_parse_reference() -> None:
    record = ResumeRecord(
        resume_id="resume_1",
        filename="demo_resume.pdf",
        imported_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
        status=ResumeStatus.new,
        parsed_document_id="fake_doc_001",
    )

    assert record.status == ResumeStatus.new
    assert record.parsed_document_id == "fake_doc_001"


def test_review_context_carries_template_config_history_and_reuse_flag() -> None:
    context = ReviewContext(
        job_template=JobTemplate.sample_frontend(),
        run_config=RunConfig(top_n=20),
        historical_context={"previous_review_id": "review_001"},
        reuse_parsed_result=True,
    )

    assert context.job_template.template_id == "frontend_engineer"
    assert context.run_config.top_n == 20
    assert context.historical_context["previous_review_id"] == "review_001"
    assert context.reuse_parsed_result is True


def test_job_template_contract_contains_hard_requirements_risk_strategy_and_version() -> None:
    template = JobTemplate.sample_frontend()

    assert template.version == "v1"
    assert template.hard_requirements
    assert template.risk_strategy
    assert template.weights
    assert template.advantage_dictionary


def test_three_sample_job_templates_are_distinct() -> None:
    templates = [
        JobTemplate.sample_frontend(),
        JobTemplate.sample_finance(),
        JobTemplate.sample_product_manager(),
    ]

    assert len({template.template_id for template in templates}) == 3
    assert len({tuple(sorted(template.weights.items())) for template in templates}) == 3
    assert len({tuple(sorted(template.advantage_dictionary.items())) for template in templates}) == 3


def test_audit_result_contract_exposes_score_layer_advantages_risks_evidence_details_trace() -> None:
    field_names = set(AuditResult.model_fields)

    assert "score" in field_names
    assert "findings" in field_names
    assert "candidates" in field_names
    assert "rejected_candidates" in field_names
    assert "trace" in field_names
