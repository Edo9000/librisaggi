import json
import os

class FailureCache:
    def __init__(self, path="failed_isbn.json"):
        self.path = path
        self.failed_isbn = self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return set(json.load(f))
        return set()

    def add(self, isbn):
        self.failed_isbn.add(isbn)
        self.save()

    def remove(self, isbn):
        self.failed_isbn.discard(isbn)
        self.save()

    def get_all(self):
        return list(self.failed_isbn)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(list(self.failed_isbn), f, indent=2)

    def clear(self):
        self.failed_isbn.clear()
        self.save()
