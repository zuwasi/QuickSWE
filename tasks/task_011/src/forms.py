"""Form classes for user authentication and registration."""

import re


class LoginForm:
    """Handles user login form data and validation."""

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.errors = []

    def validate(self):
        """Validate the login form fields. Returns True if valid."""
        self.errors = []

        # --- email checks (inlined) ---
        if not self.email or len(self.email.strip()) == 0:
            self.errors.append("Email is required")
        else:
            _email = self.email.strip()
            if len(_email) > 254:
                self.errors.append("Email must not exceed 254 characters")
            if "@" not in _email:
                self.errors.append("Email must contain an @ symbol")
            else:
                parts = _email.split("@")
                if len(parts) != 2 or len(parts[0]) == 0 or len(parts[1]) == 0:
                    self.errors.append("Email format is invalid")
                else:
                    domain = parts[1]
                    if "." not in domain:
                        self.errors.append("Email domain must contain a dot")
                    elif domain.startswith(".") or domain.endswith("."):
                        self.errors.append("Email domain is malformed")

        # --- password checks (inlined) ---
        if not self.password:
            self.errors.append("Password is required")
        else:
            pwd = self.password
            if len(pwd) < 8:
                self.errors.append("Password must be at least 8 characters")
            if not re.search(r"[A-Z]", pwd):
                self.errors.append("Password must contain an uppercase letter")
            if not re.search(r"[a-z]", pwd):
                self.errors.append("Password must contain a lowercase letter")
            if not re.search(r"\d", pwd):
                self.errors.append("Password must contain a digit")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
                self.errors.append("Password must contain a special character")

        return len(self.errors) == 0

    def get_errors(self):
        return list(self.errors)


class RegistrationForm:
    """Handles user registration form data and validation."""

    def __init__(self, username, email, password, password_confirm):
        self.username = username
        self.email = email
        self.password = password
        self.password_confirm = password_confirm
        self.errors = []

    def validate(self):
        """Validate the registration form fields. Returns True if valid."""
        self.errors = []

        # username check
        if not self.username or len(self.username.strip()) == 0:
            self.errors.append("Username is required")
        elif len(self.username.strip()) < 3:
            self.errors.append("Username must be at least 3 characters")
        elif len(self.username.strip()) > 30:
            self.errors.append("Username must be 30 characters or fewer")

        # --- email validation (copy-pasted from LoginForm, slightly different var names) ---
        email_val = self.email
        if not email_val or len(email_val.strip()) == 0:
            self.errors.append("Email is required")
        else:
            email_val = email_val.strip()
            if len(email_val) > 254:
                self.errors.append("Email must not exceed 254 characters")
            if "@" not in email_val:
                self.errors.append("Email must contain an @ symbol")
            else:
                email_parts = email_val.split("@")
                if len(email_parts) != 2 or len(email_parts[0]) == 0 or len(email_parts[1]) == 0:
                    self.errors.append("Email format is invalid")
                else:
                    email_domain = email_parts[1]
                    if "." not in email_domain:
                        self.errors.append("Email domain must contain a dot")
                    elif email_domain.startswith(".") or email_domain.endswith("."):
                        self.errors.append("Email domain is malformed")

        # --- password validation (copy-pasted from LoginForm) ---
        pw = self.password
        if not pw:
            self.errors.append("Password is required")
        else:
            if len(pw) < 8:
                self.errors.append("Password must be at least 8 characters")
            if not re.search(r"[A-Z]", pw):
                self.errors.append("Password must contain an uppercase letter")
            if not re.search(r"[a-z]", pw):
                self.errors.append("Password must contain a lowercase letter")
            if not re.search(r"\d", pw):
                self.errors.append("Password must contain a digit")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pw):
                self.errors.append("Password must contain a special character")

        # confirm-password check (unique to registration)
        if self.password != self.password_confirm:
            self.errors.append("Passwords do not match")

        return len(self.errors) == 0

    def get_errors(self):
        return list(self.errors)
