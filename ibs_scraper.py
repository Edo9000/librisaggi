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

class IBSScraper:
    def __init__(self, max_retries=2, retry_delay=1, timeout=10):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}           

    def get_price(self, isbn):
        url = f"https://www.ibs.it/search/?ts=as&query={isbn}"
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [IBS] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
                r = requests.get(url, headers=self.headers, timeout=self.timeout)
                soup = BeautifulSoup(r.text, "html.parser")
                price_tags = soup.select(".cc-price")
                if len(price_tags) >= 30:
                    selected = price_tags[29]
                    text = selected.get_text().replace("€", "").replace(",", ".").strip()
                    print(f"✅ [IBS] Prezzo trovato per ISBN {isbn}: {text}")
                    return float(text)
                else:
                    print(f"⚠️ [IBS] Nessun prezzo trovato per ISBN {isbn}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"❌ [IBS] Errore richiesta per ISBN {isbn} (tentativo {attempt}): {e}")
                if attempt < self.max_retries:
                    print(f"⏳ [IBS] Attendo {self.retry_delay} secondi prima del prossimo tentativo per ISBN {isbn}...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ [IBS] Errore definitivo dopo {self.max_retries} tentativi per ISBN {isbn}")
                    return None