from collections import OrderedDict
import time

class VerificationCache:
    """
    A simple LRU Cache for verification results.
    Prevents re-verifying the same claim against the same evidence.
    """
    def __init__(self, capacity: int = 1000, ttl_seconds: int = 3600):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()

    def get(self, key: str):
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time.time() - entry['timestamp'] > self.ttl_seconds:
            del self.cache[key]
            return None
        
        # Move to end (LRU)
        self.cache.move_to_end(key)
        return entry['value']

    def set(self, key: str, value: any):
        if key in self.cache:
            self.cache.move_to_end(key)
        
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
        
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
