import requests
from bs4 import BeautifulSoup
import time
import json
import os
from proxy_manager import ProxyManager
from failure_cache import FailureCache

class IBSScraper:
    def __init__(self, max_retries=2, retry_delay=1, timeout=10, cache_file="ibs_cache.json"):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.cache_file = cache_file
        self.cache = self.load_cache()
        self.proxy_manager = ProxyManager()
        self.failure_cache = FailureCache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_cache(self):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f)

    def get_price(self, isbn):
        if isbn in self.cache:
            print(f"📦 [IBS] Cache hit per ISBN {isbn}")
            return self.cache[isbn]

        url = f"https://www.ibs.it/search/?ts=as&query={isbn}"
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [IBS] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
                proxy = self.proxy_manager.get_random_proxy()
                proxies = {"http": proxy, "https": proxy} if proxy else None
                try:
                    r = requests.get(url, headers=self.headers, proxies=proxies, timeout=self.timeout)
                except Exception:
                    print("⚠️ [IBS] Proxy fallito, riprovo senza...")
                    r = requests.get(url, headers=self.headers, timeout=self.timeout)

                soup = BeautifulSoup(r.text, "html.parser")
                price_tags = soup.select(".cc-price")
                if len(price_tags) >= 30:
                    selected = price_tags[29]
                    text = selected.get_text().replace("€", "").replace(",", ".").strip()
                    price = float(text)
                    self.cache[isbn] = price
                    self.save_cache()
                    print(f"✅ [IBS] Prezzo trovato per ISBN {isbn}: {price}")
                    return price
                else:
                    print(f"⚠️ [IBS] Nessun prezzo trovato per ISBN {isbn}")
                    self.cache[isbn] = None
                    self.save_cache()
                    return None
            except requests.exceptions.RequestException as e:
                print(f"❌ [IBS] Errore richiesta per ISBN {isbn} (tentativo {attempt}): {e}")
                if attempt < self.max_retries:
                    print(f"⏳ [IBS] Attendo {self.retry_delay} secondi prima del prossimo tentativo...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"🟥 [IBS] ISBN {isbn} aggiunto alla lista dei falliti.")
                    self.cache[isbn] = None
                    self.save_cache()
                    self.failure_cache.add(isbn)
                    return None
