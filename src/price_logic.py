
def final_price_no_isbn_multiple(row):
    amz_prices = row.get("Prezzi_Amazon", [])
    ebay_prices = row.get("Prezzi_eBay", [])

    all_prices = amz_prices + ebay_prices
    if not all_prices:
        try:
            base = float(row["Prezzo"])
            return round(base * 1.10, 2), True
        except:
            return None, True
    if len(all_prices) <= 2:
        return max(all_prices), False

    total, weight_sum = 0, 0
    for price in amz_prices:
        total += price * 0.8
        weight_sum += 0.8
    for price in ebay_prices:
        total += price * 0.2
        weight_sum += 0.2
    return round(total / weight_sum, 2), False
