import requests
from bs4 import BeautifulSoup
import time
import json
import os
from proxy_manager import ProxyManager
from failure_cache import FailureCache


class EbayScraper:
    def __init__(self, max_retries=2, retry_delay=1, timeout=10, cache_file="ebay_cache.json"):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }
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
            print(f"📦 [eBay] Cache hit per ISBN {isbn}")
            return self.cache[isbn]

        url = f"https://www.ebay.it/sch/i.html?_nkw={isbn}"
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [eBay] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
                proxy = self.proxy_manager.get_random_proxy()
                proxies = {"http": proxy, "https": proxy} if proxy else None
                try:
                    r = requests.get(url, headers=self.headers, proxies=proxies, timeout=self.timeout)
                except Exception:
                    print("⚠️ [eBay] Proxy fallito, riprovo senza...")
                    r = requests.get(url, headers=self.headers, timeout=self.timeout)

                soup = BeautifulSoup(r.text, "html.parser")
                prices = []
                for tag in soup.select(".s-item__price"):
                    text = tag.get_text().replace("EUR", "").replace(",", ".").strip()
                    try:
                        price = float(text.split()[0])
                        prices.append(price)
                    except ValueError:
                        continue
                if prices:
                    min_price = min(prices)
                    self.cache[isbn] = min_price
                    self.save_cache()
                    print(f"✅ [eBay] Prezzo trovato per ISBN {isbn}: {min_price}")
                    return min_price
                else:
                    print(f"⚠️ [eBay] Nessun prezzo trovato per ISBN {isbn}")
                    self.cache[isbn] = None
                    self.save_cache()
                    return None
            except requests.exceptions.RequestException as e:
                print(f"❌ [eBay] Errore richiesta per ISBN {isbn} (tentativo {attempt}): {e}")
                if attempt < self.max_retries:
                    print(f"⏳ [eBay] Attendo {self.retry_delay} secondi prima del prossimo tentativo...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"🟥 [eBay] ISBN {isbn} aggiunto alla lista dei falliti.")
                    self.cache[isbn] = None
                    self.save_cache()
                    self.failure_cache.add(isbn)
                    return None
