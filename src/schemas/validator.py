from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ModuleNotFoundError:  # pragma: no cover
    jsonschema = None

from ..reviewer.models import validate_review_output


def schema_path() -> Path:
    return Path(__file__).resolve().parent / "review-output.schema.json"


def load_review_output_schema() -> dict[str, Any]:
    with schema_path().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_output_schema(payload: dict[str, Any]) -> None:
    if jsonschema is not None:
        jsonschema.validate(instance=payload, schema=load_review_output_schema())
        return
    validate_review_output(payload)
