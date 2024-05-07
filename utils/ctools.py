import os
import time
from getpass import getuser

import jsonpickle
import hashlib
from functools import wraps

from utils.crypto import CryptoManager


class CacheManager:
    def __init__(self, cache_file):
        self.cache_file = cache_file
        # Ensure the cache file exists and initialize it if not
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, 'w') as file:
                file.write(jsonpickle.encode({}))

    def cache_results(self, func=None, *, expire_in_seconds=None, encrypt=False):
        if func is None:
            return lambda f: self.cache_results(f, expire_in_seconds=expire_in_seconds, encrypt=encrypt)

        @wraps(func)
        def wrapper(*args, **kwargs):
            args_key = jsonpickle.encode(args)
            kwargs_key = jsonpickle.encode(kwargs)
            unique_key = hashlib.sha256(
                f"{func.__module__}.{func.__name__}_{args_key}_{kwargs_key}".encode()).hexdigest()

            with open(self.cache_file, 'r') as file:
                cache = jsonpickle.decode(file.read())

            if unique_key in cache:
                entry = cache[unique_key]
                if encrypt:
                    crypto_manager = CryptoManager(getuser())
                    entry = crypto_manager.decrypt_message(entry)
                    entry = jsonpickle.decode(entry)

                if expire_in_seconds is None or (time.time() - entry['time'] < expire_in_seconds):
                    return entry['result']

            result = func(*args, **kwargs)
            entry = {'result': result, 'time': time.time()}
            if encrypt:
                crypto_manager = CryptoManager(getuser())
                entry = jsonpickle.encode(entry)
                entry = crypto_manager.encrypt_message(entry)

            cache[unique_key] = entry

            with open(self.cache_file, 'w') as file:
                file.write(jsonpickle.encode(cache))

            return result

        return wrapper


# Example of using the class with expiration
if __name__ == "__main__":
    cache_manager = CacheManager('./cache.json')


    class Sample:
        @cache_manager.cache_results(expire_in_seconds=30, encrypt=True)
        def calculate_sum(self, x, y):
            return x + y


    x = Sample()
    # This will calculate and cache the result
    print(x.calculate_sum(1, 2))
    # This will fetch the result from cache if within 30 seconds
    print(x.calculate_sum(1, 2))
