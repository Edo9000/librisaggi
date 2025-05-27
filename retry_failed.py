from src.ibs_scraper import IBSScraper
from src.ebay_scraper import EbayScraper
from src.failure_cache import FailureCache

def retry_failed_isbns():
    print("🔁 Inizio riprova ISBN falliti...")
    failure_cache = FailureCache()
    ibs_scraper = IBSScraper()
    ebay_scraper = EbayScraper()

    failed_isbns = failure_cache.get_all()

    if not failed_isbns:
        print("✅ Nessun ISBN da riprovare.")
        return

    for isbn in failed_isbns:
        print(f"\n📚 ISBN: {isbn}")
        ibs_price = ibs_scraper.get_price(isbn)
        ebay_price = ebay_scraper.get_price(isbn)

        # Se almeno uno dei due ha successo, lo rimuoviamo dalla cache dei falliti
        if ibs_price is not None or ebay_price is not None:
            failure_cache.remove(isbn)

    print("\n🏁 Riprova completata.")

if __name__ == "__main__":
    retry_failed_isbns()
