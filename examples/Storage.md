### Example 1: Basic Usage for Setting and Retrieving Values
This simple example demonstrates how to create a key-value pair and then retrieve it. This could be used for storing settings or session data.

```
# Initialize the KeyValueStorage with a label
kv_storage = KeyValueStorage("settings", "cache")

# Create a new key-value pair
kv_storage.create("theme", "dark")

# Retrieve the value of a key
theme = kv_storage.read("theme")
print(f"The current theme is: {theme}")
```

### Example 2: Updating and Deleting Entries
Here's how you might update an existing entry and delete another. This is useful in scenarios where settings or user preferences need to be updated or removed.

```
# Initialize the KeyValueStorage with a label
kv_storage = KeyValueStorage("user_preferences", "cache")

# Update an existing entry
kv_storage.create("notification", "enabled")
kv_storage.update("notification", "disabled")

# Check the updated value
notification_status = kv_storage.read("notification")
print(f"Notification setting is now: {notification_status}")

# Delete an entry
kv_storage.delete("notification")
print("Notification setting removed.")
```

### Example 3: Handling Expiration of Entries
This example shows how to set entries with an expiration time. This is particularly useful for temporary data like cache or session tokens.

```
# Initialize the KeyValueStorage for cache purposes
kv_storage = KeyValueStorage("cache", "cache")

# Create a cache entry that expires in 300 seconds (5 minutes)
kv_storage.create("session_token", "abc123", seconds=300)

# Attempt to retrieve the entry after some time
import time
time.sleep(350)  # Sleep for longer than the expiration time
session_token = kv_storage.read("session_token")
if session_token is None:
    print("Session token has expired.")
else:
    print(f"Session token is still valid: {session_token}")
```

### Example 4: Incrementing a Counter
This scenario might be used for visit counters on a website or in applications where you need to keep a running count of events.

```
# Initialize the KeyValueStorage for counting
kv_storage = KeyValueStorage("counters", "cache")

# Increment a counter for page visits
kv_storage.increment("page_visits")
kv_storage.increment("page_visits")

# Retrieve and display the current count
page_visits = kv_storage.read("page_visits")
print(f"Total page visits: {page_visits}")
```

### Example 5: Starting and Utilizing the Periodic Cleanup Thread
This example shows how to start the cleanup thread which will periodically clean up expired entries. It’s useful for maintaining a clean and efficient storage system.

```
# Initialize the KeyValueStorage for a session store that needs regular cleanup
kv_storage = KeyValueStorage("session_store", "cache")

# Start the periodic cleanup thread
kv_storage.start_cleanup_thread()

# Assuming the application runs and creates sessions with expirations...

# Before shutting down the application:
kv_storage.shutdown()  # Properly stop the cleanup thread and close the database
```