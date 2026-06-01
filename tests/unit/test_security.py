"""
tests/unit/test_security.py
----------------------------
Unit tests for security utilities (password hashing and JWT tokens).
"""

import pytest
from app.utils.security import hash_password, verify_password, create_access_token, decode_token


def test_password_hashing():
    """Hashed password is different from the original."""
    password = "MySecurePassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_password_verification_correct():
    """Correct password verifies successfully."""
    password = "CorrectPassword!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_password_verification_wrong():
    """Wrong password fails verification."""
    hashed = hash_password("CorrectPassword!")
    assert verify_password("WrongPassword!", hashed) is False


def test_create_and_decode_token():
    """A created token can be decoded to retrieve the original data."""
    token = create_access_token({"sub": "42"})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"


def test_decode_invalid_token():
    """An invalid token returns None."""
    result = decode_token("this.is.not.a.valid.token")
    assert result is None


def test_decode_tampered_token():
    """A tampered token (invalid signature) returns None."""
    token = create_access_token({"sub": "1"})
    # Tamper with the token by changing a character
    tampered = token[:-5] + "XXXXX"
    result = decode_token(tampered)
    assert result is None
