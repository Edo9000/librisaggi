
import pandas as pd
import time
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

from ibs_scraper import IBSScraper
from ebay_scraper import EbayScraper

def load_failed_isbns(filename="isbn_failed.txt"):
    try:
        with open(filename, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

failed_isbns = load_failed_isbns()
print(f"🔁 Riprovo {len(failed_isbns)} ISBN falliti")

max_workers = 4
results = []

ibs_scraper = IBSScraper(max_retries=3, retry_delay=2, timeout=10)
ebay_scraper = EbayScraper(max_retries=3, retry_delay=2, timeout=10)

def retry_worker(isbn):
    result_ibs = ibs_scraper.get_price(isbn)
    time.sleep(random.uniform(0.3, 0.7))
    result_ebay = ebay_scraper.get_price(isbn)
    time.sleep(random.uniform(0.5, 1.0))
    return {"ISBN": isbn, "Prezzo_IBS": result_ibs, "Prezzo_eBay": result_ebay}

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    for r in tqdm(executor.map(retry_worker, failed_isbns), total=len(failed_isbns), desc="Retry scraping"):
        results.append(r)

df = pd.DataFrame(results)
df.to_csv("retry_results.csv", index=False)
print("✅ File salvato: retry_results.csv")
