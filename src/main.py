import pandas as pd
import time
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from amazon_scraper import AmazonScraper
from ibs_scraper import IBSScraper
from ebay_scraper import EbayScraper
from AbeBooksScraper import AbeBooksScraper
from price_cache import PriceCache
from scraper_api_client import build_query
from price_logic import final_price_no_isbn_multiple
from typing import Callable
from concurrent.futures import as_completed

def start_processing_csv(
    filename: str,
    use_ibs: bool = True,
    use_ebay: bool = True,
    use_amz: bool = False,
    use_abebooks: bool = False,
    max_workers: int = 5,
    output_filename: str = "catalogo_con_prezzi.csv",
    row_limit: int = 30,
    progress_callback=None,
    stop_requested_callback: Callable[[], bool] = lambda: False,
    use_cache: bool = True
) -> str:
    df = pd.read_csv(filename, sep='\t')
    df_has_isbn = df[df['ISBN'].notnull()]
    df_no_isbn = df[df['ISBN'].isnull()]

    if row_limit is not None:
        df_has_isbn = df_has_isbn.iloc[1:1 + row_limit].copy()
        df_no_isbn = df_no_isbn.iloc[1:1 + row_limit].copy()

    print(f"🔢 Libri con ISBN da processare: {len(df_has_isbn)}")
    print(f"🔍 Libri SENZA ISBN da processare: {len(df_no_isbn)}")

    sentinel_isbns = ["1234567891011", "1234567881012", "1234667881012"]
    cache = PriceCache() if use_cache else None

    def wrap_with_progress(scraper_fn, item_list, label):
        results = [None] * len(item_list)
        total = len(item_list)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(scraper_fn, item): idx
                for idx, item in enumerate(item_list)
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
        df_has_isbn['Prezzo_IBS'] = wrap_with_progress(ibs_worker, df_has_isbn['ISBN'], "IBS")

    if use_ebay:
        ebay_scraper = EbayScraper(max_retries=2, retry_delay=1, timeout=10, price_cache=cache)
        def ebay_worker(isbn):
            result = ebay_scraper.get_price(str(isbn))
            time.sleep(random.uniform(0.6, 1.1))
            return result
        df_has_isbn['Prezzo_eBay'] = wrap_with_progress(ebay_worker, df_has_isbn['ISBN'], "eBay")

    if use_amz:
        amz_scraper = AmazonScraper(max_retries=2, retry_delay=1, timeout=15, price_cache=cache)
        def amz_worker(isbn):
            result = amz_scraper.get_price(str(isbn))
            time.sleep(random.uniform(0.8, 1.5))
            return result
        df_has_isbn['Prezzo_Amazon'] = wrap_with_progress(amz_worker, df_has_isbn['ISBN'], "Amazon")

    if use_abebooks:
        abebooks_scraper = AbeBooksScraper(max_retries=2, retry_delay=1, timeout=15, price_cache=cache)
        def abebooks_worker(isbn):
            prices = abebooks_scraper.get_price(str(isbn))
            time.sleep(random.uniform(0.7, 1.2))
            if prices:
                return round(sum(prices) / len(prices), 2)
            return None
        df_has_isbn['Prezzo_AbeBooks'] = wrap_with_progress(abebooks_worker, df_has_isbn['ISBN'], "AbeBooks (media 5)")


    if use_ebay:
        def ebay_query_worker(row):
            query = build_query(row['Titolo'], row['Editore'], row['Anno di stampa'])
            return ebay_scraper.get_top_prices_by_query(query, max_results=5)
        df_no_isbn['Prezzi_eBay'] = wrap_with_progress(ebay_query_worker, df_no_isbn.to_dict('records'), "eBay (senza ISBN)")

    if use_amz:
        def amz_query_worker(row):
            query = build_query(row['Titolo'], row['Editore'], row['Anno di stampa'])
            return amz_scraper.get_top_prices_by_query(query, max_results=5)
        df_no_isbn['Prezzi_Amazon'] = wrap_with_progress(amz_query_worker, df_no_isbn.to_dict('records'), "Amazon (senza ISBN)")

    if use_abebooks:
        def abebooks_query_worker(row):
            query = build_query(row['Titolo'], row['Editore'], row['Anno di stampa'])
            return abebooks_scraper.get_top_prices_by_query(query, max_results=5)
        df_no_isbn['Prezzi_AbeBooks'] = wrap_with_progress(abebooks_query_worker, df_no_isbn.to_dict('records'), "AbeBooks (senza ISBN)")


    def final_price_with_isbn(row):
        prezzi = []
        for col in ["Prezzo_IBS", "Prezzo_eBay", "Prezzo_Amazon", "Prezzo_AbeBooks"]:
            try:
                val = float(row[col])
                if val > 0:
                    prezzi.append(val)
            except (ValueError, TypeError, KeyError):
                continue
        if not prezzi:
            return row.get("Prezzo", None)
        return round(sum(prezzi) / len(prezzi) * 0.95, 2)

    df_has_isbn["Prezzo"] = df_has_isbn.apply(final_price_with_isbn, axis=1)

    if cache:
        print("💾 Cache salvata dopo blocco ISBN")
        cache.save()

    manual_check_rows = []
    prezzi_finali = []

    for _, row in df_no_isbn.iterrows():
        prezzo, flag_manual = final_price_no_isbn_multiple(row)
        prezzi_finali.append(prezzo)
        if flag_manual:
            row_dict = row.to_dict()
            row_dict["NOTE"] = "Unica copia / necessario controllo manuale"
            manual_check_rows.append(row_dict)

    df_no_isbn["Prezzo"] = prezzi_finali

    df_all = pd.concat([df_has_isbn, df_no_isbn], ignore_index=True)

    try:
        if stop_requested_callback():
            print("⛔ Interrotto prima del salvataggio. Scrivo file parziale.")

        for col in ["Prezzo_IBS", "Prezzo_eBay", "Prezzo_Amazon", "Prezzo_Abebooks", "Prezzi_eBay", "Prezzi_Amazon", "Prezzi_AbeBooks"]:
            if col in df_all.columns:
                del df_all[col]

        df_all.to_csv(output_filename, index=False)
        print(f"✅ File salvato: {output_filename}")

        if manual_check_rows:
            pd.DataFrame(manual_check_rows).to_csv("manual_check.csv", index=False)
            print(f"📄 Salvati {len(manual_check_rows)} libri da controllare manualmente in manual_check.csv")

    finally:
        if cache:
            cache.save()
            print("💾 Cache salvata.")

    return output_filename