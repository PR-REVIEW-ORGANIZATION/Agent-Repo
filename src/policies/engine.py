from __future__ import annotations

from ..reviewer.models import (
    Category,
    Finding,
    Mode,
    PolicyConfig,
    ReviewDecision,
    ReviewOutput,
    RiskLevel,
    Severity,
)


SEVERITY_RANK: dict[Severity, int] = {
    Severity.CRITICAL: 5,
    Severity.HIGH: 4,
    Severity.MEDIUM: 3,
    Severity.LOW: 2,
    Severity.INFO: 1,
}


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, Severity, Category, str, int | None]] = set()
    result: list[Finding] = []
    for finding in findings:
        key = (
            finding.title.strip().lower(),
            finding.severity,
            finding.category,
            finding.file,
            finding.line,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(finding)
    return result


def _risk_from_findings(findings: list[Finding]) -> RiskLevel:
    if any(f.severity == Severity.CRITICAL for f in findings):
        return RiskLevel.CRITICAL
    if any(f.severity == Severity.HIGH for f in findings):
        return RiskLevel.HIGH
    if any(f.severity == Severity.MEDIUM for f in findings):
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def apply_policy(output: ReviewOutput, policy: PolicyConfig) -> ReviewOutput:
    findings = dedupe_findings(output.findings)
    policy_notes = list(output.policy_notes)

    if not policy.allow_style_only_comments:
        findings = [f for f in findings if f.category != Category.STYLE]

    for finding in findings:
        finding.is_mandatory = (
            finding.severity in (policy.fail_on_severities or [])
            and finding.confidence >= policy.minimum_confidence_to_enforce
        )

    mandatory_findings = [f for f in findings if f.is_mandatory]
    if policy.enforced_categories:
        present = {f.category for f in findings}
        missing = [c for c in policy.enforced_categories if c not in present]
        if missing:
            policy_notes.append(
                "No findings in enforced categories: "
                + ", ".join(sorted(category.value for category in missing))
            )

    if policy.mode == Mode.ADVISORY:
        decision = ReviewDecision.WARN if findings else ReviewDecision.PASS
    elif mandatory_findings and policy.fail_ci_on_high_or_critical:
        decision = ReviewDecision.FAIL
    elif findings:
        decision = ReviewDecision.WARN
    else:
        decision = ReviewDecision.PASS

    mandatory = [f"{f.file}:{f.line or '?'} {f.title}" for f in mandatory_findings]
    optional = [f"{f.file}:{f.line or '?'} {f.title}" for f in findings if not f.is_mandatory]

    output.findings = findings
    output.mandatory_issues = mandatory
    output.optional_recommendations = optional
    output.overall_decision = decision
    output.risk_level = _risk_from_findings(findings)
    output.policy_notes = policy_notes
    return output


def sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda f: (
            -SEVERITY_RANK[f.severity],
            f.file,
            f.line if f.line is not None else 0,
            f.title.lower(),
        ),
    )
