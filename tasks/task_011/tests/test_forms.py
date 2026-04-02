import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.forms import LoginForm, RegistrationForm


# ── pass-to-pass: LoginForm behaviour ──────────────────────────────

class TestLoginFormPassToPass:
    def test_valid_login(self):
        form = LoginForm("alice@example.com", "Str0ng!Pass")
        assert form.validate() is True
        assert form.get_errors() == []

    def test_login_missing_email(self):
        form = LoginForm("", "Str0ng!Pass")
        assert form.validate() is False
        assert "Email is required" in form.get_errors()

    def test_login_bad_email_no_at(self):
        form = LoginForm("alice.example.com", "Str0ng!Pass")
        assert form.validate() is False
        assert "Email must contain an @ symbol" in form.get_errors()

    def test_login_bad_email_no_dot_in_domain(self):
        form = LoginForm("alice@localhost", "Str0ng!Pass")
        assert form.validate() is False
        assert "Email domain must contain a dot" in form.get_errors()

    def test_login_email_too_long(self):
        long_email = "a" * 250 + "@b.co"
        form = LoginForm(long_email, "Str0ng!Pass")
        assert form.validate() is False
        assert "Email must not exceed 254 characters" in form.get_errors()

    def test_login_missing_password(self):
        form = LoginForm("alice@example.com", "")
        assert form.validate() is False
        assert "Password is required" in form.get_errors()

    def test_login_short_password(self):
        form = LoginForm("alice@example.com", "Ab1!")
        assert form.validate() is False
        assert "Password must be at least 8 characters" in form.get_errors()

    def test_login_password_no_uppercase(self):
        form = LoginForm("alice@example.com", "str0ng!pass")
        assert form.validate() is False
        assert "Password must contain an uppercase letter" in form.get_errors()

    def test_login_password_no_digit(self):
        form = LoginForm("alice@example.com", "Strongg!Pass")
        assert form.validate() is False
        assert "Password must contain a digit" in form.get_errors()

    def test_login_password_no_special(self):
        form = LoginForm("alice@example.com", "Str0ngPasss")
        assert form.validate() is False
        assert "Password must contain a special character" in form.get_errors()


# ── pass-to-pass: RegistrationForm behaviour ──────────────────────

class TestRegistrationFormPassToPass:
    def test_valid_registration(self):
        form = RegistrationForm("bob", "bob@example.com", "Str0ng!Pass", "Str0ng!Pass")
        assert form.validate() is True
        assert form.get_errors() == []

    def test_registration_missing_username(self):
        form = RegistrationForm("", "bob@example.com", "Str0ng!Pass", "Str0ng!Pass")
        assert form.validate() is False
        assert "Username is required" in form.get_errors()

    def test_registration_short_username(self):
        form = RegistrationForm("ab", "bob@example.com", "Str0ng!Pass", "Str0ng!Pass")
        assert form.validate() is False
        assert "Username must be at least 3 characters" in form.get_errors()

    def test_registration_bad_email(self):
        form = RegistrationForm("bob", "notanemail", "Str0ng!Pass", "Str0ng!Pass")
        assert form.validate() is False
        assert "Email must contain an @ symbol" in form.get_errors()

    def test_registration_weak_password(self):
        form = RegistrationForm("bob", "bob@example.com", "weak", "weak")
        assert form.validate() is False
        errors = form.get_errors()
        assert "Password must be at least 8 characters" in errors

    def test_registration_password_mismatch(self):
        form = RegistrationForm("bob", "bob@example.com", "Str0ng!Pass", "Different!1")
        assert form.validate() is False
        assert "Passwords do not match" in form.get_errors()

    def test_registration_email_domain_malformed(self):
        form = RegistrationForm("bob", "bob@.example.com", "Str0ng!Pass", "Str0ng!Pass")
        assert form.validate() is False
        assert "Email domain is malformed" in form.get_errors()


# ── fail-to-pass: extracted functions must exist ──────────────────

class TestExtractedValidators:
    @pytest.mark.fail_to_pass
    def test_validate_email_importable(self):
        from src.forms import validate_email
        assert callable(validate_email)

    @pytest.mark.fail_to_pass
    def test_validate_password_importable(self):
        from src.forms import validate_password
        assert callable(validate_password)

    @pytest.mark.fail_to_pass
    def test_validate_email_valid(self):
        from src.forms import validate_email
        errors = validate_email("alice@example.com")
        assert errors == []

    @pytest.mark.fail_to_pass
    def test_validate_email_missing_at(self):
        from src.forms import validate_email
        errors = validate_email("alice.example.com")
        assert any("@" in e for e in errors)

    @pytest.mark.fail_to_pass
    def test_validate_email_empty(self):
        from src.forms import validate_email
        errors = validate_email("")
        assert len(errors) > 0

    @pytest.mark.fail_to_pass
    def test_validate_password_valid(self):
        from src.forms import validate_password
        errors = validate_password("Str0ng!Pass")
        assert errors == []

    @pytest.mark.fail_to_pass
    def test_validate_password_too_short(self):
        from src.forms import validate_password
        errors = validate_password("Ab1!")
        assert any("8 characters" in e for e in errors)

    @pytest.mark.fail_to_pass
    def test_validate_password_no_special_char(self):
        from src.forms import validate_password
        errors = validate_password("Str0ngPasss")
        assert any("special" in e.lower() for e in errors)
