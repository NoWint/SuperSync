import gzip
import os
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

MAGIC = b"SSNC"
VERSION = 1
SALT_SIZE = 16
NONCE_SIZE = 12
KDF_ITERATIONS = 100_000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_data(data: bytes, password: str) -> bytes:
    """Encrypt data with AES-256-GCM after gzip compression.

    File format:
    [4 bytes: magic "SSNC"]
    [2 bytes: version (big endian)]
    [16 bytes: salt]
    [12 bytes: nonce]
    [4 bytes: compressed data length (big endian)]
    [N bytes: encrypted compressed data]
    [16 bytes: GCM tag]
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(password, salt)

    compressed = gzip.compress(data)
    compressed_len = len(compressed)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, compressed, None)

    encrypted_payload = ciphertext[:-16]
    gcm_tag = ciphertext[-16:]

    header = (
        MAGIC
        + struct.pack(">H", VERSION)
        + salt
        + nonce
        + struct.pack(">I", compressed_len)
    )

    return header + encrypted_payload + gcm_tag


def decrypt_data(encrypted: bytes, password: str) -> bytes:
    """Decrypt a .supersync file and return the original data."""
    if encrypted[:4] != MAGIC:
        raise ValueError("Invalid file format: missing SSNC magic bytes")

    version = struct.unpack(">H", encrypted[4:6])[0]
    if version != VERSION:
        raise ValueError(f"Unsupported version: {version}")

    salt = encrypted[6:22]
    nonce = encrypted[22:34]
    compressed_len = struct.unpack(">I", encrypted[34:38])[0]

    encrypted_payload = encrypted[38:38 + compressed_len]
    gcm_tag = encrypted[38 + compressed_len:38 + compressed_len + 16]

    key = _derive_key(password, salt)

    ciphertext = encrypted_payload + gcm_tag

    aesgcm = AESGCM(key)
    compressed = aesgcm.decrypt(nonce, ciphertext, None)

    return gzip.decompress(compressed)
