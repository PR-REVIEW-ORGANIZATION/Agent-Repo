from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from ..policies import apply_policy
from ..prompts import SYSTEM_PROMPT, build_user_prompt
from ..schemas import validate_output_schema
from .models import (
    PolicyConfig,
    PRReviewInput,
    ReviewOutput,
    validate_policy,
    validate_pr_input,
    validate_review_output,
)

logger = logging.getLogger(__name__)


class ReviewAgent:
    def __init__(self, model: str = "gpt-5-mini", client: OpenAI | None = None) -> None:
        self.model = model
        self.client = client or OpenAI()

    def review(self, pr_input: PRReviewInput, policy: PolicyConfig | None = None) -> ReviewOutput:
        policy = PolicyConfig.with_mode_defaults(policy)
        logger.info(
            "Starting review for %s PR #%s using mode=%s",
            pr_input.repo_name,
            pr_input.pr_number,
            policy.mode.value,
        )

        response_payload = self._call_model(pr_input, policy)
        output = validate_review_output(response_payload)
        output = apply_policy(output, policy)

        validate_output_schema(output.model_dump())
        logger.info(
            "Completed review for %s PR #%s with decision=%s and findings=%s",
            pr_input.repo_name,
            pr_input.pr_number,
            output.overall_decision.value,
            len(output.findings),
        )
        return output

    def _call_model(self, pr_input: PRReviewInput, policy: PolicyConfig) -> dict[str, Any]:
        user_prompt = build_user_prompt(pr_input, policy)
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )

        text = getattr(response, "output_text", "")
        if not text:
            raise RuntimeError("Model returned empty output")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            extracted = _extract_first_json_object(text)
            if extracted is None:
                raise RuntimeError("Model output is not valid JSON")
            return extracted


def _extract_first_json_object(raw: str) -> dict[str, Any] | None:
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < 0 or end <= start:
        return None

    candidate = raw[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None
    return parsed


def review_pr(
    payload: dict[str, Any],
    policy_payload: dict[str, Any] | None = None,
    model: str = "gpt-5-mini",
    client: OpenAI | None = None,
) -> ReviewOutput:
    pr_input = validate_pr_input(payload)
    policy = validate_policy(policy_payload)
    agent = ReviewAgent(model=model, client=client)
    return agent.review(pr_input, policy)
