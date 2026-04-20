import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.formatters import render_markdown_report
from src.reviewer import review_pr
from src.reviewer.models import PolicyConfig, PRReviewInput


def getenv(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def github_request(method: str, url: str, token: str, **kwargs: Any) -> requests.Response:
    headers = kwargs.pop("headers", {})
    headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )
    response = requests.request(method, url, headers=headers, timeout=60, **kwargs)
    response.raise_for_status()
    return response


def fetch_pr(api_url: str, repo: str, pr_number: str, token: str) -> dict[str, Any]:
    url = f"{api_url}/repos/{repo}/pulls/{pr_number}"
    return github_request("GET", url, token).json()


def fetch_pr_files(api_url: str, repo: str, pr_number: str, token: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    page = 1
    while True:
        url = f"{api_url}/repos/{repo}/pulls/{pr_number}/files?per_page=100&page={page}"
        chunk = github_request("GET", url, token).json()
        if not chunk:
            break
        files.extend(chunk)
        page += 1
    return files


def find_existing_bot_comment(api_url: str, repo: str, pr_number: str, token: str) -> dict[str, Any] | None:
    url = f"{api_url}/repos/{repo}/issues/{pr_number}/comments?per_page=100"
    comments = github_request("GET", url, token).json()

    marker = "<!-- ai-pr-review-comment -->"
    for comment in comments:
        body = comment.get("body", "")
        if marker in body:
            return comment
    return None


def upsert_pr_comment(api_url: str, repo: str, pr_number: str, token: str, review_md: str) -> None:
    marker = "<!-- ai-pr-review-comment -->"
    body = f"{marker}\n# AI PR Review\n\n{review_md}"

    existing = find_existing_bot_comment(api_url, repo, pr_number, token)
    if existing:
        comment_id = existing["id"]
        url = f"{api_url}/repos/{repo}/issues/comments/{comment_id}"
        github_request("PATCH", url, token, json={"body": body})
    else:
        url = f"{api_url}/repos/{repo}/issues/{pr_number}/comments"
        github_request("POST", url, token, json={"body": body})


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", name)


def build_input_payload(repo: str, pr_number: int, pr: dict[str, Any], files: list[dict[str, Any]]) -> dict[str, Any]:
    changed_files: list[dict[str, Any]] = []
    full_patch_parts: list[str] = []

    for file_item in files:
        patch = file_item.get("patch", "")
        changed_files.append(
            {
                "filename": file_item.get("filename", "unknown"),
                "status": file_item.get("status", "modified"),
                "additions": file_item.get("additions", 0),
                "deletions": file_item.get("deletions", 0),
                "patch": patch,
            }
        )
        if patch:
            full_patch_parts.append(
                f"--- {file_item.get('filename', 'unknown')}\n{patch}\n"
            )

    return {
        "repo_name": repo,
        "pr_number": pr_number,
        "pr_title": pr.get("title", "Untitled PR"),
        "pr_description": pr.get("body") or "",
        "base_branch": pr.get("base", {}).get("ref", "main"),
        "head_branch": pr.get("head", {}).get("ref", "unknown"),
        "changed_files": changed_files,
        "full_diff_patch": "\n".join(full_patch_parts),
    }


def main() -> None:
    github_token = getenv("GITHUB_TOKEN")
    github_api_url = getenv("GITHUB_API_URL")
    repo = getenv("GITHUB_REPOSITORY")
    pr_number = int(getenv("PR_NUMBER"))
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini"

    pr = fetch_pr(github_api_url, repo, str(pr_number), github_token)
    files = fetch_pr_files(github_api_url, repo, str(pr_number), github_token)

    payload = build_input_payload(repo, pr_number, pr, files)
    pr_input = PRReviewInput.model_validate(payload)
    policy = PolicyConfig.with_mode_defaults()

    review_output = review_pr(
        payload=pr_input.model_dump(),
        policy_payload=policy.model_dump(),
        model=model,
    )
    review_md = render_markdown_report(pr_input, review_output)

    Path("review-output.json").write_text(
        json.dumps(review_output.model_dump(), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    with open("pr-review.md", "w", encoding="utf-8") as handle:
        handle.write("# AI PR Review Document\n\n")
        handle.write(f"- Repository: {repo}\n")
        handle.write(f"- PR Number: {pr_number}\n")
        handle.write(f"- Model: {sanitize_filename(model)}\n\n")
        handle.write(review_md)

    upsert_pr_comment(github_api_url, repo, str(pr_number), github_token, review_md)


if __name__ == "__main__":
    main()
