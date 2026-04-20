# PR Review Report

- Repository: `acme/payments-service`
- PR: #128
- Branches: `feature/idempotency-guard` -> `main`
- Decision: **WARN**
- Risk Level: **MEDIUM**

## PR Summary
Introduces Idempotency-Key handling for charge creation and adds baseline tests.

## Files Changed Overview
Updates API charge creation flow and extends charge endpoint tests.

Changed files: 2 (modified=2)

## Key Risks
Stale cache replay and untested concurrent retry behavior.

## Design / Technical Notes
Cache keying is clear, but lifecycle policy for cache entries should be explicit.

## Findings
- [HIGH][correctness] Cached response can outlive business validity window
  - Location: src/api/charges.py:47
  - Confidence: 0.82
  - Why: Idempotency responses are returned without checking expiration metadata, which can replay stale state after settlement changes.
  - Fix: Store response with an explicit TTL and validate freshness before returning the cached payload.
  - Required: yes

- [MEDIUM][testing] Missing race-condition coverage for parallel retries
  - Location: tests/test_charges.py:89
  - Confidence: 0.77
  - Why: Current tests validate sequential idempotency only and do not assert behavior when two requests arrive at the same time.
  - Fix: Add a parallel execution test that verifies exactly one charge intent is created across concurrent requests.
  - Required: no

## Test Recommendations
Add concurrency test and a stale-entry invalidation test.

## Release Notes
Charge endpoint now requires Idempotency-Key and may return cached responses for duplicate requests.

## Mandatory Issues
- src/api/charges.py:47 Cached response can outlive business validity window

## Optional Recommendations
- tests/test_charges.py:89 Missing race-condition coverage for parallel retries
