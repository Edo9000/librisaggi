import json
import os

class PriceCache:
    def __init__(self, path="price_cache.json"):
        self.path = path
        self.cache = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"⚠️ Errore nel caricamento della cache: {e}")
                self.cache = {}

    def get(self, isbn, source):
        return self.cache.get(f"{isbn}_{source}")

    def set(self, isbn, source, value):
        self.cache[f"{isbn}_{source}"] = value
        self.save()

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Errore nel salvataggio della cache: {e}")
