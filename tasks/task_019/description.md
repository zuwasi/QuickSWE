# Bug Report: Orders are being approved without going through submission review

## Summary

We use a state machine to manage order workflows. Orders should follow a defined lifecycle: draft → submitted → approved → fulfilled (or rejected/cancelled at certain points). The state machine enforces which transitions are allowed.

## Problem

QA discovered that orders in "draft" state can be directly approved without going through the submission and review process. This bypasses compliance checks that happen during the submission step.

Additionally, it seems like any transition can be triggered from any state, making the state machine essentially useless for enforcing workflow rules. The transitions are being registered correctly (we verified the configuration), but the runtime enforcement isn't working.

## Steps to Reproduce

1. Create a new order (starts in "draft" state)
2. Call `trigger("approve")` directly (without first doing `trigger("submit")`)
3. The order moves to "approved" state — this should NOT be allowed

## Expected Behavior

- `trigger("approve")` from "draft" should raise an `InvalidTransitionError`
- Only `trigger("submit")` should be valid from "draft"
- The state machine should validate that the current state matches the transition's source state

## Environment

- Python 3.10+
- Custom state machine implementation
