import requests
import csv
from datetime import datetime

# ✅ Dein Helius API-Key
API_KEY = "a6101a02-6a80-45a5-ba0d-bf462cc9e166"
BASE_URL = "https://api.helius.xyz/v0/addresses"

# ✅ Liste der Wallets
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
    "5KuVn3hw4oNd16763oPZsD4TnpFhr2TDRUQHZvjMEj",
    "Jvuzwu4dTSBgdKWeJjdhHDpz8XEkMQqFhfi7ePY7kzv",
    "6BSxVeqT3bcjYW8jFjxr2Df5kf4BoGefWaeJAuEpKLJX",
    "84DGj4Qpypcaa5uxdzphYzkutEUTvxLWSuwq3BoJLxkp",
    "87q5VhRNAC8L2WX9gLwiigbHKbXMKdwU56cjGkBsPtUrnC",
    "CXZinB62qBAGJpMymVSrE4oi6j85ZUmGdWGMscECf9bN",
    "GViJHLkWt12RcR6QkZBVybWzeG6g31ZHwRz2MCwNtWee",
    "FDcnoqz44hqPQqntWnpjPmzaynasCrMz81EDTWffgBGT",
    "4mNSrPhWCEUuCH3L4LMfeyiNyDBvJcFVU1PwYpybnyhJ",
    "HHiYxeuMq27kNmjD3zGj1mo6BBUhG8btRceq2p8iAv9P",
    "HvDzh6pzvjukAFUSajhkFgumhMLCUMjhMdFABbuc9YqL",
]

# ✅ Nur diese Token-Symbole berücksichtigen
ALLOWED_SYMBOLS = {"USDC", "SOL", "BONK", "JUP", "WSOL", "USDT"}

# ✅ Tokenbestand einer Wallet abfragen
def get_filtered_tokens(wallet):
    url = f"{BASE_URL}/{wallet}/balances?api-key={API_KEY}"
    try:
        res = requests.get(url)
        if res.status_code != 200:
            print(f"❌ Fehler bei {wallet}: {res.status_code}")
            return []

        data = res.json()
        tokens = []
        for token in data.get("tokens", []):
            symbol = token.get("symbol", "").upper()
            if symbol in ALLOWED_SYMBOLS:
                amount = token["amount"] / (10 ** token["decimals"])
                tokens.append({
                    "wallet": wallet,
                    "symbol": symbol,
                    "amount": amount,
                    "decimals": token["decimals"],
                    "mint": token["mint"]
                })
        return tokens
    except Exception as e:
        print(f"❌ Fehler bei {wallet}: {e}")
        return []

# ✅ CSV schreiben
def export_to_csv(data):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S_UTC")
    filename = f"filtered_balances_{timestamp}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["wallet", "symbol", "amount", "decimals", "mint"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"✅ CSV gespeichert: {filename}")

# ✅ Hauptfunktion
def main():
    all_data = []
    for wallet in wallets:
        print(f"🔍 Verarbeite Wallet: {wallet}")
        tokens = get_filtered_tokens(wallet)
        all_data.extend(tokens)
    export_to_csv(all_data)

if __name__ == "__main__":
    main()
