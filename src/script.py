# ⚙️ Installazione librerie necessarie (esegui manualmente su terminale)
# pip install beautifulsoup4 requests pandas tqdm

import argparse
import pandas as pd
import time
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from amazon_scraper import AmazonScraper
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

parser = argparse.ArgumentParser(description="Scrape book prices from IBS and/or eBay and/or Amazon.")
parser.add_argument('--ibs', action='store_true', help='Scrape IBS')
parser.add_argument('--ebay', action='store_true', help='Scrape eBay')
parser.add_argument('--amz', action='store_true', help='Scrape Amazon')
args = parser.parse_args()

filename = "20250515165414_allsalable_0.csv"
df = pd.read_csv(filename, sep='\t')
df_filtrati = df[df['ISBN'].notnull()]
df_scraping = df_filtrati.iloc[1:32].copy()

print(f"Numero di ISBN da processare: {len(df_scraping)}")
print(df_scraping['ISBN'].head())

# Lista di ISBN fittizi noti per non restituire risultati
sentinel_isbns = ["1234567891011", "1234567881012", "1234667881012"]


max_workers = 5

if args.ibs:
    ibs_scraper = IBSScraper(sentinel_isbns=sentinel_isbns, max_retries=2, retry_delay=1, timeout=10)
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
    ebay_scraper = EbayScraper(max_retries=2, retry_delay=1, timeout=10)
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

if args.amz and AmazonScraper is not None:
    amz_scraper = AmazonScraper(max_retries=2, retry_delay=1, timeout=10)
    def amz_worker(isbn):
        result = amz_scraper.get_price(str(isbn))
        time.sleep(random.uniform(0.6, 1.1))
        return result
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        df_scraping['Prezzo_Amazon'] = list(tqdm(
            executor.map(amz_worker, df_scraping['ISBN']),
            total=len(df_scraping),
            desc="Amazon scraping"
        ))        

output_filename = "catalogo_con_prezzi.csv"
df_scraping.to_csv(output_filename, index=False)
print(f"✅ File salvato: {output_filename}")
