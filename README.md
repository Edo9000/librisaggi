# 📚 Scraper per Librisaggi

Lo **Scraper** è uno strumento in Python progettato per confrontare i prezzi dei libri su diverse piattaforme online, tra cui IBS, eBay e Amazon. L'obiettivo è facilitare la ricerca del miglior prezzo per un determinato libro, automatizzando il processo di raccolta e confronto dei dati.

## 🚀 Funzionalità

* **Ricerca multipiattaforma**: consente di effettuare ricerche su IBS, eBay e Amazon.
* **Esecuzione selettiva**: possibilità di scegliere su quali piattaforme effettuare la ricerca.
* **Caching dei prezzi**: implementazione di un sistema di caching per evitare richieste ripetitive e migliorare le prestazioni.
* **Interfaccia grafica**: presenza di un'interfaccia utente per facilitare l'interazione con l'applicazione.

## 🛠️ Installazione

1. **Clona il repository**:

   ```bash
   git clone https://github.com/Edo9000/librisaggi.git
   cd librisaggi
   ```

2. **Installa le dipendenze**:

   Assicurati di avere Python 3 installato. Poi, installa le dipendenze necessarie:

   ```bash
   pip install -r requirements.txt
   ```

   > *Nota*: Il file `requirements.txt` dovrebbe contenere tutte le librerie necessarie per l'esecuzione del progetto.

## ⚙️ Utilizzo

Puoi eseguire l'applicazione da linea di comando con i seguenti parametri:

* Solo IBS:

  ```bash
  python main_gui.py --ibs
  ```

* Solo eBay:

  ```bash
  python main_gui.py --ebay
  ```

* Solo Amazon:

  ```bash
  python main_gui.py --amz
  ```

* Tutte le piattaforme:

  ```bash
  python main_gui.py --ibs --ebay --amz
  ```

## 📋 TODO

* Implementare un selettore per gruppi di libri.
* Testare il sistema su un primo batch di 1000 libri con eBay e IBS.
* Rivedere e ottimizzare il sistema di caching.
* Migliorare l'interfaccia utente per una migliore esperienza.

## 📂 Struttura del progetto

* `main_gui.py`: script principale per l'esecuzione dell'applicazione con interfaccia grafica.
* `src/`: directory contenente i moduli e le funzioni ausiliarie.
* `price_cache.json`: file utilizzato per il caching dei prezzi.
* `.gitignore`: file per escludere determinati file e directory dal controllo di versione.
* `README.md`: questo file.

## 🤝 Contributi

I contributi sono benvenuti! Se desideri contribuire, ti preghiamo di aprire una *issue* o una *pull request* con le tue proposte o modifiche.
