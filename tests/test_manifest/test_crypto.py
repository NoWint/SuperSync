from supersync.manifest.crypto import encrypt_data, decrypt_data


def test_encrypt_decrypt_roundtrip():
    original = b"Hello, SuperSync!"
    password = "test-password-123"

    encrypted = encrypt_data(original, password)
    assert isinstance(encrypted, bytes)
    assert encrypted != original
    assert encrypted[:4] == b"SSNC"

    decrypted = decrypt_data(encrypted, password)
    assert decrypted == original


def test_decrypt_with_wrong_password_fails():
    original = b"Secret data"
    password = "correct-password"

    encrypted = encrypt_data(original, password)

    import pytest
    with pytest.raises(Exception):
        decrypt_data(encrypted, "wrong-password")


def test_encrypted_file_format():
    original = b"Test data"
    password = "password123"

    encrypted = encrypt_data(original, password)

    assert encrypted[0:4] == b"SSNC"
    version = int.from_bytes(encrypted[4:6], "big")
    assert version == 1
