from __future__ import annotations

from collections import Counter

from ..policies.engine import sort_findings
from ..reviewer.models import PRReviewInput, ReviewOutput


def _findings_section(output: ReviewOutput) -> str:
    findings = sort_findings(output.findings)
    if not findings:
        return "None"

    lines: list[str] = []
    for finding in findings:
        location = f"{finding.file}:{finding.line}" if finding.line else finding.file
        lines.append(
            "\n".join(
                [
                    f"- [{finding.severity.value.upper()}][{finding.category.value}] {finding.title}",
                    f"  - Location: {location}",
                    f"  - Confidence: {finding.confidence:.2f}",
                    f"  - Why: {finding.explanation}",
                    f"  - Fix: {finding.suggestion}",
                    f"  - Required: {'yes' if finding.is_mandatory else 'no'}",
                ]
            )
        )
    return "\n\n".join(lines)


def render_markdown_report(pr_input: PRReviewInput, output: ReviewOutput) -> str:
    status_counts = Counter(f.status for f in pr_input.changed_files)
    status_summary = ", ".join(
        f"{status}={count}" for status, count in sorted(status_counts.items())
    )

    lines = [
        "# PR Review Report",
        "",
        f"- Repository: `{pr_input.repo_name}`",
        f"- PR: #{pr_input.pr_number}",
        f"- Branches: `{pr_input.head_branch}` -> `{pr_input.base_branch}`",
        f"- Decision: **{output.overall_decision.value.upper()}**",
        f"- Risk Level: **{output.risk_level.value.upper()}**",
        "",
        "## PR Summary",
        output.generated_documentation.pr_summary,
        "",
        "## Files Changed Overview",
        output.generated_documentation.files_changed_overview,
        "",
        f"Changed files: {len(pr_input.changed_files)} ({status_summary})",
        "",
        "## Key Risks",
        output.generated_documentation.key_risks,
        "",
        "## Design / Technical Notes",
        output.generated_documentation.design_technical_notes,
        "",
        "## Findings",
        _findings_section(output),
        "",
        "## Test Recommendations",
        output.generated_documentation.test_recommendations,
        "",
        "## Release Notes",
        output.generated_documentation.release_notes,
        "",
        "## Mandatory Issues",
    ]

    if output.mandatory_issues:
        lines.extend(f"- {item}" for item in output.mandatory_issues)
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Optional Recommendations")
    if output.optional_recommendations:
        lines.extend(f"- {item}" for item in output.optional_recommendations)
    else:
        lines.append("- None")

    if output.policy_notes:
        lines.append("")
        lines.append("## Policy Notes")
        lines.extend(f"- {note}" for note in output.policy_notes)

    return "\n".join(lines).strip() + "\n"
