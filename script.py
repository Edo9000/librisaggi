# ⚙️ Installazione librerie necessarie (esegui manualmente su terminale)
# pip install beautifulsoup4 requests pandas tqdm

import argparse
import pandas as pd
import time
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from failure_cache import FailureCache

from ibs_scraper import IBSScraper
# Importa solo se serve davvero
try:
    from ebay_scraper import EbayScraper
except ImportError:
    EbayScraper = None

def load_failed_isbns(filename="isbn_failed.txt"):
    try:
        with open(filename, "r") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()    

parser = argparse.ArgumentParser(description="Scrape book prices from IBS and/or eBay.")
parser.add_argument('--ibs', action='store_true', help='Scrape IBS')
parser.add_argument('--ebay', action='store_true', help='Scrape eBay')
args = parser.parse_args()

filename = "20250515165414_allsalable_0.csv"
df = pd.read_csv(filename, sep='\t')
df_filtrati = df[df['ISBN'].notnull()]
df_scraping = df_filtrati.iloc[280:320].copy()

print(f"Numero di ISBN da processare: {len(df_scraping)}")
print(df_scraping['ISBN'].head())

max_workers = 8

if args.ibs:
    ibs_scraper = IBSScraper(max_retries=2, retry_delay=1, timeout=10)
    def ibs_worker(isbn):
        result = ibs_scraper.get_price(str(isbn))
        time.sleep(random.uniform(0.2, 0.6))
        return result
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        df_scraping['Prezzo_IBS'] = list(tqdm(
            executor.map(ibs_worker, df_scraping['ISBN']),
            total=len(df_scraping),
            desc="IBS scraping"
        ))

if args.ebay and EbayScraper is not None:
    ebay_scraper = EbayScraper(max_retries=2, retry_delay=1, timeout=15)
    def ebay_worker(isbn):
        result = ebay_scraper.get_price(str(isbn))
        time.sleep(random.uniform(0.6, 1.1))
        return result
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        df_scraping['Prezzo_eBay'] = list(tqdm(
            executor.map(ebay_worker, df_scraping['ISBN']),
            total=len(df_scraping),
            desc="eBay scraping"
        ))

output_filename = "catalogo_con_prezzi.csv"
df_scraping.to_csv(output_filename, index=False)
print(f"✅ File salvato: {output_filename}")
