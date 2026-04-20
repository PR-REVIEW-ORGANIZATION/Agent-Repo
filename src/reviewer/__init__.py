from .models import (
    Finding,
    PolicyConfig,
    PRFile,
    PRReviewInput,
    ReviewDecision,
    ReviewOutput,
)

__all__ = [
    "Finding",
    "PolicyConfig",
    "PRFile",
    "PRReviewInput",
    "ReviewAgent",
    "ReviewDecision",
    "ReviewOutput",
    "review_pr",
]


def review_pr(*args, **kwargs):
    from .api import review_pr as _review_pr

    return _review_pr(*args, **kwargs)


class ReviewAgent:
    def __new__(cls, *args, **kwargs):
        from .api import ReviewAgent as _ReviewAgent

        return _ReviewAgent(*args, **kwargs)
