import pandas as pd
import time
import random
import os
from csv_da_cache import esegui_post_processing
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from ebay_scraper import EbayScraper
from AbeBooksScraper import AbeBooksScraper
from price_cache import PriceCache
from scraper_api_client import build_query
from typing import Callable
from concurrent.futures import as_completed
from pathlib import Path

base_dir = Path.home() / "Documents" / "Librisaggi"
data_dir = base_dir / "output"
data_dir.mkdir(parents=True, exist_ok=True)

cache_file = data_dir / "price_cache.json"
output_file = data_dir / "catalogo_finale.csv"
output_confronto = data_dir / "confronto_prezzi.csv"
input_file = data_dir / "catalogo_di_debug.csv"

def start_processing_csv(
    filename: str,
    max_workers: int = 5,
    output_filename: str = str(data_dir / "catalogo_di_debug.csv"),
    row_limit: int = 30,
    progress_callback=None,
    stop_requested_callback: Callable[[], bool] = lambda: False,
    use_cache: bool = True,
    api_key=None
) -> str:
    df = pd.read_csv(filename, sep='\t')
    df_has_isbn = df[df['ISBN'].notnull()]
    df_no_isbn = df[df['ISBN'].isnull()]

    if row_limit is not None:
        df_has_isbn = df_has_isbn.iloc[1:1 + row_limit].copy()
        df_no_isbn = df_no_isbn.iloc[1:1 + row_limit].copy()

    print(f"🔢 Libri con ISBN da processare: {len(df_has_isbn)}")
    print(f"🔍 Libri SENZA ISBN da processare: {len(df_no_isbn)}")

    cache = PriceCache(path=cache_file) if use_cache else None

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

    ebay_scraper = EbayScraper(max_retries=2, retry_delay=2, timeout=30, price_cache=cache, api_key=api_key)
    def ebay_worker(isbn):
        if stop_requested_callback():
            return None
        result = ebay_scraper.get_price(str(isbn))
        time.sleep(random.uniform(0.6, 1.1))
        return result
    df_has_isbn['Prezzo_eBay'] = wrap_with_progress(ebay_worker, df_has_isbn['ISBN'], "eBay")

    abebooks_scraper = AbeBooksScraper(max_retries=2, retry_delay=2, timeout=30, price_cache=cache, api_key=api_key)
    def abebooks_worker(isbn):
        if stop_requested_callback():
            return None
        prices = abebooks_scraper.get_price(str(isbn))
        time.sleep(random.uniform(0.7, 1.2))
        if prices:
            return round(sum(prices) / len(prices), 2)
        return None
    df_has_isbn['Prezzo_AbeBooks'] = wrap_with_progress(abebooks_worker, df_has_isbn['ISBN'], "AbeBooks (media 5)")


    def ebay_query_worker(row):
        if stop_requested_callback():
            return None
        query = build_query(row['Titolo'], row['Editore'], row['Anno di stampa'])
        return ebay_scraper.get_top_prices_by_query(query, max_results=5)
    df_no_isbn['Prezzi_eBay'] = wrap_with_progress(ebay_query_worker, df_no_isbn.to_dict('records'), "eBay (senza ISBN)")

    def abebooks_query_worker(row):
        if stop_requested_callback():
            return None
        query = build_query(row['Titolo'], row['Editore'], row['Anno di stampa'])
        return abebooks_scraper.get_top_prices_by_query(query, max_results=5)
    df_no_isbn['Prezzi_AbeBooks'] = wrap_with_progress(abebooks_query_worker, df_no_isbn.to_dict('records'), "AbeBooks (senza ISBN)")


    def final_price_with_isbn(row):
        prezzi = []
        for col in ["Prezzo_eBay", "Prezzo_AbeBooks"]:
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

    def final_price(row):
        prezzi = []
        for col in ["Prezzi_eBay", "Prezzi_AbeBooks"]:
            values = row.get(col, [])
            if isinstance(values, str):
                try:
                    values = eval(values)
                except:
                    values = []
            if isinstance(values, list):
                prezzi.extend([float(v) for v in values if v > 0])
        return round(sum(prezzi) / len(prezzi), 2) if prezzi else None

    df_no_isbn["Prezzo"] = df_no_isbn.apply(final_price, axis=1)

    df_all = pd.concat([df_has_isbn, df_no_isbn], ignore_index=True)

    try:
        if stop_requested_callback():
            print("⛔ Interrotto prima del salvataggio. Scrivo file parziale.")

        for col in ["Prezzo_eBay", "Prezzo_AbeBooks", "Prezzi_eBay", "Prezzi_AbeBooks"]:
            if col in df_all.columns:
                del df_all[col]

        df_all.to_csv(output_filename, index=False, sep="\t")
        print(f"✅ File salvato: {output_filename}")

    finally:
        if cache:
            cache.save()
            print("💾 Cache salvata.")

    if stop_requested_callback():
        print("⛔ Interrotto prima della post-elaborazione.")
        return output_filename

    esegui_post_processing(
        input_file=input_file,
        cache_file=cache_file,
        output_file=output_file,
        output_confronto=output_confronto
    )

    return output_filename