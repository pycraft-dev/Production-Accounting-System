"""Шифрование файлов AES-256-GCM."""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12


def _get_key(key_b64: str) -> bytes:
    """Декодирует ключ AES-256 из Base64."""

    raw = base64.b64decode(key_b64)
    if len(raw) != 32:
        raise ValueError("Ключ AES должен быть 32 байта (256 бит) в Base64.")
    return raw


def encrypt_file_bytes(plaintext: bytes, key_base64: str) -> bytes:
    """
    Шифрует содержимое файла (AES-256-GCM).

    Формат выхода: nonce || ciphertext_with_tag.

    :param plaintext: исходные байты.
    :param key_base64: ключ в Base64 (32 байта).
    :returns: зашифрованный буфер.
    """

    key = _get_key(key_base64)
    nonce = os.urandom(NONCE_SIZE)
    aes = AESGCM(key)
    ct = aes.encrypt(nonce, plaintext, None)
    return nonce + ct


def decrypt_file_bytes(blob: bytes, key_base64: str) -> bytes:
    """
    Расшифровывает буфер, записанный через ``encrypt_file_bytes``.

    :param blob: nonce || ciphertext_with_tag.
    :param key_base64: ключ в Base64.
    :returns: исходные байты.
    """

    if len(blob) < NONCE_SIZE:
        raise ValueError("Некорректный шифртекст.")
    key = _get_key(key_base64)
    nonce = blob[:NONCE_SIZE]
    ct = blob[NONCE_SIZE:]
    aes = AESGCM(key)
    return aes.decrypt(nonce, ct, None)


def generate_encryption_key_base64() -> str:
    """Генерирует новый ключ AES-256 в Base64 (для заполнения .env)."""

    return base64.b64encode(os.urandom(32)).decode("ascii")
