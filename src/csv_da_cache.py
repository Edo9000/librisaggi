import json
import pandas as pd
import os

def esegui_post_processing(
    input_file: str,
    cache_file: str,
    output_file: str,
    output_confronto: str,
    output_sospetti: str = "prezzi_sospetti.csv"
):
    # === Carica CSV originale ===
    df = pd.read_csv(input_file, sep="\t")
    original_columns = df.columns.tolist()
    df["Prezzo_Originale"] = pd.to_numeric(df["Prezzo"], errors="coerce")
    df["ISBN"] = df["ISBN"].astype(str).str.strip()

    # === Carica cache ===
    def safe_load_cache(path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    cache = safe_load_cache(cache_file)

    # === Correggi prezzi eBay anomali ===
    def correggi_prezzi_ebay(prezzi):
        if not isinstance(prezzi, list) or len(prezzi) < 2:
            return prezzi
        primo = prezzi[0]
        altri = prezzi[1:]
        media_altri = sum(altri) / len(altri)
        if primo > media_altri * 1.5:
            return [primo]
        return prezzi

    def correggi_cache_ebay(cache):
        modificati = 0
        for key in list(cache.keys()):
            if key.endswith("_list_eBay"):
                originali = cache[key]
                corretti = correggi_prezzi_ebay(originali)
                if corretti != originali:
                    cache[key] = corretti
                    modificati += 1
        return modificati

    modificati = correggi_cache_ebay(cache)
    print(f"Correzioni applicate: {modificati} in cache")

    # === Funzione esterna mock per fallback
    def final_price_no_isbn_multiple(row):
        prices = row.get("Prezzi_eBay", [])
        if isinstance(prices, list) and prices:
            media = sum(prices) / len(prices)
            return round(media * 0.95, 2), "media_ebay"
        return row.get("Prezzo_Originale", None), "originale"

    # === Aggiorna prezzo per ogni riga
    def aggiorna_prezzo(row):
        isbn = row["ISBN"]
        titolo = str(row.get("Titolo", "")).strip()
        editore = str(row.get("Editore", "")).strip()
        anno = str(row.get("Anno di stampa", "")).strip()
        condizione = str(row.get("Condizioni", "")).strip().lower()
        chiave = f"{titolo} {editore} {anno}".strip()

        prezzi_abe = cache.get(f"{isbn}_list_AbeBooks") or cache.get(f"{chiave}_list_AbeBooks")
        prezzi_ebay_raw = cache.get(f"{chiave}_list_eBay")

        prezzi_pesati = []
        fonti = []
        note_extra = []

        if isbn and isbn.isdigit():
            prezzi_isbn_abe = cache.get(f"{isbn}_list_AbeBooks") or []
            prezzi_isbn_ebay = cache.get(f"{isbn}_list_eBay") or []

            if len(prezzi_isbn_abe) == 1:
                unico = prezzi_isbn_abe[0]
                prezzo_finale = int(round(unico * 1.10))
                row["Prezzo"] = prezzo_finale
                row["FontePrezzo"] = "AbeBooks (1 solo prezzo ISBN)"
                row["CondizioneUsata"] = condizione
                row["MoltiplicatoreCondizione"] = ""
                row["NoteModifica"] = "1 solo prezzo AbeBooks (ISBN), maggiorato del 10% — eBay ignorato"
                return row

            tutti_prezzi_isbn = list(prezzi_isbn_abe) + list(prezzi_isbn_ebay)

            if len(tutti_prezzi_isbn) >= 3:
                massimo = max(tutti_prezzi_isbn)
                tutti_prezzi_isbn.remove(massimo)
                note_extra.append("Prezzo massimo rimosso da fonti ISBN")
            if tutti_prezzi_isbn:
                prezzi_pesati.extend(tutti_prezzi_isbn)
                fonti.append("ISBN")

        if not prezzi_pesati:
            prezzi_abe = cache.get(f"{chiave}_list_AbeBooks")
            if isinstance(prezzi_abe, list) and prezzi_abe:
                if len(prezzi_abe) == 1:
                    unico = prezzi_abe[0]
                    prezzo_finale = int(round(unico * 1.10))
                    row["Prezzo"] = prezzo_finale
                    row["FontePrezzo"] = "AbeBooks (1 solo prezzo chiave)"
                    row["CondizioneUsata"] = condizione
                    row["MoltiplicatoreCondizione"] = ""
                    row["NoteModifica"] = "1 solo prezzo AbeBooks (chiave), maggiorato del 10% — eBay ignorato"
                    return row

                prezzi_clean = sorted(prezzi_abe)
                if len(prezzi_clean) > 1:
                    prezzi_clean.pop(0)
                    note_extra.append("Min AbeBooks rimosso (no ISBN)")
                prezzi_pesati.extend(prezzi_clean * 3)
                fonti.append("AbeBooks")

            prezzi_ebay_raw = cache.get(f"{chiave}_list_eBay")
            if isinstance(prezzi_ebay_raw, list) and prezzi_ebay_raw:
                usa_ebay = True
                if prezzi_abe:
                    media_abe = sum(prezzi_abe) / len(prezzi_abe)
                    media_ebay = sum(prezzi_ebay_raw) / len(prezzi_ebay_raw)
                    if media_ebay < media_abe * 0.6:
                        usa_ebay = False
                        note_extra.append("eBay ignorato (prezzi troppo bassi)")
                if usa_ebay:
                    prezzi_ebay_clean = sorted(prezzi_ebay_raw)
                    if len(prezzi_ebay_clean) > 1:
                        prezzi_ebay_clean.pop(0)
                        note_extra.append("Min eBay rimosso")
                    prezzi_pesati.extend(prezzi_ebay_clean)
                    fonti.append("eBay")

        if prezzi_pesati:
            if len(set(prezzi_pesati)) == 1:
                unico = prezzi_pesati[0]
                prezzo_finale = int(round(unico * 1.10))
                row["Prezzo"] = prezzo_finale
                row["FontePrezzo"] = "+".join(fonti)
                row["CondizioneUsata"] = ""
                row["MoltiplicatoreCondizione"] = ""
                row["NoteModifica"] = "Prezzo unico, maggiorato del 10%" + (" | " + "; ".join(note_extra) if note_extra else "")
                return row

            base_price = round(sum(prezzi_pesati) / len(prezzi_pesati) * 0.95, 2)
            moltiplicatori = {
                "perfetto (mint)": 1.05,
                "molto buono (very good)": 0.95,
                "buono (good)": 0.90,
                "mediocre (poor)": 0.85
            }
            moltiplicatore = moltiplicatori.get(condizione, 1.00)
            prezzo_finale = int(round(base_price * moltiplicatore))
            row["Prezzo"] = prezzo_finale
            row["FontePrezzo"] = "+".join(fonti)
            row["CondizioneUsata"] = condizione
            row["MoltiplicatoreCondizione"] = moltiplicatore
            row["NoteModifica"] = f"Fonte: {row['FontePrezzo']}, moltiplicato per {moltiplicatore}" + (" | " + "; ".join(note_extra) if note_extra else "")
            return row

        row["Prezzo"] = row.get("Prezzo_Originale", None)
        row["FontePrezzo"] = ""
        row["CondizioneUsata"] = condizione
        row["MoltiplicatoreCondizione"] = ""
        row["NoteModifica"] = "Nessuna modifica"
        return row

    # === Applica aggiornamento prezzi
    df = df.apply(aggiorna_prezzo, axis=1)

    # === Applica limite ±20%
    def clamp_price(row):
        orig = row["Prezzo_Originale"]
        new = row["Prezzo"]
        if pd.notnull(orig) and pd.notnull(new):
            minp = round(orig * 0.8, 2)
            maxp = round(orig * 1.2, 2)
            return max(min(new, maxp), minp)
        return new

    df["Prezzo"] = df.apply(clamp_price, axis=1)

    # === Isola i casi sospetti
    df["Prezzo_Aggiornato_Temporaneo"] = pd.to_numeric(df["Prezzo"], errors="coerce")
    df["DifferenzaAssoluta"] = df["Prezzo_Aggiornato_Temporaneo"] - df["Prezzo_Originale"]
    df["DifferenzaRelativa"] = df["DifferenzaAssoluta"].abs() / df["Prezzo_Originale"]

    df_sospetti = df[
        (df["Prezzo_Originale"] > 0) &
        (df["Prezzo_Aggiornato_Temporaneo"] > 100) &
        (df["DifferenzaRelativa"] >= 0.4)
    ].copy()

    df.loc[df_sospetti.index, "Prezzo"] = df.loc[df_sospetti.index, "Prezzo_Originale"]

    # === Genera confronto prezzi
    df_confronto = df.copy()
    df_confronto["Prezzo_Originale"] = pd.to_numeric(df_confronto["Prezzo_Originale"], errors="coerce")
    df_confronto["Prezzo_Aggiornato"] = pd.to_numeric(df_confronto["Prezzo"], errors="coerce")
    df_confronto["Differenza"] = df_confronto["Prezzo_Aggiornato"] - df_confronto["Prezzo_Originale"]

    def percentuale_con_segno(row):
        try:
            base = row["Prezzo_Originale"]
            diff = row["Differenza"]
            if pd.notnull(base) and base != 0:
                perc = (diff / base) * 100
                return f"{'+' if perc > 0 else ''}{round(perc, 2)}%"
        except:
            pass
        return None

    df_confronto["Variazione_%"] = df_confronto.apply(percentuale_con_segno, axis=1)

    confronto_cols = [
        "IDLibro", "Titolo", "ISBN",
        "Prezzo_Originale", "Prezzo_Aggiornato", "Differenza", "Variazione_%",
        "FontePrezzo", "CondizioneUsata", "MoltiplicatoreCondizione", "NoteModifica"
    ]

    df["Prezzo"] = df["Prezzo"].apply(lambda x: str(int(x)) if pd.notnull(x) and float(x).is_integer() else x)
    df_confronto["Prezzo_Aggiornato"] = df_confronto["Prezzo_Aggiornato"].apply(
        lambda x: str(int(x)) if pd.notnull(x) and float(x).is_integer() else x
    )

    df_confronto[confronto_cols].to_csv(output_confronto, index=False, sep="\t")
    df = df[original_columns]
    df.to_csv(output_file, index=False, sep="\t")

    df_sospetti["Prezzo_Calcolato"] = df_sospetti["Prezzo_Aggiornato_Temporaneo"]
    df_sospetti["Diff_%"] = df_sospetti["DifferenzaRelativa"].apply(lambda x: f"{round(x * 100, 2)}%")
    sospetti_cols = original_columns + ["Prezzo_Calcolato", "Diff_%"]
    df_sospetti[sospetti_cols].to_csv(output_sospetti, sep="\t", index=False)

    return output_file, output_confronto, output_sospetti
