import Pyro5.api

from core.storage import Storage


class KeyValueServer:
    def __init__(self, label, cache_path):
        self.kv_storage = Storage(label, cache_path)

    def create(self, key, value, seconds=None):
        return self.kv_storage.create(key, value, seconds)

    def read(self, key):
        return self.kv_storage.read(key)

    def update(self, key, new_value, days=None):
        return self.kv_storage.update(key, new_value, days)

    def delete(self, key):
        return self.kv_storage.delete(key)

    def increment(self, key, amount=1):
        return self.kv_storage.increment(key, amount)

    def keys(self, pattern):
        return self.kv_storage.keys(pattern)

    def start_cleanup(self):
        self.kv_storage.start_cleanup_thread()

    def shutdown(self):
        self.kv_storage.shutdown()