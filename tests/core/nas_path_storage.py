import unittest
import os
from datetime import datetime, timedelta

from core.storage import NASPathStorage


class TestNASPathStorage(unittest.TestCase):
    def setUp(self):
        # Define paths and initialize the storage class
        self.cache_path = 'test_cache'
        self.label = 'test_nas_storage'
        self.nas_storage = NASPathStorage(self.label, self.cache_path)

    def test_store_and_read_path(self):
        """Test storing and then reading a NAS path."""
        self.nas_storage.store_path("backup_nas", "dev", "linux", "/mnt/dev_backups")
        path = self.nas_storage.read_path("backup_nas", "dev", "linux")
        self.assertEqual(path, "/mnt/dev_backups")

    def test_update_path(self):
        """Test updating an existing NAS path."""
        self.nas_storage.store_path("backup_nas", "dev", "linux", "/mnt/dev_backups")
        self.nas_storage.update_path("backup_nas", "dev", "linux", "/mnt/updated_dev_backups")
        updated_path = self.nas_storage.read_path("backup_nas", "dev", "linux")
        self.assertEqual(updated_path, "/mnt/updated_dev_backups")

    def test_delete_path(self):
        """Test deleting an existing NAS path."""
        self.nas_storage.store_path("backup_nas", "dev", "linux", "/mnt/dev_backups")
        self.nas_storage.delete_path("backup_nas", "dev", "linux")
        path = self.nas_storage.read_path("backup_nas", "dev", "linux")
        self.assertIsNone(path)

    def test_list_all_paths(self):
        """Test listing all stored NAS paths."""
        self.nas_storage.store_path("backup_nas", "dev", "linux", "/mnt/dev_backups")
        self.nas_storage.store_path("backup_nas", "dev", "windows", "C:\\dev_backups")
        all_paths = self.nas_storage.list_all_paths("backup_nas", "dev")
        self.assertIn("backup_nas_dev_linux", all_paths)
        self.assertIn("backup_nas_dev_windows", all_paths)

    def test_path_exists(self):
        """Test checking if a specific path exists."""
        self.nas_storage.store_path("backup_nas", "dev", "linux", "/mnt/dev_backups")
        exists = self.nas_storage.path_exists("backup_nas", "dev", "linux")
        self.assertTrue(exists)

    def tearDown(self):
        self.nas_storage.shutdown()
        os.remove(self.nas_storage.db_path)
        lock_path = f"{self.nas_storage.db_path}.lock"
        if os.path.exists(lock_path):
            os.remove(lock_path)

if __name__ == '__main__':
    unittest.main()
