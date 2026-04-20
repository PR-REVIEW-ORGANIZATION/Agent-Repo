# Reusable PR Review Agent

Production-ready AI PR review agent that can be consumed by other repositories as:
- a CLI (`python -m src.cli.main ...`)
- a callable Python library (`from src.reviewer import review_pr`)

It analyzes PR metadata + code changes, returns validated structured JSON, and renders deterministic markdown for PR comments or CI artifacts.

## Features

- Input contract for PR metadata, changed files, full diff, optional file contents, and optional review guidelines
- Review focus areas:
  - correctness
  - bugs/regressions
  - security
  - performance
  - maintainability
  - architecture consistency
  - test/documentation gaps
- Structured JSON output with findings and generated docs sections
- Policy engine with strict/balanced/advisory modes and CI fail logic
- Output schema validation (`src/schemas/review-output.schema.json`)
- Deterministic markdown generator
- Logging hooks in CLI and reviewer engine
- Unit tests for parsing, schema, markdown formatting, and policy decisions

## Repository Layout

```text
Agent-Repo/
  .github/workflows/
    reusable-pr-ai-review.yml
  src/
    reviewer/
      __init__.py
      api.py
      models.py
    prompts/
      __init__.py
      system_prompt.py
      user_prompt.py
    schemas/
      __init__.py
      review-output.schema.json
      validator.py
    formatters/
      __init__.py
      markdown.py
    policies/
      __init__.py
      engine.py
    cli/
      __init__.py
      main.py
  scripts/
    ai_pr_review.py
  tests/
  examples/
    example-input.json
    example-review-output.json
    example-report.md
  sample-config.json
  requirements.txt
```

## Install

```bash
pip install -r requirements.txt
```

## CLI Usage

Run review from PR input JSON:

```bash
python -m src.cli.main \
  --input examples/example-input.json \
  --config sample-config.json \
  --output-json review-output.json \
  --output-md review-report.md \
  --model gpt-5-mini \
  --fail-on-decision
```

Required env var:
- `OPENAI_API_KEY`

CLI exit codes:
- `0`: success
- `1`: runtime failure
- `2`: malformed/missing input
- `3`: `--fail-on-decision` and overall decision is `fail`

## Library Usage

```python
from src.reviewer import review_pr
from src.formatters import render_markdown_report
from src.reviewer.models import PRReviewInput

payload = {
    "repo_name": "org/repo",
    "pr_number": 42,
    "pr_title": "Refactor auth middleware",
    "pr_description": "...",
    "base_branch": "main",
    "head_branch": "feature/auth-refactor",
    "changed_files": [
        {
            "filename": "src/auth.py",
            "status": "modified",
            "additions": 20,
            "deletions": 10,
            "patch": "@@ ...",
            "content": None,
        }
    ],
    "full_diff_patch": "diff --git ...",
    "repository_review_guidelines": "Prioritize backward compatibility",
}

policy = {
    "mode": "balanced",
    "fail_on_severities": ["critical", "high"],
    "enforced_categories": ["security", "correctness"],
    "fail_ci_on_high_or_critical": True,
    "minimum_confidence_to_enforce": 0.6,
    "allow_style_only_comments": False,
}

result = review_pr(payload=payload, policy_payload=policy, model="gpt-5-mini")
pr_input = PRReviewInput.model_validate(payload)
markdown = render_markdown_report(pr_input, result)
```

## Reusable Workflow Consumption

Caller repository workflow example is in:
- `templates/test-repo-caller-workflow.yml`

Reusable workflow exposed by this repo:
- `.github/workflows/reusable-pr-ai-review.yml`

Caller passes:
- `repository`
- `pr_number`
- `is_draft`
- `openai_model`
- secret: `OPENAI_API_KEY`

Caller example:

```yaml
name: AI PR Review (Caller)

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

permissions:
  contents: read
  pull-requests: write

jobs:
  ai-pr-review:
    uses: <OWNER_OR_ORG>/Agent-Repo/.github/workflows/reusable-pr-ai-review.yml@main
    with:
      openai_model: gpt-5-mini
      repository: ${{ github.repository }}
      pr_number: ${{ github.event.pull_request.number }}
      is_draft: ${{ github.event.pull_request.draft }}
    secrets:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

Artifacts produced:
- `pr-review.md`
- `review-output.json`

Workflow outputs produced:
- `review_decision` (`pass`, `warn`, `fail`)
- `risk_level` (`low`, `medium`, `high`, `critical`)
- `findings_count` (integer)

The workflow also writes an `AI PR Review Decision` section to the GitHub Actions run summary.

## Compatibility And Migration

- Current contract is compatible with the Test-Repo caller workflow above.
- No caller changes are required for repositories already passing:
  - `openai_model`
  - `repository`
  - `pr_number`
  - `is_draft`
  - secret `OPENAI_API_KEY`
- Behavior note: policy decision is now explicitly surfaced through reusable-workflow outputs and job summary.

## Policy Configuration

See `sample-config.json`.

Supported controls:
- severity thresholds (`fail_on_severities`)
- categories to enforce (`enforced_categories`)
- CI fail behavior (`fail_ci_on_high_or_critical`)
- mode (`strict`, `balanced`, `advisory`)
- confidence threshold (`minimum_confidence_to_enforce`)
- style-only noise control (`allow_style_only_comments`)

## Testing

```bash
pytest -q
```

Current tests cover:
- malformed/incomplete PR input handling
- review output schema validation
- deterministic markdown generation
- policy decision logic

## Extensibility

The design is intentionally modular:
- `src/prompts/` for prompt variants and specialized reviewer personas
- `src/reviewer/` for orchestration and model providers
- `src/policies/` for custom organization-level gating policies
- `src/formatters/` for alternate output formats (Jira, SARIF, etc.)
