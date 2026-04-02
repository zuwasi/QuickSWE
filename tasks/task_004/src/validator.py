import re


def validate_email(email):
    """Validate an email address and return True if valid, False otherwise.

    A valid email has:
    - A local part that may contain alphanumerics, dots, underscores, hyphens
    - An @ symbol
    - A domain that may contain alphanumerics and hyphens, with dot-separated labels
    - A TLD of at least 2 characters
    """
    # BUG: regex doesn't allow dots in local part, hyphens in domain,
    # or multiple domain levels (e.g. co.uk)
    pattern = r"^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))
