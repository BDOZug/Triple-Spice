import json
import csv
from datetime import datetime

INPUT_FILE = "ton_transactions.json"
OUTPUT_FILE = "ton_transactions.csv"
MY_WALLET = "UQBU5xsozZyIqlrE5X-imhjfLZkS5hZXdqI693I9ERbGoR4p"

def load_transactions(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def convert_to_breezing_format(transactions):
    rows = []

    for tx in transactions:
        tx_id = tx["transaction_id"]["hash"]
        timestamp = datetime.utcfromtimestamp(tx["utime"]).strftime("%Y-%m-%d %H:%M:%S")
        fee = int(tx.get("fee", "0")) / 1e9  # Convert nanoTON to TON
        direction = "out" if tx.get("in_msg", {}).get("source") == MY_WALLET else "in"
        token = "TON"
        fee_token = "TON"
        type_ = "transfer"

        # Default values
        amount = 0
        wallet_from = ""
        wallet_to = ""

        # INCOMING
        if direction == "in":
            amount = int(tx.get("in_msg", {}).get("value", 0)) / 1e9
            wallet_from = tx.get("in_msg", {}).get("source", "")
            wallet_to = MY_WALLET

        # OUTGOING
        elif direction == "out":
            out_msgs = tx.get("out_msgs", [])
            for msg in out_msgs:
                amount = int(msg.get("value", 0)) / 1e9
                wallet_from = MY_WALLET
                wallet_to = msg.get("destination", "")

                rows.append([
                    timestamp, tx_id, direction, token, fee_token,
                    amount, "", fee, wallet_from, wallet_to, type_
                ])
            continue  # already added each outgoing message as a row

        # One row for non-split txs (usually incoming)
        rows.append([
            timestamp, tx_id, direction, token, fee_token,
            amount, "", fee, wallet_from, wallet_to, type_
        ])

    return rows

def write_csv(rows, filename):
    header = [
        "date", "transactionId", "direction", "token", "feeToken",
        "amount", "amountFiat", "feeFiat", "walletFrom", "walletTo", "type"
    ]
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

if __name__ == "__main__":
    transactions = load_transactions(INPUT_FILE)
    csv_rows = convert_to_breezing_format(transactions)
    write_csv(csv_rows, OUTPUT_FILE)
    print(f"✅ {len(csv_rows)} Zeilen nach '{OUTPUT_FILE}' geschrieben.")
