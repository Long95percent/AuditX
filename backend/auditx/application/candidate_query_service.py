from pydantic import BaseModel

from auditx.domain.candidate import CandidateFindingRecord, CandidateProfile, CandidateScoreRecord
from auditx.domain.scoring import CandidateLayer
from auditx.infrastructure.storage.candidate_repository import InMemoryCandidateRepository


class CandidateListItem(BaseModel):
    profile: CandidateProfile
    latest_score: CandidateScoreRecord | None = None


class CandidateDetail(BaseModel):
    profile: CandidateProfile
    scores: list[CandidateScoreRecord]
    findings: list[CandidateFindingRecord]


class CandidateQueryService:
    def __init__(self, repository: InMemoryCandidateRepository) -> None:
        self.repository = repository

    def list_candidates(
        self,
        layer: CandidateLayer | None = None,
        min_score: float | None = None,
        max_risk_count: int | None = None,
    ) -> list[CandidateListItem]:
        items = [
            CandidateListItem(
                profile=profile,
                latest_score=self._latest_score(profile.candidate_id),
            )
            for profile in self.repository.list_profiles()
        ]
        if layer is not None:
            items = [
                item
                for item in items
                if item.latest_score is not None and item.latest_score.layer == layer
            ]
        if min_score is not None:
            items = [
                item
                for item in items
                if item.latest_score is not None and item.latest_score.total_score >= min_score
            ]
        if max_risk_count is not None:
            items = [
                item
                for item in items
                if item.latest_score is not None and item.latest_score.risk_count <= max_risk_count
            ]
        return items

    def top_n(self, limit: int) -> list[CandidateListItem]:
        candidates = []
        score_limit = max(limit, len(self.repository.list_scores()))
        for score in self.repository.top_scores(score_limit):
            profile = self.repository.get_profile(score.candidate_id)
            if profile is None:
                continue
            candidates.append(CandidateListItem(profile=profile, latest_score=score))
            if len(candidates) == limit:
                break
        return candidates

    def get_candidate(self, candidate_id: str) -> CandidateDetail | None:
        profile = self.repository.get_profile(candidate_id)
        if profile is None:
            return None
        return CandidateDetail(
            profile=profile,
            scores=self.repository.list_scores(candidate_id=candidate_id),
            findings=self.repository.list_findings(candidate_id=candidate_id),
        )

    def _latest_score(self, candidate_id: str) -> CandidateScoreRecord | None:
        scores = self.repository.list_scores(candidate_id=candidate_id)
        if not scores:
            return None
        return sorted(scores, key=lambda score: score.created_at, reverse=True)[0]
