import os
import base64
import keyring
import logging
from getpass import getuser
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO)

class CryptoManager:
    SERVICE_NAME = 'SAMPLE'  # Static service name

    @staticmethod
    def generate_key() -> bytes:
        """Generate a random 256-bit key."""
        return os.urandom(32)  # 32 bytes * 8 bits/byte = 256 bits

    @classmethod
    def store_key(cls, username: str, key: bytes):
        """Store the key in the system keyring."""
        encoded_key = base64.urlsafe_b64encode(key).decode()  # Encode key in a URL-safe base64 format
        try:
            keyring.set_password(cls.SERVICE_NAME, username, encoded_key)
        except keyring.errors.KeyringError as e:
            logging.error(f"Failed to store key in keyring: {e}")
            raise

    @classmethod
    def retrieve_key(cls, username: str) -> bytes:
        """Retrieve the key from the system keyring and decode it."""
        try:
            encoded_key = keyring.get_password(cls.SERVICE_NAME, username)
            if encoded_key is None:
                # Key not found, generate a new one, store it, and return it
                new_key = cls.generate_key()
                cls.store_key(username, new_key)
                return new_key
            return base64.urlsafe_b64decode(encoded_key)
        except Exception as e:
            logging.error(f"Failed to retrieve or generate key: {e}")
            raise

    def __init__(self, username=None):
        self.username = username or getuser()

    def encrypt_message(self, message: str) -> bytes:
        """Encrypt a message using AES."""
        key = self.retrieve_key(self.username)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(message.encode()) + encryptor.finalize()
        return iv + encrypted  # Prepend IV for use in decryption

    def decrypt_message(self, encrypted: bytes) -> str:
        """Decrypt a message using AES."""
        key = self.retrieve_key(self.username)
        iv, encrypted_msg = encrypted[:16], encrypted[16:]
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return (decryptor.update(encrypted_msg) + decryptor.finalize()).decode()

if __name__ == '__main__':
    crypto_manager = CryptoManager()

    # Demonstrate encryption and decryption
    message = "Hello, secure world!"
    encrypted_message = crypto_manager.encrypt_message(message)
    logging.info(f"Encrypted message: {encrypted_message}")

    decrypted_message = crypto_manager.decrypt_message(encrypted_message)
    logging.info(f"Decrypted message: {decrypted_message}")