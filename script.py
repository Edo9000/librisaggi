# ⚙️ Installazione librerie necessarie (esegui manualmente su terminale)
# pip install beautifulsoup4 requests pandas tqdm

# 📚 Import
import pandas as pd
import time
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

from ibs_scraper import IBSScraper
# from ebay_scraper import EbayScraper  # Decommenta se ti serve

filename = "20250515165414_allsalable_0.csv"
df = pd.read_csv(filename, sep='\t')
df_filtrati = df[df['ISBN'].notnull()]
df_scraping = df_filtrati.iloc[200:301].copy()

print(f"Numero di ISBN da processare: {len(df_scraping)}")
print(df_scraping['ISBN'].head())

ibs_scraper = IBSScraper(max_retries=2, retry_delay=1, timeout=10)
# ebay_scraper = EbayScraper(max_retries=2, retry_delay=1, timeout=10)

def ibs_worker(isbn):
    result = ibs_scraper.get_price(str(isbn))
    time.sleep(random.uniform(0.2, 0.6))
    return result

# def ebay_worker(isbn):
#     result = ebay_scraper.get_price(str(isbn))
#     time.sleep(random.uniform(0.2, 0.6))
#     return result

max_workers = 8

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    df_scraping['Prezzo_IBS'] = list(tqdm(
        executor.map(ibs_worker, df_scraping['ISBN']),
        total=len(df_scraping),
        desc="IBS scraping"
    ))

# with ThreadPoolExecutor(max_workers=max_workers) as executor:
#     df_scraping['Prezzo_eBay'] = list(tqdm(
#         executor.map(ebay_worker, df_scraping['ISBN']),
#         total=len(df_scraping),
#         desc="eBay scraping"
#     ))

output_filename = "catalogo_con_prezzi.csv"
df_scraping.to_csv(output_filename, index=False)
print(f"✅ File salvato: {output_filename}")
