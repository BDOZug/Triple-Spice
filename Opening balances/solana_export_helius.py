import requests
import csv
import json
import os
from datetime import datetime

# 🔐 Helius API Key
API_KEY = "a6101a02-6a80-45a5-ba0d-bf462cc9e166"
BASE_URL = f"https://api.helius.xyz/v0/addresses"
TOKENLIST_FILE = "Opening balances/tokenlist.json"

# ✅ Vollständige Wallet-Liste
wallets = [
    "YWmErgPSqc6rshcibxtgeLxDhgfs88MuuuJobd8exRH",
    "9JjQqHGuAXdk5UmEMvGeRuT2TtGvFdsexnE4wJeTwQp1",
    "ZG98FUCjb8mJ824Gbs6RsgVmr1FhXb2oNiJHa2dwmPd",
    "GDFsGLuJNT3SuDauKmvLpHm9DMNkwWrsN574gvrgnzk3",
    "6Su3CvAxazKcjQLRBJyMVbToM9zdT12VnY7pdj2NEAXH",
    "572baVHC2MxXeNQfqtDsjYdHqeGABmquvGD4fc57Ra8M",
    "6FkBcUcQcW45A6Q2zu6dniFNTg9x3zzzRYUAhgwJ4dc4",
    "D316VNcwiZBkpmtzSh63GH5j9xMdkGnutUoSMeFZdMCC",
    "95g7htdVvYkLLPLVW8CoJGPTRsVjKiMMW1K6MDbNfGF1",
    "2Ucp5f13wYycJdtfJHLVcdtPUDJqXFvUxCdXCNrmkC8P",
    "83Vz1jMgh1yAm7CzPpxkyVCUh5zc63LrrYNUkP2sQjbA",
    "91kg3MxN9gXdAW3YCsBdqJ2etuf3WoQzCfUqMzupuk7e",
    "GLapwXf7kZQBWp9dMZH7k5TcdPHprrhkCpN3BsLLJ2pN",
    "2fV9kPRSdCvCpNdcLU6Cemtvf7E22eddcnxAhjFaohqg",
    "6EzG2SLsD5Gd9HFqQW3iSMRLJJfPDkzE8LSwNb3aktBz",
    "5KuVn3Ww4oNd16R763oPZsD4TnpFHrr2TDRUQHZvjMEj",
    "Jvuzwu4dTSBgdKWeJjdhHDpz8XEkMQqFhfi7ePY7kzv",
    "6BSxVeqT3bcjYW8jFjxr2Df5kf4BoGefWaeJAuEpKLJX",
    "84DGj4Qpypcaa5uxdzphYzkutEUTvxLWSuWq3BoJLxkp",
    "87q5VhRAC8L2WX9gLwiigbHXMkdwU56cjGkBsPtUrncB",
    "CXZinB62qBAGJpMymVSrE4oi6jy85ZUmGdWGMsECf9bN",
    "GViJHLkWt12RcR6QkZBVybWzeG6g31ZHwRz2MCwNtWee",
    "FDcnoqz44hqPQqntWnpjPmzaynasCrMz81EDTWffgBGT",
    "4mNSrPhWCEUuCH3L4LMfeyiNyDBvJcFVU1PwYpybnyhJ",
    "HHiYxeuMq27kNmjD3zGj1mo6BBUhG8btRceq2p8iAv9P",
    "HvDzh6pzvjukAFUSajhkFgumhMLCUMjhMdFABbuc9YqL"
]

# 📦 Token-Registry laden
def load_token_registry():
    try:
        with open(TOKENLIST_FILE, "r") as f:
            registry = json.load(f)
            return {
                token["address"]: {
                    "name": token["name"],
                    "symbol": token["symbol"]
                }
                for token in registry["tokens"]
            }
    except FileNotFoundError:
        print(f"❌ Fehler: {TOKENLIST_FILE} nicht gefunden.")
        return {}

token_registry = load_token_registry()

# 🔍 Metadaten für Token ergänzen
def lookup_token_metadata(mint):
    return token_registry.get(mint, {"name": "Unknown", "symbol": "N/A"})

# 📡 Token-Balances via Helius API
def get_token_balances(wallet_address):
    url = f"{BASE_URL}/{wallet_address}/balances?api-key={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Fehler bei {wallet_address}: {response.status_code}")
        return []

    data = response.json()
    balances = []

    # ✅ Native SOL einfügen
    sol_raw = data.get("nativeBalance", 0)
    sol_amount = int(sol_raw) / 1e9
    balances.append({
        "wallet": wallet_address,
        "token_name": "Solana",
        "symbol": "SOL",
        "amount": sol_amount,
        "decimals": 9,
        "mint": "native"
    })

    # ✅ SPL Tokens einfügen
    for token in data.get("tokens", []):
        mint = token["mint"]
        amount = token["amount"] / (10 ** token["decimals"])
        meta = lookup_token_metadata(mint)
        name = token.get("tokenName") or meta["name"]
        symbol = token.get("symbol") or meta["symbol"]

        balances.append({
            "wallet": wallet_address,
            "token_name": name,
            "symbol": symbol,
            "amount": amount,
            "decimals": token["decimals"],
            "mint": mint
        })

    return balances

# 💾 Speichern in CSV
def export_to_csv(data):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S_UTC")
    filename = f"Opening balances/solana_token_balances_{timestamp}.csv"
    os.makedirs("Opening balances", exist_ok=True)
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["wallet", "token_name", "symbol", "amount", "decimals", "mint"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"✅ CSV gespeichert: {filename}")

# ▶ Hauptfunktion
def main():
    all_balances = []
    for wallet in wallets:
        print(f"🔍 Verarbeite {wallet}")
        balances = get_token_balances(wallet)
        all_balances.extend(balances)
    export_to_csv(all_balances)

if __name__ == "__main__":
    main()
