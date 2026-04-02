# Bug: Email validation regex is too restrictive

## Description

The `validate_email(email)` function uses a regex that does not allow dots (`.`) in the local part (before `@`) and does not allow hyphens (`-`) in the domain name. This causes valid emails like `john.doe@my-company.com` to be rejected.

## Expected Behavior

- `validate_email("user.name@example.com")` → `True`
- `validate_email("test@my-domain.co.uk")` → `True`
- `validate_email("first.last@sub.domain.org")` → `True`

## Actual Behavior

- All of the above return `False` because the regex pattern `^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z]{2,}$` requires the local part to be purely alphanumeric (no dots) and the domain label to be purely alphanumeric (no hyphens), and only allows a single domain level.

## How to Reproduce

```python
from validator import validate_email

print(validate_email("user.name@example.com"))    # Expected True, returns False
print(validate_email("test@my-domain.co.uk"))      # Expected True, returns False
```
