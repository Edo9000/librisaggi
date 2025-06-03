import pandas as pd
import time
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from amazon_scraper import AmazonScraper
from ibs_scraper import IBSScraper
from ebay_scraper import EbayScraper
from price_cache import PriceCache
from typing import Callable
from concurrent.futures import as_completed

def start_processing_csv(
    filename: str,
    use_ibs: bool = True,
    use_ebay: bool = True,
    use_amz: bool = False,
    max_workers: int = 5,
    output_filename: str = "catalogo_con_prezzi.csv",
    row_limit: int = 30,
    progress_callback=None,
    stop_requested_callback: Callable[[], bool] = lambda: False,
    use_cache: bool = False
) -> str:
    df = pd.read_csv(filename, sep='\t')
    df_filtrati = df[df['ISBN'].notnull()]
    if row_limit is None:
        df_scraping = df_filtrati.copy()
    else:
        df_scraping = df_filtrati.iloc[1:1 + row_limit].copy()

    print(f"🔢 ISBN da processare: {len(df_scraping)}")

    sentinel_isbns = ["1234567891011", "1234567881012", "1234667881012"]
    cache = PriceCache() if use_cache else None

    def wrap_with_progress(scraper_fn, isbn_list, label):
        results = [None] * len(isbn_list)
        total = len(isbn_list)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(scraper_fn, isbn): idx
                for idx, isbn in enumerate(isbn_list)
            }
            for i, future in enumerate(tqdm(as_completed(future_to_index), total=total, desc=label)):
                if stop_requested_callback():
                    print("⛔ Interrotto su richiesta dell'utente")
                    break
                idx = future_to_index[future]
                try:
                    result = future.result()
                except Exception as e:
                    result = None
                    print(f"⚠️ Errore nel worker: {e}")
                results[idx] = result
                if progress_callback:
                    progress_callback((i + 1) / total)
        return results

    if use_ibs:
        ibs_scraper = IBSScraper(sentinel_isbns=sentinel_isbns, max_retries=2, retry_delay=1, timeout=10, price_cache=cache)
        def ibs_worker(isbn):
            result = ibs_scraper.get_price(str(isbn))
            time.sleep(random.uniform(0.2, 0.6))
            return result
        df_scraping['Prezzo_IBS'] = wrap_with_progress(ibs_worker, df_scraping['ISBN'], "IBS")

    if use_ebay and EbayScraper is not None:
        ebay_scraper = EbayScraper(max_retries=2, retry_delay=1, timeout=10, price_cache=cache)
        def ebay_worker(isbn):
            result = ebay_scraper.get_price(str(isbn))
            time.sleep(random.uniform(0.6, 1.1))
            return result
        df_scraping['Prezzo_eBay'] = wrap_with_progress(ebay_worker, df_scraping['ISBN'], "eBay")

    if use_amz and AmazonScraper is not None:
        amz_scraper = AmazonScraper(max_retries=2, retry_delay=1, timeout=15, price_cache=cache)
        def amz_worker(isbn):
            result = amz_scraper.get_price(str(isbn))
            time.sleep(random.uniform(0.8, 1.5))  
            return result
        df_scraping['Prezzo_Amazon'] = wrap_with_progress(amz_worker, df_scraping['ISBN'], "Amazon")

    def get_min_price(row):
        prezzi = []
        for col in ["Prezzo_IBS", "Prezzo_eBay", "Prezzo_Amazon"]:
            try:
                val = float(row[col])
                if val > 0:
                    prezzi.append(val)
            except (ValueError, TypeError, KeyError):
                continue
        return min(prezzi) if prezzi else row.get("Prezzo", None)

    df_scraping["Prezzo"] = df_scraping.apply(get_min_price, axis=1)

    for col in ["Prezzo_IBS", "Prezzo_eBay", "Prezzo_Amazon"]:
        if col in df_scraping.columns:
            del df_scraping[col]

    df_scraping.to_csv(output_filename, index=False)
    print(f"✅ File salvato: {output_filename}")

    if cache:
        cache.save()

    return output_filename
