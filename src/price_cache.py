import json
import os

class PriceCache:
    def __init__(self, path="price_cache.json"):
        self.path = path
        self.cache = {}
        print(f"📂 Cache: uso file '{self.path}'")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
                print(f"✅ Cache caricata ({len(self.cache)} elementi)")
            except Exception as e:
                print(f"⚠️ Errore nel caricamento della cache: {e}")
                self.cache = {}
        else:
            print("ℹ️ File cache non esistente, sarà creato al primo salvataggio.")

    def get(self, isbn, source):
        key = f"{isbn}_{source}"
        val = self.cache.get(key)
        if val is not None:
            print(f"🔎 [CACHE] Hit: {key} = {val}")
        return val

    def set(self, isbn, source, value):
        key = f"{isbn}_{source}"
        self.cache[key] = value
        print(f"📥 [CACHE] Set: {key} = {value}")
        self.save()

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True) if os.path.dirname(self.path) else None
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            print(f"💾 Cache salvata in '{self.path}' ({len(self.cache)} elementi).")
        except Exception as e:
            print(f"❌ Errore nel salvataggio della cache: {e}")
