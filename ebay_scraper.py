import requests
from bs4 import BeautifulSoup
import time
import random

def get_random_proxy(self):
        try:
            with open("working_proxies.txt", "r") as f:
                proxies = [line.strip() for line in f if line.strip()]
            proxy = random.choice(proxies)
            return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        except Exception as e:
            print(f"⚠️ Errore caricamento proxy: {e}")
            return None
def cache_failed_isbn(self, isbn, filename="isbn_failed.txt"):
        with open(filename, "a") as f:
            f.write(str(isbn) + "\n")    
        
        
class EbayScraper:
    def __init__(self, max_retries=2, retry_delay=1, timeout=15):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}

    def get_price(self, isbn):
        url = f"https://www.ebay.it/sch/i.html?_nkw={isbn}"
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [eBay] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
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
                    print(f"✅ [eBay] Prezzo trovato per ISBN {isbn}: {min_price}")
                    return min_price
                else:
                    print(f"⚠️ [eBay] Nessun prezzo trovato per ISBN {isbn}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"❌ [eBay] Errore richiesta per ISBN {isbn} (tentativo {attempt}): {e}")
                if attempt < self.max_retries:
                    print(f"⏳ [eBay] Attendo {self.retry_delay} secondi prima del prossimo tentativo per ISBN {isbn}...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ [eBay] Errore definitivo dopo {self.max_retries} tentativi per ISBN {isbn}")
                    return None