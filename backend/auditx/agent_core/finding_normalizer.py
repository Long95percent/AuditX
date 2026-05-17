from auditx.domain.audit import AuditFinding


class FindingNormalizer:
    def normalize(self, findings: list[AuditFinding]) -> list[AuditFinding]:
        return sorted(findings, key=lambda finding: (finding.risk_level.value, finding.finding_id))
