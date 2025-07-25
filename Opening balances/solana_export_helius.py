import requests
import csv
import json
from datetime import datetime

API_KEY = "a6101a02-6a80-45a5-ba0d-bf462cc9e166"
BASE_URL = f"https://api.helius.xyz/v0/addresses"
TOKENLIST_FILE = "tokenlist.json"

# Wallets (wie gehabt)
wallets = [
    "YWmErgPSqc6rshcibxtgeLxDhgfs88MuuuJobd8exRH",
    "9JjQqHGuAXdk5UmEMvGeRuT2TtGvFdsexnE4wJeTwQp1",
    "ZG98FUCjb8mJ824Gbs6RsgVmr1FhXb2oNiJHa2dwmPd",
    "GDFsGLuJNT3SuDauKmvLpHm9DMNkwWrsN574gvrgnzk3",
    # ... (alle anderen)
]

# 🔍 Schritt 1: Lade Token Registry
def load_token_registry():
    try:
        with open(TOKENLIST_FILE, "r") as f:
            registry = json.load(f)
            token_map = {
                token["address"]: {
                    "name": token["name"],
                    "symbol": token["symbol"]
                }
                for token in registry["tokens"]
            }
            return token_map
    except FileNotFoundError:
        print(f"Fehler: {TOKENLIST_FILE} nicht gefunden.")
        return {}

token_registry = load_token_registry()

# 🔄 Schritt 2: Token-Metadaten ergänzen
def lookup_token_metadata(mint):
    return token_registry.get(mint, {"name": "Unknown", "symbol": "N/A"})

# 🔄 Schritt 3: Token-Balances via Helius API
def get_token_balances(wallet_address):
    url = f"{BASE_URL}/{wallet_address}/balances?api-key={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Fehler bei {wallet_address}: {response.status_code}")
        return []

    data = response.json()
    balances = []

    for token in data.get("tokens", []):
        mint = token["mint"]
        amount = token["amount"] / (10 ** token["decimals"])
        name = token.get("tokenName") or lookup_token_metadata(mint)["name"]
        symbol = token.get("symbol") or lookup_token_metadata(mint)["symbol"]

        balances.append({
            "wallet": wallet_address,
            "token_name": name,
            "symbol": symbol,
            "amount": amount,
            "decimals": token["decimals"],
            "mint": mint
        })

    return balances

# 📝 Schritt 4: CSV schreiben
def export_to_csv(data):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"solana_token_balances_{timestamp}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["wallet", "token_name", "symbol", "amount", "decimals", "mint"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"Gespeichert in: {filename}")

# ▶ Hauptablauf
def main():
    all_balances = []
    for wallet in wallets:
        print(f"Verarbeite {wallet}")
        balances = get_token_balances(wallet)
        all_balances.extend(balances)
    export_to_csv(all_balances)

if __name__ == "__main__":
    main()
