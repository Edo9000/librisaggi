import time
from bs4 import BeautifulSoup
from scraper_api_client import ScraperAPIClient
from urllib.parse import quote_plus

class AbeBooksScraper:
    def __init__(self, max_retries=2, retry_delay=1, timeout=30, api_key=None, price_cache=None):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.api_key = api_key or "e4b967afdaf014ef917eaa9773019cbe"
        self.client = ScraperAPIClient(api_key=self.api_key, country_code="it")
        self.cache = price_cache

    def get_price(self, isbn, max_results=5):
        if self.cache:
            cached_price = self.cache.get(isbn + "_list", "AbeBooks")
            if cached_price:
                return cached_price[:max_results]

        url = f"https://www.abebooks.it/servlet/SearchResults?isbn={quote_plus(isbn)}"
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [AbeBooks] Cerco prezzi per ISBN: {isbn} (tentativo {attempt})")
                html = self.client.get(url, timeout=self.timeout)
                if not html:
                    raise Exception("Risposta vuota da ScraperAPI")

                soup = BeautifulSoup(html, "html.parser")
                prices = []
                for tag in soup.select(".item-price"):
                    try:
                        text = tag.get_text().replace("EUR", "").replace(",", ".").replace("\xa0", "").strip()
                        price = float(text)
                        if price > 0:
                            prices.append(price)
                    except ValueError:
                        continue

                filtered = prices[:max_results]

                if filtered:
                    print(f"✅ [AbeBooks] Prezzi trovati per ISBN {isbn}: {filtered}")
                    if self.cache:
                        self.cache.set(isbn + "_list", "AbeBooks", filtered)
                    return filtered
                else:
                    print(f"⚠️ [AbeBooks] Nessun prezzo valido trovato per ISBN {isbn}")
                    return []

            except Exception as e:
                print(f"❌ [AbeBooks] Errore per ISBN {isbn} (tentativo {attempt}): {type(e).__name__} - {e}")
                time.sleep(self.retry_delay)

        print(f"❌ [AbeBooks] Errore definitivo per ISBN {isbn}")
        return []


    def get_top_prices_by_query(self, query, max_results=5):
        search_url = f"https://www.abebooks.it/servlet/SearchResults?sts=t&kn={quote_plus(query)}"

        if self.cache:
            cached = self.cache.get(query + "_list", "AbeBooks")
            if cached:
                return cached[:max_results]

        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [AbeBooks] Cerco prezzi per query: '{query}' (tentativo {attempt})")
                html = self.client.get(search_url, timeout=self.timeout)
                if not html:
                    raise Exception("Risposta vuota da ScraperAPI")

                soup = BeautifulSoup(html, "html.parser")
                prices = []
                for tag in soup.select(".item-price"):
                    try:
                        text = tag.get_text().replace("EUR", "").replace(",", ".").replace("\xa0", "").strip()
                        price = float(text)
                        if price > 0:
                            prices.append(price)
                    except ValueError:
                        continue

                print(f"🧾 [AbeBooks] Tutti i prezzi trovati per '{query}': {prices}")
                filtered = prices[:max_results]

                if filtered:
                    print(f"✅ [AbeBooks] Prezzi validi per '{query}': {filtered}")
                else:
                    print(f"⚠️ [AbeBooks] Nessun prezzo valido per query '{query}'")

                if self.cache:
                    self.cache.set(query + "_list", "AbeBooks", filtered)

                return filtered

            except Exception as e:
                print(f"❌ [AbeBooks] Errore query '{query}' (tentativo {attempt}): {type(e).__name__} - {e}")
                time.sleep(self.retry_delay)

        print(f"⚠️ [AbeBooks] Nessun risultato valido per query '{query}'")
        return []
