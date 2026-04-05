import pytest
def pytest_configure(config):
    config.addinivalue_line("markers", "fail_to_pass: tests that should fail before fix and pass after")
