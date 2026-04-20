from src.policies import apply_policy
from src.reviewer.models import (
    DocumentationSections,
    Finding,
    PolicyConfig,
    ReviewDecision,
    ReviewOutput,
    RiskLevel,
)


def _base_output() -> ReviewOutput:
    return ReviewOutput(
        summary="summary",
        overall_decision=ReviewDecision.WARN,
        risk_level=RiskLevel.MEDIUM,
        findings=[],
        generated_documentation=DocumentationSections(
            pr_summary="pr",
            files_changed_overview="files",
            key_risks="risks",
            design_technical_notes="notes",
            test_recommendations="tests",
            release_notes="release",
        ),
        mandatory_issues=[],
        optional_recommendations=[],
        policy_notes=[],
    )


def test_policy_fails_when_high_confidence_high_severity_exists() -> None:
    output = _base_output()
    output.findings = [
        Finding(
            id="F1",
            title="Auth bypass",
            severity="high",
            category="security",
            file="src/auth.py",
            line=90,
            explanation="Missing role check",
            suggestion="enforce authorization middleware",
            confidence=0.91,
            is_mandatory=False,
        )
    ]

    config = PolicyConfig.with_mode_defaults(PolicyConfig(mode="balanced"))
    updated = apply_policy(output, config)

    assert updated.overall_decision == ReviewDecision.FAIL
    assert len(updated.mandatory_issues) == 1


def test_policy_warns_in_advisory_mode() -> None:
    output = _base_output()
    output.findings = [
        Finding(
            id="F1",
            title="Doc gap",
            severity="low",
            category="documentation",
            file="README.md",
            line=3,
            explanation="No migration note",
            suggestion="Add release note section",
            confidence=0.8,
            is_mandatory=False,
        )
    ]

    config = PolicyConfig.with_mode_defaults(PolicyConfig(mode="advisory"))
    updated = apply_policy(output, config)

    assert updated.overall_decision == ReviewDecision.WARN
