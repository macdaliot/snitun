"""Encrypt or Decrypt multiplexer transport data."""

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ..exceptions import MultiplexerTransportDecrypto


class CryptoTransport:
    """Encrypt/Decrypt Transport flow."""

    def __init__(self, key: bytes, iv: bytes):
        """Initialize crypto data."""
        self._cipher = Cipher(
            algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        self._encryptor = self._cipher.encryptor()
        self._decryptor = self._cipher.decryptor()

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data from transport."""
        return self._encryptor.update(data)

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt data from transport."""
        try:
            return self._decryptor.update(data)
        except cryptography.exceptions.InvalidTag:
            raise MultiplexerTransportDecrypto() from None