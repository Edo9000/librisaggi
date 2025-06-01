import pandas as pd
import time
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from amazon_scraper import AmazonScraper
from ibs_scraper import IBSScraper
from ebay_scraper import EbayScraper

def start_processing_csv(
    filename: str,
    use_ibs: bool = True,
    use_ebay: bool = True,
    use_amz: bool = False,
    max_workers: int = 5,
    output_filename: str = "catalogo_con_prezzi.csv",
    row_limit: int = 30,
    progress_callback=None
) -> str:
    df = pd.read_csv(filename, sep='\t')
    df_filtrati = df[df['ISBN'].notnull()]
    df_scraping = df_filtrati.iloc[1:1 + row_limit].copy()

    print(f"🔢 ISBN da processare: {len(df_scraping)}")

    sentinel_isbns = ["1234567891011", "1234567881012", "1234667881012"]

    def wrap_with_progress(scraper_fn, isbn_list, label):
        results = []
        total = len(isbn_list)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i, result in enumerate(tqdm(executor.map(scraper_fn, isbn_list), total=total, desc=label)):
                results.append(result)
                if progress_callback:
                    progress_callback((i + 1) / total)
        return results

    if use_ibs:
        ibs_scraper = IBSScraper(sentinel_isbns=sentinel_isbns, max_retries=2, retry_delay=1, timeout=10)
        def ibs_worker(isbn):
            result = ibs_scraper.get_price(str(isbn))
            time.sleep(random.uniform(0.2, 0.6))
            return result
        df_scraping['Prezzo_IBS'] = wrap_with_progress(ibs_worker, df_scraping['ISBN'], "IBS")

    if use_ebay and EbayScraper is not None:
        ebay_scraper = EbayScraper(max_retries=2, retry_delay=1, timeout=10)
        def ebay_worker(isbn):
            result = ebay_scraper.get_price(str(isbn))
            time.sleep(random.uniform(0.6, 1.1))
            return result
        df_scraping['Prezzo_eBay'] = wrap_with_progress(ebay_worker, df_scraping['ISBN'], "eBay")

    if use_amz and AmazonScraper is not None:
        amz_scraper = AmazonScraper(max_retries=2, retry_delay=1, timeout=15)
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
    return output_filename
