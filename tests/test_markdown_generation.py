from src.formatters import render_markdown_report
from src.reviewer.models import (
    DocumentationSections,
    Finding,
    PRFile,
    PRReviewInput,
    ReviewDecision,
    ReviewOutput,
    RiskLevel,
)


def test_markdown_generation_is_deterministic() -> None:
    pr_input = PRReviewInput(
        repo_name="org/repo",
        pr_number=10,
        pr_title="Improve cache layer",
        pr_description="desc",
        base_branch="main",
        head_branch="feature/cache",
        changed_files=[
            PRFile(filename="src/cache.py", status="modified", additions=10, deletions=2),
            PRFile(filename="tests/test_cache.py", status="added", additions=20, deletions=0),
        ],
    )

    output = ReviewOutput(
        summary="summary",
        overall_decision=ReviewDecision.WARN,
        risk_level=RiskLevel.MEDIUM,
        findings=[
            Finding(
                id="F2",
                title="Missing concurrent test",
                severity="medium",
                category="testing",
                file="tests/test_cache.py",
                line=12,
                explanation="No concurrent coverage",
                suggestion="Add a parallel access test",
                confidence=0.74,
            ),
            Finding(
                id="F1",
                title="Potential stale entry",
                severity="high",
                category="correctness",
                file="src/cache.py",
                line=45,
                explanation="Stale values may persist",
                suggestion="Add TTL invalidation",
                confidence=0.83,
                is_mandatory=True,
            ),
        ],
        generated_documentation=DocumentationSections(
            pr_summary="PR summary",
            files_changed_overview="Files changed overview",
            key_risks="Key risks",
            design_technical_notes="Design notes",
            test_recommendations="Test recommendations",
            release_notes="Release notes",
        ),
        mandatory_issues=["src/cache.py:45 Potential stale entry"],
        optional_recommendations=["tests/test_cache.py:12 Missing concurrent test"],
        policy_notes=[],
    )

    markdown = render_markdown_report(pr_input, output)

    assert "# PR Review Report" in markdown
    assert "Decision: **WARN**" in markdown
    assert markdown.index("Potential stale entry") < markdown.index("Missing concurrent test")
