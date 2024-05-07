import os
import threading
import time
from contextlib import contextmanager

from filelock import FileLock, Timeout
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
from core.config import logger


@contextmanager
def locked_db(db, lock):
    try:
        lock.acquire()
        yield db
    finally:
        lock.release()


class PeriodicExecutor:
    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.stop_event = threading.Event()

    def is_alive(self):
        return self.thread.is_alive()

    def start(self):
        self.thread.start()

    def run(self):
        next_run_time = time.time()
        while not self.stop_event.is_set():
            time.sleep(max(0, next_run_time - time.time()))  # Sleep only the necessary time
            if self.stop_event.is_set():  # Check again before proceeding
                break
            try:
                self.function(*self.args, **self.kwargs)
            except Exception as e:
                logger.error(f"Error during periodic execution: {e}")
            next_run_time += self.interval

    def stop(self):
        self.stop_event.set()
        self.thread.join()


class Storage:
    def __init__(self, label: str, cache_path: str):
        try:
            self.label = label
            self.db_path = os.path.join(cache_path, 'STORES', f"{label}.db")
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.db = TinyDB(self.db_path)
            self.db_lock = FileLock(f"{self.db_path}.lock", timeout=int(os.getenv('DB_LOCK_TIMEOUT', 10)))
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise RuntimeError(f"Failed to initialize KeyValueStore: {e}")

    def start_cleanup_thread(self):
        self.cleanup_thread = PeriodicExecutor(3600, self.cleanup_expired_entries)  # every hour
        self.cleanup_thread.start()

    def create(self, key: str, value: any, seconds: int = None) -> bool:
        try:
            with locked_db(self.db, self.db_lock):
                record = {'key': key, 'value': value}
                if seconds is not None:
                    expiration_date = datetime.now() + timedelta(seconds=seconds)
                    record['expiration'] = expiration_date.timestamp()
                self.db.insert(record)
                return True
        except Timeout as e:
            logger.error(f"Timeout acquiring database lock: {e}")
        except Exception as e:
            logger.error(f"Failed to create entry: {e}")
        return False

    def read(self, key: str):
        try:
            with locked_db(self.db, self.db_lock):
                Entry = Query()
                result = self.db.search(Entry.key == key)
                if result:
                    entry = result[0]
                    if 'expiration' in entry and datetime.now().timestamp() > entry['expiration']:
                        self.db.remove(Entry.key == key)
                        return None
                    return entry['value']
        except Timeout as e:
            logger.error(f"Timeout acquiring database lock: {e}")
        except Exception as e:
            logger.error(f"Failed to read entry: {e}")
        return None

    def update(self, key: str, new_value: any, days: int = None) -> bool:
        try:
            with locked_db(self.db, self.db_lock):
                Entry = Query()
                update_data = {'value': new_value}
                if days is not None:
                    expiration_date = datetime.now() + timedelta(days=days)
                    update_data['expiration'] = expiration_date.timestamp()
                updated_count = self.db.update(update_data, Entry.key == key)[0]
                return updated_count > 0
        except Timeout as e:
            logger.error(f"Timeout acquiring database lock: {e}")
        except Exception as e:
            logger.error(f"Failed to update entry: {e}")
        return False

    def delete(self, key: str) -> bool:
        try:
            with locked_db(self.db, self.db_lock):
                Entry = Query()
                deleted_count = self.db.remove(Entry.key == key)[0]
                return deleted_count > 0
        except Timeout as e:
            logger.error(f"Timeout acquiring database lock: {e}")
        except Exception as e:
            logger.error(f"Failed to delete entry: {e}")
        return False

    def increment(self, key: str, amount: int = 1) -> int:
        try:
            with locked_db(self.db, self.db_lock):
                Entry = Query()
                result = self.db.search(Entry.key == key)
                if result:
                    new_count = result[0]['value'] + amount
                    self.db.update({'value': new_count}, Entry.key == key)
                    return new_count
                else:
                    # If the key does not exist, create it with the amount
                    self.create(key, amount)  # Ensure this call is inside try-except as well
                    return amount
        except Timeout as e:
            logger.error(f"Timeout acquiring database lock: {e}")
        except Exception as e:
            logger.error(f"Failed to increment value: {e}")
        return amount

    def keys(self, pattern: str):
        try:
            with locked_db(self.db, self.db_lock):
                import fnmatch
                all_keys = [item['key'] for item in self.db.all()]
                return fnmatch.filter(all_keys, pattern)
        except Timeout as e:
            logger.error(f"Timeout acquiring database lock: {e}")
        except Exception as e:
            logger.error(f"Failed to retrieve keys: {e}")
        return []

    def cleanup_expired_entries(self):
        try:
            with locked_db(self.db, self.db_lock):
                now = datetime.now().timestamp()
                Entry = Query()
                removed_count = self.db.remove(Entry.expiration.test(lambda x: x < now))
                logger.info(f"Cleaned up {removed_count} expired entries.")
                return removed_count[0]
        except Timeout as e:
            logger.error(f"Timeout acquiring database lock: {e}")
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")
        return 0

    def shutdown(self):
        logger.info("Shutdown signal received")
        if getattr(self, 'cleanup_thread', None):
            if self.cleanup_thread.is_alive():
                self.cleanup_thread.stop()
        self.db.close()


class NASPathStorage(Storage):
    def __init__(self, label, cache_path):
        super().__init__(label, cache_path)

    def store_path(self, label, env, os, path):
        key = self._generate_key(label, env, os)
        self.create(key, path)

    def read_path(self, label, env, os):
        key = self._generate_key(label, env, os)
        return self.read(key)

    def update_path(self, label, env, os, new_path):
        key = self._generate_key(label, env, os)
        self.update(key, new_path)

    def delete_path(self, label, env, os):
        key = self._generate_key(label, env, os)
        self.delete(key)

    def list_all_paths(self, label=None, env=None, os=None):
        pattern = self._generate_pattern(label, env, os)
        keys = self.keys(pattern)
        return {key: self.read(key) for key in keys}

    def path_exists(self, label, env, os):
        key = self._generate_key(label, env, os)
        return self.read(key) is not None

    def _generate_key(self, label, env, os):
        return f"{label}_{env}_{os}"

    def _generate_pattern(self, label, env, os):
        return f"{label or '*'}_{env or '*'}_{os or '*'}"
