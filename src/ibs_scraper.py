import time
from bs4 import BeautifulSoup
from scraper_api_client import ScraperAPIClient

class IBSScraper:
    def __init__(self, max_retries=2, retry_delay=1, timeout=10, api_key=None, sentinel_isbns=None, price_cache=None):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.api_key = api_key or "172215073eaeac24a47020e044760bf5"
        self.client = ScraperAPIClient(api_key=self.api_key, country_code="it")
        self.sentinel_index = None
        self.cache = price_cache

        if sentinel_isbns:
            self.sentinel_index = self.detect_sentinel_index(sentinel_isbns)

    def detect_sentinel_index(self, isbns):
        print("🔍 Avvio rilevamento indice sentinella...")
        index_counts = {}

        for isbn in isbns:
            url = f"https://www.ibs.it/search/?ts=as&query={isbn}"
            try:
                html = self.client.get(url)
                if html is None:
                    continue

                soup = BeautifulSoup(html, "html.parser")
                price_tags = soup.select(".cc-price")
                print(f"📘 ISBN {isbn} → {len(price_tags)} prezzi")

                if price_tags:
                    last_index = len(price_tags) - 1
                    index_counts[last_index] = index_counts.get(last_index, 0) + 1

            except Exception as e:
                print(f"⚠️ Errore durante rilevamento per ISBN {isbn}: {e}")

        if not index_counts:
            raise Exception("❌ Nessuna informazione trovata per rilevare l'indice sentinella.")

        # Trova l'indice più frequente
        sentinel_index = max(index_counts, key=index_counts.get)
        print(f"📌 Indice sentinella rilevato: {sentinel_index}")
        return sentinel_index

    def get_price(self, isbn):
        if self.cache:
            cached_price = self.cache.get(isbn, "IBS")
            if cached_price is not None:
                print(f"💾 Prezzo trovato nella cache per ISBN {isbn}: {cached_price} €")
                return cached_price
            
        url = f"https://www.ibs.it/search/?ts=as&query={isbn}"
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [IBS] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
                html = self.client.get(url)
                if html is None:
                    raise Exception("Risposta vuota da ScraperAPI")

                soup = BeautifulSoup(html, "html.parser")
                price_tags = soup.select(".cc-price")
                print(f"🔢 Trovati {len(price_tags)} prezzi per ISBN {isbn}")

                if self.sentinel_index is None:
                    raise Exception("Indice sentinella non impostato. Passare sentinel_isbns al costruttore.")

                # Tentativo di accesso diretto
                try:
                    price_tag = price_tags[self.sentinel_index + 1]
                except IndexError:
                    print(f"⚠️ [IBS] Nessun prezzo valido oltre la sentinella per ISBN {isbn}")
                    return None  # ⛔️ Nessun retry, ritorno immediato

                text = price_tag.get_text().replace("€", "").replace(",", ".").strip()
                price = float(text)
                print(f"✅ [IBS] Prezzo selezionato per ISBN {isbn}: {price} €")
                
                if self.cache:
                    self.cache.set(isbn, "IBS", price)
                
                return price

            except Exception as e:
                print(f"❌ [IBS] Errore richiesta per ISBN {isbn} (tentativo {attempt}): {e}")
                if attempt < self.max_retries:
                    print(f"⏳ Attendo {self.retry_delay} secondi prima del prossimo tentativo.")
                    time.sleep(self.retry_delay)
                else:
                    print(f"❌ Errore definitivo dopo {self.max_retries} tentativi.")
                    return None

