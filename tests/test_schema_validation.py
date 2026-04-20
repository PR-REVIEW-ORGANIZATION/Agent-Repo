from src.schemas import validate_output_schema


def test_output_schema_validation() -> None:
    payload = {
        "summary": "Looks mostly good",
        "overall_decision": "warn",
        "risk_level": "medium",
        "findings": [
            {
                "id": "F-1",
                "title": "Potential null dereference",
                "severity": "high",
                "category": "bugs",
                "file": "src/service.py",
                "line": 18,
                "explanation": "value can be None when flag is disabled",
                "suggestion": "guard for None before attribute access",
                "confidence": 0.88,
                "is_mandatory": True,
            }
        ],
        "generated_documentation": {
            "pr_summary": "Adds guard handling",
            "files_changed_overview": "Updates service layer",
            "key_risks": "No immediate release blocker",
            "design_technical_notes": "Flow remains aligned with existing architecture",
            "test_recommendations": "Add disabled-flag regression test",
            "release_notes": "Improves safety around null access",
        },
        "mandatory_issues": ["src/service.py:18 Potential null dereference"],
        "optional_recommendations": [],
        "policy_notes": [],
    }

    validate_output_schema(payload)
