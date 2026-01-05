"""Password and token hashing utilities."""
import hashlib

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def hash_token(token: str) -> str:
    """Deterministic hash for opaque lookup of refresh tokens in the DB.

    Uses SHA-256 rather than bcrypt: refresh tokens are already
    high-entropy random strings (no need for salting against guessing),
    and we need an exact-match lookup, which a salted bcrypt hash can't do.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
