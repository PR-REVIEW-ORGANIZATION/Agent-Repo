from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from ..formatters import render_markdown_report
from ..reviewer import review_pr
from ..reviewer.models import ReviewDecision, validate_policy, validate_pr_input

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run reusable AI PR review from JSON input")
    parser.add_argument("--input", required=True, help="Path to PR input JSON")
    parser.add_argument("--config", help="Path to policy config JSON")
    parser.add_argument("--output-json", default="review-output.json", help="Output path for structured JSON")
    parser.add_argument("--output-md", default="review-report.md", help="Output path for markdown report")
    parser.add_argument("--model", default="gpt-5-mini", help="OpenAI model")
    parser.add_argument(
        "--fail-on-decision",
        action="store_true",
        help="Exit non-zero when overall decision is fail",
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser.parse_args()


def _load_json(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_openai_client():
    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("openai package is required for CLI execution") from exc
    return OpenAI()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    try:
        raw_input = _load_json(args.input)
        pr_input = validate_pr_input(raw_input)

        policy_payload = _load_json(args.config) if args.config else None
        policy = validate_policy(policy_payload)

        output = review_pr(
            payload=pr_input.model_dump(),
            policy_payload=policy.model_dump(),
            model=args.model,
            client=_build_openai_client(),
        )

        Path(args.output_json).write_text(
            json.dumps(output.model_dump(), indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        Path(args.output_md).write_text(
            render_markdown_report(pr_input, output),
            encoding="utf-8",
        )

        logger.info("Wrote review JSON to %s", args.output_json)
        logger.info("Wrote markdown report to %s", args.output_md)

        if args.fail_on_decision and output.overall_decision == ReviewDecision.FAIL:
            return 3
        return 0
    except FileNotFoundError as exc:
        logger.error("Input file missing: %s", exc)
        return 2
    except json.JSONDecodeError as exc:
        logger.error("Malformed JSON input: %s", exc)
        return 2
    except Exception as exc:  # noqa: BLE001
        logger.exception("Review run failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
