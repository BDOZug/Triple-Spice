import requests
import json
import time

WALLET = "UQBU5xsozZyIqlrE5X-imhjfLZkS5hZXdqI693I9ERbGoR4p"
API_URL = "https://toncenter.com/api/v2/getTransactions"
LIMIT = 50
MAX_PAGES = 20
RETRY_COUNT = 3
RETRY_DELAY = 5

def fetch_transactions(wallet, limit=50, max_pages=10):
    transactions = []
    last_lt = None
    last_hash = None

    for page in range(max_pages):
        params = {
            "address": wallet,
            "limit": limit,
            "archival": "true"  # wichtig für historische Daten
        }

        if last_lt and last_hash:
            params["lt"] = last_lt
            params["hash"] = last_hash
        else:
            params["to_lt"] = 0

        for attempt in range(RETRY_COUNT):
            try:
                print(f"🔄 Seite {page + 1}, Versuch {attempt + 1}...")
                resp = requests.get(API_URL, params=params)
                print(f"➡️  Anfrage an: {resp.url}")
                resp.raise_for_status()
                chunk = resp.json().get("result", [])
                break  # Erfolgreich -> raus aus Retry-Loop
            except requests.exceptions.HTTPError as e:
                print(f"❌ HTTPError ({resp.status_code}): {e}")
                if resp.status_code >= 500:
                    print("⏳ Serverfehler – neuer Versuch...")
                    time.sleep(RETRY_DELAY)
                else:
                    print("❌ Clientfehler – Abbruch.")
                    return transactions
            except requests.exceptions.RequestException as e:
                print(f"❌ Netzwerkfehler: {e} – neuer Versuch in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
        else:
            print("🚫 Max. Wiederholungen erreicht – Abbruch.")
            break

        if not chunk:
            print("✅ Keine weiteren Transaktionen.")
            break

        transactions.extend(chunk)
        last_tx = chunk[-1]["transaction_id"]
        last_lt = last_tx["lt"]
        last_hash = last_tx["hash"]

        if len(chunk) < limit:
            print("✅ Weniger als 'limit' Transaktionen erhalten – fertig.")
            break

    return transactions

def write_json(obj, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    txs = fetch_transactions(WALLET, LIMIT, MAX_PAGES)
    print(f"✅ Insgesamt {len(txs)} Transaktionen abgerufen.")
    write_json(txs, "ton_transactions.json")
    print("💾 Gespeichert in 'ton_transactions.json'")
