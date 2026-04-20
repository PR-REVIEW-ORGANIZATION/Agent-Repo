from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


class Mode(str, Enum):
    STRICT = "strict"
    BALANCED = "balanced"
    ADVISORY = "advisory"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Category(str, Enum):
    CORRECTNESS = "correctness"
    BUGS = "bugs"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    STYLE = "style"


class ReviewDecision(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PRFile(BaseModel):
    filename: str = Field(min_length=1)
    status: str = Field(default="modified")
    additions: int = Field(default=0, ge=0)
    deletions: int = Field(default=0, ge=0)
    patch: str | None = None
    content: str | None = None


class PRReviewInput(BaseModel):
    repo_name: str = Field(min_length=3, description="owner/repo")
    pr_number: int = Field(gt=0)
    pr_title: str = Field(min_length=1)
    pr_description: str | None = None
    base_branch: str = Field(min_length=1)
    head_branch: str = Field(min_length=1)
    changed_files: list[PRFile] = Field(default_factory=list)
    full_diff_patch: str | None = None
    repository_review_guidelines: str | None = None

    @field_validator("repo_name")
    @classmethod
    def _validate_repo_name(cls, value: str) -> str:
        if "/" not in value or value.startswith("/") or value.endswith("/"):
            raise ValueError("repo_name must look like 'owner/repo'")
        return value

    @field_validator("changed_files")
    @classmethod
    def _validate_changed_files(cls, value: list[PRFile]) -> list[PRFile]:
        if not value:
            raise ValueError("changed_files cannot be empty")
        return value


class Finding(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    severity: Severity
    category: Category
    file: str = Field(min_length=1)
    line: int | None = Field(default=None, ge=1)
    explanation: str = Field(min_length=1)
    suggestion: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    is_mandatory: bool = False


class DocumentationSections(BaseModel):
    pr_summary: str = Field(min_length=1)
    files_changed_overview: str = Field(min_length=1)
    key_risks: str = Field(min_length=1)
    design_technical_notes: str = Field(min_length=1)
    test_recommendations: str = Field(min_length=1)
    release_notes: str = Field(min_length=1)


class PolicyConfig(BaseModel):
    mode: Mode = Mode.BALANCED
    fail_on_severities: list[Severity] | None = None
    enforced_categories: list[Category] = Field(default_factory=list)
    fail_ci_on_high_or_critical: bool = True
    minimum_confidence_to_enforce: float = Field(default=0.55, ge=0, le=1)
    allow_style_only_comments: bool = False

    @classmethod
    def with_mode_defaults(cls, config: PolicyConfig | None = None) -> PolicyConfig:
        if config is None:
            config = cls()

        if config.fail_on_severities is not None:
            return config

        if config.mode == Mode.STRICT:
            config.fail_on_severities = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM]
        elif config.mode == Mode.BALANCED:
            config.fail_on_severities = [Severity.CRITICAL, Severity.HIGH]
        else:
            config.fail_on_severities = []
        return config


class ReviewOutput(BaseModel):
    summary: str = Field(min_length=1)
    overall_decision: ReviewDecision
    risk_level: RiskLevel
    findings: list[Finding]
    generated_documentation: DocumentationSections
    mandatory_issues: list[str] = Field(default_factory=list)
    optional_recommendations: list[str] = Field(default_factory=list)
    policy_notes: list[str] = Field(default_factory=list)


def validate_pr_input(payload: dict[str, Any]) -> PRReviewInput:
    try:
        return PRReviewInput.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid PR input: {exc}") from exc


def validate_policy(payload: dict[str, Any] | None) -> PolicyConfig:
    try:
        if payload is None:
            return PolicyConfig.with_mode_defaults()
        return PolicyConfig.with_mode_defaults(PolicyConfig.model_validate(payload))
    except ValidationError as exc:
        raise ValueError(f"Invalid policy config: {exc}") from exc


def validate_review_output(payload: dict[str, Any]) -> ReviewOutput:
    try:
        return ReviewOutput.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid review output: {exc}") from exc
