import time
import unittest
import os
import json
from unittest.mock import patch

from utils.ctools import CacheManager


class ComplexData:
    # A simple custom class to test caching of object instances
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        # This is required for unittest to assert equality of two instances
        return self.value == other.value


class TestCacheManager(unittest.TestCase):
    def setUp(self):
        # Setup a temporary cache file for each test
        self.cache_file = 'test_cache.json'
        self.cache_manager = CacheManager(self.cache_file)

    def tearDown(self):
        # Remove the temporary cache file after each test
        os.remove(self.cache_file)

    def test_function_with_list(self):
        @self.cache_manager.cache_results()
        def process_list(data):
            return [x * 2 for x in data]

        result = process_list([1, 2, 3])
        self.assertEqual(result, [2, 4, 6])
        cached_result = process_list([1, 2, 3])
        self.assertEqual(cached_result, [2, 4, 6])

    def test_function_with_dict(self):
        @self.cache_manager.cache_results()
        def process_dict(data):
            return {k: v * 2 for k, v in data.items()}

        result = process_dict({'a': 1, 'b': 2})
        self.assertEqual(result, {'a': 2, 'b': 4})
        cached_result = process_dict({'a': 1, 'b': 2})
        self.assertEqual(cached_result, {'a': 2, 'b': 4})

    def test_function_with_custom_object(self):
        @self.cache_manager.cache_results()
        def modify_object(obj):
            return ComplexData(obj.value + 10)

        obj = ComplexData(5)
        result = modify_object(obj)
        self.assertEqual(result, ComplexData(15))
        cached_result = modify_object(obj)
        self.assertEqual(cached_result, ComplexData(15))

    def test_function_with_mixed_types(self):
        @self.cache_manager.cache_results()
        def mixed_inputs(a, b, c):
            return a * 2, b['key'] * 3, [x + 3 for x in c]

        result = mixed_inputs(5, {'key': 2}, [1, 2])
        self.assertEqual(result, (10, 6, [4, 5]))
        cached_result = mixed_inputs(5, {'key': 2}, [1, 2])
        self.assertEqual(cached_result, (10, 6, [4, 5]))

    def test_function_caching(self):
        # Test that function results are cached
        @self.cache_manager.cache_results()
        def test_func(x):
            return x * x

        # First call, should compute the result
        result = test_func(3)
        self.assertEqual(result, 9)

        # Modify the function to see if it still returns the cached result
        @self.cache_manager.cache_results()
        def test_func(x):
            return x * x * x

        # Second call, should retrieve the result from cache, not compute new one
        cached_result = test_func(3)
        self.assertEqual(cached_result, 9)

    def test_cache_collision(self):
        # Ensure that different functions or arguments don't collide in the cache
        @self.cache_manager.cache_results()
        def square(x):
            return x * x

        @self.cache_manager.cache_results()
        def cube(x):
            return x * x * x

        result_square = square(3)
        result_cube = cube(3)
        self.assertNotEqual(result_square, result_cube)

    def test_cache_persistence(self):
        # Test that results are correctly written to and read from the file
        @self.cache_manager.cache_results()
        def add(x, y):
            return x + y

        # Call with first set of parameters and write to cache
        result = add(1, 2)
        self.assertEqual(result, 3)

        # Create a new cache manager with the same file to simulate a new program run
        new_cache_manager = CacheManager(self.cache_file)

        @new_cache_manager.cache_results()
        def add(x, y):
            return x + y

        # Call with the same parameters should retrieve the cached result
        cached_result = add(1, 2)
        self.assertEqual(cached_result, 3)

    def test_cache_with_ttl(self):
        # Adding a counter to monitor the number of function executions
        self.execution_count = 0

        @self.cache_manager.cache_results(expire_in_seconds=2)
        def compute(x):
            self.execution_count += 1
            return x * x

        # First call to compute and cache the result
        compute(3)
        self.assertEqual(self.execution_count, 1)  # Function should be called once

        # Sleep for a time less than the TTL and check if the result is from cache
        time.sleep(1)
        compute(3)
        self.assertEqual(self.execution_count, 1)  # Function should not be called again, cache is used

        # Sleep to ensure the TTL has expired
        time.sleep(2)
        compute(3)
        self.assertEqual(self.execution_count, 2)

    def test_encryption(self):
        @self.cache_manager.cache_results(encrypt=True)
        def sensitive_data_function(x):
            return {"secret": x * 10}

        # Test storing and retrieving encrypted data
        result = sensitive_data_function(5)
        self.assertEqual(result, {"secret": 50})

        # Ensure the data in the file is not in plain text
        with open(self.cache_file, 'r') as file:
            cache_content = file.read()
            self.assertNotIn('secret', cache_content)
            self.assertNotIn('50', cache_content)

        # Ensure that decrypting the cache retrieves the correct data
        cached_result = sensitive_data_function(5)  # This should fetch from cache
        self.assertEqual(cached_result, {"secret": 50})

    def test_cache_with_ttl_and_encryption(self):
        # Adding a counter to monitor the number of function executions
        self.execution_count = 0

        @self.cache_manager.cache_results(expire_in_seconds=2, encrypt=True)
        def compute(x):
            self.execution_count += 1
            return x * x

        # First call to compute and cache the result
        compute(3)
        self.assertEqual(self.execution_count, 1)  # Function should be called once

        # Sleep for a time less than the TTL and check if the result is from cache
        time.sleep(1)
        compute(3)
        self.assertEqual(self.execution_count, 1)  # Function should not be called again, cache is used

        # Sleep to ensure the TTL has expired
        time.sleep(2)
        compute(3)
        self.assertEqual(self.execution_count, 2)

    def test_cached_class_method(self):
        class TestClass:
            def __init__(self, identifier):
                self.id = identifier

            @self.cache_manager.cache_results(encrypt=False)
            def compute(self, x):
                return x + self.id

        obj1 = TestClass(10)
        obj2 = TestClass(20)

        # First object tests
        self.assertEqual(obj1.compute(5), 15)
        self.assertEqual(obj1.compute(5), 15)  # Should fetch from cache

        # Second object tests
        self.assertEqual(obj2.compute(5), 25)
        self.assertEqual(obj2.compute(5), 25)  # Should fetch from cache

        obj2 = TestClass(20)
        self.assertEqual(obj2.compute(5), 25)
        self.assertEqual(obj2.compute(5), 25)  # Should fetch from cache

if __name__ == '__main__':
    unittest.main()
