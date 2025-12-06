"""Test configuration for pytest."""

import pytest


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (may be slow)"
    )
