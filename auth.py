import base64
import hashlib
import hmac
import os

ITERATIONS = 600_000


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("utf-8"))


def hash_password(password: str) -> str:
    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
    )

    return (
        f"pbkdf2_sha256${ITERATIONS}$"
        f"{_encode(salt)}${_encode(password_hash)}"
    )


def verify_password(password: str, saved_hash: str) -> bool:
    try:
        algorithm, iterations, salt_text, hash_text = saved_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        salt = _decode(salt_text)
        expected_hash = _decode(hash_text)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )

        return hmac.compare_digest(actual_hash, expected_hash)
    except (ValueError, TypeError):
        return False
