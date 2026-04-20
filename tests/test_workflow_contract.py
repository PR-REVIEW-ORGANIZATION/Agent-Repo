from pathlib import Path


WORKFLOW_PATH = Path('.github/workflows/reusable-pr-ai-review.yml')


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding='utf-8')


def test_reusable_workflow_contract_matches_caller() -> None:
    text = _workflow_text()

    assert 'workflow_call:' in text
    assert 'openai_model:' in text
    assert 'default: gpt-5-mini' in text
    assert 'repository:' in text
    assert 'pr_number:' in text
    assert 'is_draft:' in text
    assert 'default: false' in text
    assert 'OPENAI_API_KEY:' in text


def test_reusable_workflow_surfaces_policy_and_artifacts() -> None:
    text = _workflow_text()

    assert 'outputs:' in text
    assert 'review_decision' in text
    assert 'risk_level' in text
    assert 'findings_count' in text
    assert 'AI PR Review Decision' in text
    assert 'path: |' in text
    assert 'pr-review.md' in text
    assert 'review-output.json' in text
