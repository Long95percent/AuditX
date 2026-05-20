import re
from datetime import date
from typing import Any

from auditx.domain.audit import RiskLevel
from auditx.domain.documents import ParsedDocument
from auditx.domain.review import FindingCandidate
from auditx.domain.scoring import JobTemplate, ScoringSignal
from auditx.tool_registry.base import Tool, ToolResult


def _document_text(document: ParsedDocument) -> str:
    return "\n".join(block.text for page in document.pages for block in page.blocks)


class AdvantageDictionaryTool(Tool):
    name = "resume.job.advantage_dictionary"
    description = "Matches job-template advantage dictionary entries against resume text."

    def run(self, input_data: dict[str, Any]) -> ToolResult:
        document = input_data["document"]
        job_template = input_data["job_template"]
        if not isinstance(document, ParsedDocument) or not isinstance(job_template, JobTemplate):
            return ToolResult(tool_name=self.name, ok=False, error="invalid document or job_template")
        text = _document_text(document).lower()
        signals = [
            signal
            for signal in job_template.advantage_dictionary
            if signal.lower() in text or job_template.advantage_dictionary[signal].lower() in text
        ]
        if "audit_trace" in job_template.advantage_dictionary and "审计" in text:
            signals.append("audit_trace")
        unique_signals = sorted(set(signals))
        scoring_signals = [
            ScoringSignal(
                signal_id=f"advantage:{signal}",
                category="advantage",
                value=signal,
                source_step=self.name,
                source_agent=self.name,
                reason=f"Matched advantage dictionary entry {signal}",
            )
            for signal in unique_signals
        ]
        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={
                "advantage_signals": unique_signals,
                "advantage_tags": [job_template.advantage_dictionary[signal] for signal in unique_signals],
                "scoring_signals": scoring_signals,
            },
        )


class ContactMissingRuleTool(Tool):
    name = "resume.rule.contact_missing"
    description = "Detects missing phone and email contact information."

    def run(self, input_data: dict[str, Any]) -> ToolResult:
        document = input_data["document"]
        text = _document_text(document)
        has_phone = re.search(r"1[3-9]\d{9}", text) is not None
        has_email = re.search(r"[\w.+-]+@[\w.-]+", text) is not None
        candidates = []
        if not has_phone and not has_email:
            candidates.append(
                FindingCandidate(
                    candidate_id="rule_contact_missing",
                    rule_id="resume.rule.contact_missing",
                    title="联系方式缺失",
                    description="简历中未识别到手机号或邮箱。",
                    risk_level=RiskLevel.low,
                    confidence=0.8,
                    source_agent=self.name,
                    suggestion="请 HR 复核候选人联系方式是否在附件或其它渠道提供。",
                )
            )
        return ToolResult(tool_name=self.name, ok=True, data={"candidates": candidates})


class EducationMissingRuleTool(Tool):
    name = "resume.rule.education_missing"
    description = "Detects missing education section keywords."

    def run(self, input_data: dict[str, Any]) -> ToolResult:
        document = input_data["document"]
        text = _document_text(document)
        has_education = any(keyword in text for keyword in ["本科", "硕士", "博士", "学历", "大学"])
        candidates = []
        if not has_education:
            candidates.append(
                FindingCandidate(
                    candidate_id="rule_education_missing",
                    rule_id="resume.rule.education_missing",
                    title="教育经历缺失",
                    description="简历中未识别到明确教育经历关键词。",
                    risk_level=RiskLevel.low,
                    confidence=0.75,
                    source_agent=self.name,
                    suggestion="请 HR 复核教育经历是否缺失或格式异常。",
                )
            )
        return ToolResult(tool_name=self.name, ok=True, data={"candidates": candidates})


class YearsExperienceRuleTool(Tool):
    name = "resume.rule.years_experience"
    description = "Calculates rough years of experience from year-month ranges."

    def run(self, input_data: dict[str, Any]) -> ToolResult:
        document = input_data["document"]
        text = _document_text(document)
        matches = re.findall(r"(20\d{2})\.(\d{2})\s*-\s*(20\d{2})\.(\d{2})", text)
        total_months = 0
        for start_year, start_month, end_year, end_month in matches:
            total_months += (int(end_year) - int(start_year)) * 12 + int(end_month) - int(start_month)
        years_experience = round(total_months / 12)
        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={
                "years_experience": years_experience,
                "scoring_signals": [
                    ScoringSignal(
                        signal_id="experience:years",
                        category="experience",
                        value=years_experience,
                        source_step=self.name,
                        source_agent=self.name,
                        reason="Calculated rough years of experience from resume date ranges",
                    )
                ],
            },
        )


class KeywordMatchRuleTool(Tool):
    name = "resume.rule.keyword_match"
    description = "Matches configured keywords against resume text."

    def __init__(self, keywords: list[str] | None = None) -> None:
        self.keywords = keywords or ["合规审计", "React", "TypeScript"]

    def run(self, input_data: dict[str, Any]) -> ToolResult:
        document = input_data["document"]
        text = _document_text(document)
        matched_keywords = [keyword for keyword in self.keywords if keyword in text]
        return ToolResult(
            tool_name=self.name,
            ok=True,
            data={
                "matched_keywords": matched_keywords,
                "scoring_signals": [
                    ScoringSignal(
                        signal_id=f"keyword:{keyword}",
                        category="hard_requirement",
                        value=keyword,
                        source_step=self.name,
                        source_agent=self.name,
                        reason=f"Matched resume keyword {keyword}",
                    )
                    for keyword in matched_keywords
                ],
            },
        )


class FailingRuleTool(Tool):
    name = "resume.rule.failing"
    description = "Test-only rule tool that raises an error."

    def run(self, input_data: dict[str, Any]) -> ToolResult:
        raise RuntimeError("rule failed")
