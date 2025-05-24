import random
import os

class ProxyManager:
    def __init__(self, proxy_file="working_proxies.txt"):
        self.proxy_file = proxy_file
        self.proxies = self.load_proxies()

    def load_proxies(self):
        if not os.path.exists(self.proxy_file):
            print("⚠️ Nessun file di proxy trovato, procederò senza proxy.")
            return []
        with open(self.proxy_file, "r", encoding="utf-8") as f:
            proxies = [line.strip() for line in f if line.strip()]
            print(f"📦 Caricati {len(proxies)} proxy")
            return proxies

    def get_random_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)
