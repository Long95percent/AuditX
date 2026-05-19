from datetime import datetime, timezone

import pytest

from auditx.domain.scoring import (
    CandidateLayer,
    CandidateScoreInput,
    JobTemplate,
    ScoringEngine,
    TopNSelector,
)


def test_low_education_with_strong_skills_is_potential_not_rejected() -> None:
    template = JobTemplate.sample_frontend()
    score_input = CandidateScoreInput(
        candidate_id="candidate_low_edu_strong_skill",
        completeness=0.9,
        hard_requirement_match=0.35,
        ability_match=0.95,
        experience_relevance=0.82,
        advantage_signals=["react", "typescript", "audit_trace"],
        risk_count=0,
    )

    result = ScoringEngine().score(score_input, template)

    assert result.layer == CandidateLayer.potential
    assert result.dimension_scores["hard_requirement_match"] == 35
    assert result.total_score >= 65
    assert "hard_requirement_low_not_eliminated" in result.calculation_details


def test_same_candidate_scores_differently_across_job_templates() -> None:
    score_input = CandidateScoreInput(
        candidate_id="candidate_cross_template",
        completeness=0.9,
        hard_requirement_match=0.75,
        ability_match=0.85,
        experience_relevance=0.7,
        advantage_signals=["react", "cost_control"],
        risk_count=1,
    )

    frontend_result = ScoringEngine().score(score_input, JobTemplate.sample_frontend())
    finance_result = ScoringEngine().score(score_input, JobTemplate.sample_finance())

    assert frontend_result.total_score != finance_result.total_score
    assert frontend_result.advantage_tags != finance_result.advantage_tags


def test_top_n_selector_respects_custom_n_and_tie_breakers() -> None:
    selector = TopNSelector(default_n=2)
    candidates = [
        CandidateScoreInput.scored_stub(
            candidate_id="older_more_risk",
            total_score=88,
            risk_count=2,
            advantage_count=3,
            created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        ),
        CandidateScoreInput.scored_stub(
            candidate_id="newer_less_risk",
            total_score=88,
            risk_count=1,
            advantage_count=2,
            created_at=datetime(2026, 5, 2, tzinfo=timezone.utc),
        ),
        CandidateScoreInput.scored_stub(
            candidate_id="lower_score",
            total_score=80,
            risk_count=0,
            advantage_count=5,
            created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
        ),
    ]

    selected = selector.select(candidates, n=1)

    assert [candidate.candidate_id for candidate in selected] == ["newer_less_risk"]


def test_top_n_selector_selects_all_when_input_smaller_than_n() -> None:
    selector = TopNSelector(default_n=20)
    candidates = [CandidateScoreInput.scored_stub(candidate_id="only_one", total_score=70)]

    assert selector.select(candidates) == candidates


def test_top_n_selector_rejects_invalid_n() -> None:
    selector = TopNSelector(default_n=20)

    with pytest.raises(ValueError, match="n must be greater than 0"):
        selector.select([], n=0)
