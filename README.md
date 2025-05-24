# librisaggi

## comandi

Solo IBS:
python --ibs
Solo eBay:
python --ebay
Entrambi:
python --ibs --ebay

struttura che dovrei avere
librisaggi/
├── proxies.txt
├── failed_isbn.json
├── retry_failed.py
├── src/
│   ├── ibs_scraper.py
│   ├── ebay_scraper.py
│   ├── failure_cache.py
│   └── proxy_manager.py