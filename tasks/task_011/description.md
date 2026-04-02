# Task 011: Extract Duplicated Validation Logic

## Current State

`src/forms.py` contains two form classes — `LoginForm` and `RegistrationForm`. Both classes have `validate()` methods that perform email and password validation. The validation logic is **copy-pasted** between the two classes with minor cosmetic differences (variable names, error message wording), but the core rules are identical:

- **Email validation**: must contain `@`, must have a domain part with a `.`, must be non-empty, must be <= 254 characters.
- **Password validation**: must be >= 8 characters, must contain at least one uppercase letter, one lowercase letter, one digit, and one special character.

This is a textbook DRY violation. If validation rules change, both classes must be updated independently, risking inconsistencies.

## Code Smell

- **Duplicated Code** — The same validation logic exists in two places.
- Both `validate()` methods are ~30 lines each, with ~80% identical logic.

## Requested Refactoring

Extract the duplicated validation into standalone module-level functions:

1. `validate_email(email: str) -> list[str]` — returns a list of error strings (empty if valid).
2. `validate_password(password: str) -> list[str]` — returns a list of error strings (empty if valid).

Both `LoginForm.validate()` and `RegistrationForm.validate()` should delegate to these functions instead of inlining the logic.

## Acceptance Criteria

- [ ] `validate_email` and `validate_password` are importable from `src.forms`.
- [ ] Calling `validate_email("bad")` returns a non-empty list of error strings.
- [ ] Calling `validate_password("weak")` returns a non-empty list of error strings.
- [ ] `LoginForm.validate()` and `RegistrationForm.validate()` still work correctly and return the same results as before.
- [ ] No duplicated validation logic remains inside the form classes.
