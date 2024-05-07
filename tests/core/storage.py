import time
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os

from core.storage import Storage


class TestStorage(unittest.TestCase):
    def setUp(self):
        # Create a temporary database path for testing
        self.storage = Storage("test_storage", "cache")

    def test_create(self):
        """Test creating a new key-value pair."""
        success = self.storage.create("test_key", "test_value")
        self.assertTrue(success)
        # Verify that the value can be retrieved
        value = self.storage.read("test_key")
        self.assertEqual(value, "test_value")

    def test_read_non_existent(self):
        """Test reading a non-existent key."""
        result = self.storage.read("non_existent_key")
        self.assertIsNone(result)

    def test_update_existing_key(self):
        """Test updating an existing key."""
        self.storage.create("test_key", "old_value")
        success = self.storage.update("test_key", "new_value")
        self.assertTrue(success)
        # Check the new value
        value = self.storage.read("test_key")
        self.assertEqual(value, "new_value")

    def test_delete_existing_key(self):
        """Test deleting an existing key."""
        self.storage.create("test_key", "test_value")
        success = self.storage.delete("test_key")
        self.assertTrue(success)
        # Verify deletion
        result = self.storage.read("test_key")
        self.assertIsNone(result)

    def test_increment_non_existent_key(self):
        """Test incrementing a non-existent key."""
        result = self.storage.increment("increment_key")
        self.assertEqual(result, 1)

    def test_cleanup_expired_entries(self):
        """Test the cleanup of expired entries."""
        self.storage.create("temp_key", "temp_value", seconds=1)
        # Wait for expiration
        time.sleep(1.1)
        # Cleanup manually triggered for testing purposes
        removed_count = self.storage.cleanup_expired_entries()
        self.assertGreater(removed_count, 0)
        # Verify cleanup
        result = self.storage.read("temp_key")
        self.assertIsNone(result)

    @patch('threading.Thread')
    def test_periodic_cleanup_thread_starts(self, mock_thread):
        """Test if the cleanup thread starts correctly."""
        self.storage.start_cleanup_thread()
        mock_thread.assert_called_once()

    def tearDown(self):
        # Clean up any files or resources if necessary
        self.storage.shutdown()
        os.remove(self.storage.db_path)
        lock_path = f"{self.storage.db_path}.lock"
        if os.path.exists(lock_path):
            os.remove(lock_path)

if __name__ == '__main__':
    unittest.main()
