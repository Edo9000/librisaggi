# ⚙️ Installazione librerie necessarie (esegui manualmente su terminale)
# pip install beautifulsoup4 requests pandas tqdm

# 📚 Import
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# ⬆️ Caricamento del CSV manuale
filename = "20250515165414_allsalable_0.csv"  # Assicurati di avere questo file nella stessa cartella dello script
df = pd.read_csv(filename, sep='\t')

# 🔍 Funzione scraping eBay
'''
def get_ebay_price(isbn, max_retries=2, retry_delay=1):
    url = f"https://www.ebay.it/sch/i.html?_nkw={isbn}"
    headers = {"User-Agent": "Mozilla/5.0"}
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔎 [eBay] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
            r = requests.get(url, headers=headers, timeout=10)
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
            if attempt < max_retries:
                print(f"⏳ [eBay] Attendo {retry_delay} secondi prima del prossimo tentativo per ISBN {isbn}...")
                time.sleep(retry_delay)
            else:
                print(f"❌ [eBay] Errore definitivo dopo {max_retries} tentativi per ISBN {isbn}")
                return None
'''

#def ebay_worker(isbn):
#    result = get_ebay_price(str(isbn))
#    time.sleep(random.uniform(0.2, 0.6))  # Delay random per evitare blocchi
#    return result

#with ThreadPoolExecutor(max_workers=max_workers) as executor:
#    df_scraping['Prezzo_eBay'] = list(tqdm(
#        executor.map(ebay_worker, df_scraping['ISBN']),
#        total=len(df_scraping),
#        desc="eBay scraping"
#    ))

#time.sleep(1)

# 🔍 Funzione scraping IBS
def get_ibs_price(isbn, max_retries=2, retry_delay=1):
    url = f"https://www.ibs.it/search/?ts=as&query={isbn}"
    headers = {"User-Agent": "Mozilla/5.0"}

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔎 [IBS] Cerco prezzo per ISBN: {isbn} (tentativo {attempt})")
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            price_tags = soup.select(".cc-price")
            #TODO: Cambiare il selettore per il prezzo ibs senbra cambiare spesso struttura, ma il prezzo è sempre l'ultimo
            if len(price_tags) >= 30:
                selected = price_tags[29]
                text = selected.get_text().replace("€", "").replace(",", ".").strip()
                print(f"✅ [IBS] Prezzo trovato per ISBN {isbn}: {text}")
                return float(text)
            else:
                print(f"⚠️ [IBS] Solo {len(price_tags)} prezzi trovati per ISBN {isbn}, atteso almeno 30")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ [IBS] Errore richiesta per ISBN {isbn} (tentativo {attempt}): {e}")
            if attempt < max_retries:
                print(f"⏳ [IBS] Attendo {retry_delay} secondi prima del prossimo tentativo per ISBN {isbn}...")
                time.sleep(retry_delay)
            else:
                print(f"❌ [IBS] Errore definitivo dopo {max_retries} tentativi per ISBN {isbn}")
                return None

# 📦 Prendiamo solo le righe dalla 200 alla 300 con ISBN valido
df_filtrati = df[df['ISBN'].notnull()]
df_scraping = df_filtrati.iloc[200:301].copy()

print(f"Numero di ISBN da processare: {len(df_scraping)}")
print(df_scraping['ISBN'].head())

# 📦 Applichiamo lo scraping con barra di avanzamento e parallelizzazione
def ibs_worker(isbn):
    result = get_ibs_price(str(isbn))
    time.sleep(random.uniform(0.2, 0.6))  # Delay random per evitare blocchi
    return result

max_workers = 8  # Puoi aumentare o diminuire in base alla tua connessione

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    df_scraping['Prezzo_IBS'] = list(tqdm(
        executor.map(ibs_worker, df_scraping['ISBN']),
        total=len(df_scraping),
        desc="IBS scraping"
    ))

# 💾 Salvataggio file aggiornato
output_filename = "catalogo_con_prezzi.csv"
df_scraping.to_csv(output_filename, index=False)
print(f"✅ File salvato: {output_filename}")
