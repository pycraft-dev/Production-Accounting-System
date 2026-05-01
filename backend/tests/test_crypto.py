"""Тест шифрования файлов."""

from __future__ import annotations

from app.core.crypto import decrypt_file_bytes, encrypt_file_bytes, generate_encryption_key_base64


def test_aes_roundtrip() -> None:
    """AES-GCM шифрование и расшифровка."""

    key = generate_encryption_key_base64()
    plain = b"secret data \xff binary"
    blob = encrypt_file_bytes(plain, key)
    assert decrypt_file_bytes(blob, key) == plain
