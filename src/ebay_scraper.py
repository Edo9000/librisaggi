import time
from bs4 import BeautifulSoup
from scraper_api_client import ScraperAPIClient
from urllib.parse import quote_plus

class EbayScraper:
    def __init__(self, max_retries=2, retry_delay=1, timeout=30, api_key=None, price_cache=None):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.api_key = api_key
        self.client = ScraperAPIClient(api_key=self.api_key, country_code="it")
        self.cache = price_cache

    def get_price(self, isbn):
        if self.cache:
            cached_price = self.cache.get(isbn, "eBay")
            if cached_price is not None:
                print(f"💾 [eBay] Prezzo cache per ISBN {isbn}: {cached_price} €")
                return cached_price

        url = f"https://www.ebay.it/sch/i.html?_nkw={quote_plus(isbn)}"
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [eBay] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
                html = self.client.get(url, timeout=self.timeout)
                if not html:
                    raise Exception("Risposta vuota da ScraperAPI")

                soup = BeautifulSoup(html, "html.parser")
                prices = []
                for tag in soup.select(".s-item__price"):
                    try:
                        price_text = tag.get_text().replace("€", "").replace(",", ".").strip()
                        price = float(price_text.split()[0])
                        prices.append(price)
                    except (ValueError, TypeError, IndexError):
                        continue

                filtered_prices = [p for p in prices if p > 0]
                if filtered_prices:
                    min_price = min(filtered_prices)
                    print(f"✅ [eBay] Prezzo trovato per ISBN {isbn}: {min_price}")
                    if self.cache:
                        self.cache.set(isbn, "eBay", min_price)
                    return min_price
                else:
                    print(f"⚠️ [eBay] Nessun prezzo valido trovato per ISBN {isbn}")
                    return None

            except Exception as e:
                print(f"❌ [eBay] Errore per ISBN {isbn} (tentativo {attempt}): {type(e).__name__} - {e}")
                if attempt < self.max_retries:
                    print(f"⏳ Ritento in {self.retry_delay} secondi...")
                    time.sleep(self.retry_delay)
        print(f"❌ [eBay] Errore definitivo per ISBN {isbn}")
        return None

    def get_top_prices_by_query(self, query, max_results=5):
        search_url = f"https://www.ebay.it/sch/i.html?_nkw={quote_plus(query)}&LH_BIN=1"

        if self.cache:
            cached_price = self.cache.get(query + "_list", "eBay")
            if cached_price:
                return cached_price[2:2 + max_results] if len(cached_price) > 2 else cached_price[:max_results]

        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [eBay] Cerco prezzi multipli per query: '{query}' (tentativo {attempt})")
                html = self.client.get(search_url, timeout=self.timeout)
                if not html:
                    raise Exception("Risposta vuota da ScraperAPI")

                soup = BeautifulSoup(html, "html.parser")
                prices = []
                for tag in soup.select(".s-item__price"):
                    try:
                        text = tag.get_text().replace("€", "").replace("EUR", "").replace(",", ".").replace("$", "").strip()
                        parts = text.split()
                        if not parts:
                            continue
                        price = float(parts[0])
                        if price > 0:
                            prices.append(price)
                    except (ValueError, IndexError):
                        continue
                
                print(f"🧾 [eBay] Tutti i prezzi trovati per '{query}': {prices}")

                if len(prices) > 2:
                    filtered_prices = prices[2:2 + max_results]
                else:
                    filtered_prices = prices[:max_results]

                if filtered_prices:
                    print(f"✅ [eBay] Prezzi validi per '{query}': {filtered_prices}")
                else:
                    print(f"⚠️ [eBay] Nessun prezzo valido per query '{query}'")

                if self.cache:
                    self.cache.set(query + "_list", "eBay", filtered_prices)
                return filtered_prices
            except Exception as e:
                print(f"❌ [eBay] Errore query '{query}' (tentativo {attempt}): {type(e).__name__} - {e}")
                time.sleep(self.retry_delay)

        print(f"⚠️ [eBay] Nessun risultato valido per query '{query}'")
        return []
