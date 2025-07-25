import json, csv
from datetime import datetime, timezone

IN_FILE = "ton_transactions.json"
OUT_FILE = "ton_events.csv"

def load_json(f):
    return json.load(open(f, encoding="utf-8"))

def convert_events(txs):
    rows = []
    for tx in txs:
        ts = datetime.fromtimestamp(tx.get("utime"), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        txh = tx["transaction_id"]["hash"]
        in_msg = tx.get("in_msg", {})
        from_addr = in_msg.get("source", "")
        to_addr = in_msg.get("destination", "")
        value_in = int(in_msg.get("value", 0)) / 1e9
        if value_in > 0:
            rows.append([ts, txh, "in", from_addr, to_addr, round(value_in, 9)])

        for m in tx.get("out_msgs", []):
            from_addr = m.get("source", "")
            to_addr = m.get("destination", "")
            value_out = int(m.get("value", 0)) / 1e9
            if value_out > 0:
                rows.append([ts, txh, "out", from_addr, to_addr, round(-value_out, 9)])

    return rows

def write_csv(rows, file):
    hdr = ["date", "txHash", "direction", "from", "to", "amount"]
    with open(file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(hdr)
        w.writerows(rows)
    print(f"✅ {len(rows)} event(s) exported to {file}")

if __name__ == "__main__":
    txs = load_json(IN_FILE)
    evs = convert_events(txs)
    write_csv(evs, OUT_FILE)
