import time
from bs4 import BeautifulSoup
from scraper_api_client import ScraperAPIClient
from urllib.parse import quote_plus

class AmazonScraper:
    def __init__(self, max_retries=2, retry_delay=1, timeout=10, api_key=None, price_cache=None):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.api_key = api_key or "e4b967afdaf014ef917eaa9773019cbe"
        self.client = ScraperAPIClient(api_key=self.api_key, country_code="it")
        self.cache = price_cache

    def get_price(self, isbn):
        if self.cache:
            cached_price = self.cache.get(isbn, "Amazon")
            if cached_price is not None:
                print(f"💾 Prezzo trovato nella cache per ISBN {isbn}: {cached_price} €")
                return cached_price

        url = f"https://www.amazon.it/s?k={isbn}"
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [Amazon] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
                html = self.client.get(url, timeout=self.timeout)
                if html is None:
                    raise Exception("Risposta vuota da ScraperAPI")

                soup = BeautifulSoup(html, "html.parser")
                price_tags = soup.select(".a-price .a-offscreen")

                for tag in price_tags:
                    price_text = tag.get_text().strip().replace("€", "").replace(",", ".")
                    try:
                        price = float(price_text)
                        print(f"✅ [Amazon] Prezzo trovato per ISBN {isbn}: {price}")
                        if self.cache:
                            self.cache.set(isbn, "Amazon", price)
                        return price
                    except ValueError:
                        continue

                print(f"⚠️ [Amazon] Nessun prezzo valido trovato per ISBN {isbn}")
                return None

            except Exception as e:
                print(f"❌ [Amazon] Errore per ISBN {isbn} (tentativo {attempt}): {e}")
                if attempt < self.max_retries:
                    print(f"⏳ Ritento tra {self.retry_delay} secondi...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ [Amazon] Errore definitivo dopo {self.max_retries} tentativi.")
                    return None

    def get_top_prices_by_query(self, query, max_results=5):
        search_url = f"https://www.amazon.it/s?k={quote_plus(query)}"
        if self.cache:
            cached_price = self.cache.get(query + "_list", "Amazon")
            if cached_price:
                return cached_price[:max_results]

        prices = []
        for attempt in range(1, self.max_retries + 1):
            try:
                html = self.client.get(search_url)
                if html is None:
                    raise Exception("Risposta vuota da ScraperAPI")

                soup = BeautifulSoup(html, "html.parser")
                for tag in soup.select(".a-price .a-offscreen"):
                    price_text = tag.text
                    if isinstance(price_text, str):
                        price_text = price_text.replace("€", "").replace(",", ".").strip()
                    try:
                        price = float(price_text)
                        prices.append(price)
                        if len(prices) >= max_results:
                            break
                    except (ValueError, TypeError):
                        continue
                break
            except Exception as e:
                print(f"❌ [Amazon] Errore per query '{query}': {e}")
                time.sleep(self.retry_delay)

        if self.cache:
            self.cache.set(query + "_list", "Amazon", prices)
        return prices
