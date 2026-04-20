from src.reviewer.models import validate_pr_input


def test_validate_pr_input_accepts_valid_payload() -> None:
    payload = {
        "repo_name": "org/repo",
        "pr_number": 3,
        "pr_title": "Fix bug",
        "pr_description": "desc",
        "base_branch": "main",
        "head_branch": "feature/fix",
        "changed_files": [
            {
                "filename": "app.py",
                "status": "modified",
                "additions": 1,
                "deletions": 0,
                "patch": "@@ -1 +1 @@",
            }
        ],
    }

    parsed = validate_pr_input(payload)

    assert parsed.repo_name == "org/repo"
    assert parsed.pr_number == 3


def test_validate_pr_input_rejects_missing_changed_files() -> None:
    payload = {
        "repo_name": "org/repo",
        "pr_number": 3,
        "pr_title": "Fix bug",
        "base_branch": "main",
        "head_branch": "feature/fix",
        "changed_files": [],
    }

    try:
        validate_pr_input(payload)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "changed_files cannot be empty" in str(exc)
