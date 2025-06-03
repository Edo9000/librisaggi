import time
from bs4 import BeautifulSoup
from scraper_api_client import ScraperAPIClient

class EbayScraper:
    def __init__(self, max_retries=2, retry_delay=1, timeout=10, api_key=None, price_cache=None):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.api_key = api_key or "172215073eaeac24a47020e044760bf5"
        self.client = ScraperAPIClient(api_key=self.api_key, country_code="it")
        self.cache = price_cache

    def get_price(self, isbn):
        if self.cache:
            cached_price = self.cache.get(isbn, "eBay")
            if cached_price is not None:
                print(f"💾 Prezzo trovato nella cache per ISBN {isbn}: {cached_price} €")
                return cached_price
        
        url = f"https://www.ebay.it/sch/i.html?_nkw={isbn}"
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [eBay] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
                html = self.client.get(url)
                if html is None:
                    raise Exception("Risposta vuota da ScraperAPI")

                soup = BeautifulSoup(html, "html.parser")
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
                    if self.cache:
                        self.cache.set(isbn, "eBay", min_price)
                    return min_price
                else:
                    print(f"⚠️ [eBay] Nessun prezzo trovato per ISBN {isbn}")
                    return None

            except Exception as e:
                print(f"❌ [eBay] Errore richiesta per ISBN {isbn} (tentativo {attempt}): {e}")
                if attempt < self.max_retries:
                    print(f"⏳ [eBay] Attendo {self.retry_delay} secondi prima del prossimo tentativo per ISBN {isbn}.")
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ [eBay] Errore definitivo dopo {self.max_retries} tentativi per ISBN {isbn}")
                    return None
