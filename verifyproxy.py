import requests
import concurrent.futures
import time

TEST_URL = "https://httpbin.org/ip"
TIMEOUT = 5
INPUT_FILE = "proxies.txt"
OUTPUT_FILE = "working_proxies.txt"

def is_proxy_working(proxy):
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        r = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT)
        if r.status_code == 200:
            print(f"✅ Proxy funzionante: {proxy} -> IP: {r.json()['origin']}")
            return proxy
    except Exception as e:
        print(f"❌ Proxy fallito: {proxy} -> {e}")
    return None

def verify_proxies():
    with open(INPUT_FILE, "r") as f:
        proxy_list = [line.strip() for line in f if line.strip()]

    working = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(is_proxy_working, proxy_list))
        working = [proxy for proxy in results if proxy]

    with open(OUTPUT_FILE, "w") as f:
        for proxy in working:
            f.write(proxy + "\n")

    print(f"\n🔎 Trovati {len(working)} proxy funzionanti su {len(proxy_list)}")
    print(f"💾 Salvati in '{OUTPUT_FILE}'")

if __name__ == "__main__":
    verify_proxies()
