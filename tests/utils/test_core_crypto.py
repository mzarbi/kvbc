import os
import unittest
from unittest.mock import patch, MagicMock
import base64

from utils.crypto import CryptoManager


class TestCryptoManager(unittest.TestCase):

    def setUp(self):
        self.crypto_manager = CryptoManager(username="testuser")
        self.test_key = os.urandom(32)
        self.encoded_key = base64.urlsafe_b64encode(self.test_key).decode()

    @patch('os.urandom')
    def test_generate_key(self, mock_urandom):
        mock_urandom.return_value = self.test_key
        key = CryptoManager.generate_key()
        self.assertEqual(key, self.test_key)
        mock_urandom.assert_called_once_with(32)

    @patch('keyring.set_password')
    def test_store_key(self, mock_set_password):
        CryptoManager.store_key("testuser", self.test_key)
        mock_set_password.assert_called_once_with(CryptoManager.SERVICE_NAME, "testuser", self.encoded_key)

    @patch('keyring.get_password')
    @patch('keyring.set_password')
    def test_retrieve_key_key_exists(self, mock_set_password, mock_get_password):
        mock_get_password.return_value = self.encoded_key
        key = CryptoManager.retrieve_key("testuser")
        self.assertEqual(key, self.test_key)
        mock_get_password.assert_called_once_with(CryptoManager.SERVICE_NAME, "testuser")
        mock_set_password.assert_not_called()

    @patch('keyring.get_password')
    @patch('keyring.set_password')
    @patch('os.urandom')
    def test_retrieve_key_no_key_found(self, mock_urandom, mock_set_password, mock_get_password):
        mock_get_password.return_value = None
        mock_urandom.return_value = self.test_key
        key = CryptoManager.retrieve_key("testuser")
        self.assertEqual(key, self.test_key)
        mock_set_password.assert_called_once_with(CryptoManager.SERVICE_NAME, "testuser", self.encoded_key)
        mock_get_password.assert_called_once_with(CryptoManager.SERVICE_NAME, "testuser")

    @patch('os.urandom')
    def test_encrypt_decrypt_message(self, mock_urandom):
        mock_urandom.side_effect = [self.test_key[:16], self.test_key[:16]]  # IV for both encrypt and decrypt
        CryptoManager.store_key("testuser", self.test_key)
        message = "Hello, secure world!"
        encrypted_message = self.crypto_manager.encrypt_message(message)
        decrypted_message = self.crypto_manager.decrypt_message(encrypted_message)
        self.assertEqual(decrypted_message, message)

if __name__ == '__main__':
    unittest.main()
