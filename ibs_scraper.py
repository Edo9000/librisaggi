import requests
from bs4 import BeautifulSoup
import time

class IBSScraper:
    def __init__(self, max_retries=2, retry_delay=1, timeout=10):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def get_price(self, isbn):
        url = f"https://www.ibs.it/search/?ts=as&query={isbn}"
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"🔎 [IBS] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
                r = requests.get(url, headers=self.headers, timeout=self.timeout)
                soup = BeautifulSoup(r.text, "html.parser")
                price_tags = soup.select(".cc-price")
                if len(price_tags) >= 1:
                    selected = price_tags[-1]
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