from __future__ import annotations

import json

from ..reviewer.models import PolicyConfig, PRReviewInput


def build_user_prompt(pr_input: PRReviewInput, policy: PolicyConfig) -> str:
    file_entries: list[dict[str, object]] = []
    for file in pr_input.changed_files:
        file_entries.append(
            {
                "filename": file.filename,
                "status": file.status,
                "additions": file.additions,
                "deletions": file.deletions,
                "patch": file.patch,
                "content": file.content,
            }
        )

    payload = {
        "pr": {
            "repo_name": pr_input.repo_name,
            "pr_number": pr_input.pr_number,
            "title": pr_input.pr_title,
            "description": pr_input.pr_description or "",
            "base_branch": pr_input.base_branch,
            "head_branch": pr_input.head_branch,
            "full_diff_patch": pr_input.full_diff_patch or "",
            "changed_files": file_entries,
            "repository_review_guidelines": pr_input.repository_review_guidelines or "",
        },
        "policy": {
            "mode": policy.mode.value,
            "fail_on_severities": [s.value for s in (policy.fail_on_severities or [])],
            "enforced_categories": [c.value for c in policy.enforced_categories],
            "allow_style_only_comments": policy.allow_style_only_comments,
            "minimum_confidence_to_enforce": policy.minimum_confidence_to_enforce,
        },
        "expected_output_contract": {
            "summary": "string",
            "overall_decision": "pass|warn|fail",
            "risk_level": "low|medium|high|critical",
            "findings": [
                {
                    "id": "string",
                    "title": "string",
                    "severity": "critical|high|medium|low|info",
                    "category": "correctness|bugs|security|performance|maintainability|architecture|testing|documentation|style",
                    "file": "path/to/file",
                    "line": "integer or null",
                    "explanation": "string",
                    "suggestion": "string",
                    "confidence": "0-1",
                    "is_mandatory": "boolean",
                }
            ],
            "generated_documentation": {
                "pr_summary": "string",
                "files_changed_overview": "string",
                "key_risks": "string",
                "design_technical_notes": "string",
                "test_recommendations": "string",
                "release_notes": "string",
            },
            "mandatory_issues": ["string"],
            "optional_recommendations": ["string"],
            "policy_notes": ["string"],
        },
    }

    return (
        "Review this pull request and return only JSON matching the expected contract. "
        "Do not wrap in markdown.\n\n"
        f"{json.dumps(payload, ensure_ascii=True, indent=2)}"
    )
