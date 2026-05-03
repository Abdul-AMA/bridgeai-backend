"""
Encryption utilities for secure API key storage.

Uses Fernet symmetric encryption (AES-128 in CBC mode with PKCS7 padding)
for encrypting user API keys at rest.
"""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    _fernet: Optional[Fernet] = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """Get or create Fernet instance."""
        if cls._fernet is None:
            encryption_key = settings.ENCRYPTION_KEY
            if not encryption_key:
                raise ValueError("ENCRYPTION_KEY not configured in settings")

            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()

            cls._fernet = Fernet(encryption_key)
        return cls._fernet

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        fernet = cls._get_fernet()
        encrypted = fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    @classmethod
    def decrypt(cls, encrypted: str) -> Optional[str]:
        """
        Decrypt an encrypted string.

        Args:
            encrypted: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string, or None if decryption fails
        """
        if not encrypted:
            return None

        try:
            fernet = cls._get_fernet()
            decoded = base64.urlsafe_b64decode(encrypted.encode())
            decrypted = fernet.decrypt(decoded)
            return decrypted.decode()
        except (InvalidToken, ValueError, Exception):
            return None

    @classmethod
    def generate_key(cls) -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded encryption key
        """
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()


def encrypt_api_key(api_key: str) -> str:
    """Convenience function for encrypting API keys."""
    return EncryptionService.encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> Optional[str]:
    """Convenience function for decrypting API keys."""
    return EncryptionService.decrypt(encrypted_key)
