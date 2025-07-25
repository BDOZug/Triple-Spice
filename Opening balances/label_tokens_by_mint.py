import csv
import json
from datetime import datetime

# 📁 Datei- und Pfad-Konfiguration
INPUT_FILE = "Opening balances/solana_token_balances_2025-07-27_19-10-31_UTC.csv"
TOKENLIST_FILE = "Opening balances/tokenlist.json"
OUTPUT_FILE = "Opening balances/labeled_balances_output.csv"

# 🔍 CSV einlesen und Mint-Adressen extrahieren
def load_mints_from_csv(path):
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        mint_list = [row["mint"] for row in rows if "mint" in row]
        return mint_list, rows

# 🧠 Lade Token-Metadaten
def load_token_metadata(tokenlist_path):
    with open(tokenlist_path, "r") as f:
        tokenlist = json.load(f)
        metadata = {
            token["address"]: {
                "token_name": token["name"],
                "symbol": token["symbol"]
            }
            for token in tokenlist["tokens"]
        }
        return metadata

# 🏷 Mint-Adressen mit Metadaten mappen
def label_mints(rows, metadata):
    labeled = []
    for row in rows:
        mint = row.get("mint")
        token_info = metadata.get(mint, {"token_name": "Unknown", "symbol": "N/A"})
        row["token_name"] = token_info["token_name"]
        row["symbol"] = token_info["symbol"]
        labeled.append(row)
    return labeled

# 📝 Schreibe gelabelte Daten in CSV (dynamisch)
def write_labeled_csv(rows, output_file, selected_fields=None):
    if not rows:
        print("⚠️ Keine Daten zum Schreiben vorhanden.")
        return

    # Felder dynamisch oder gezielt wählen
    fieldnames = selected_fields if selected_fields else list(rows[0].keys())

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Nur relevante Felder schreiben
            filtered_row = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(filtered_row)

# ▶ Hauptfunktion
def main():
    print(f"🔍 Lese Mint-Adressen aus {INPUT_FILE}...")
    mint_list, rows = load_mints_from_csv(INPUT_FILE)

    print(f"🔍 Hole Token-Metadaten für {len(mint_list)} Mints...")
    mint_metadata = load_token_metadata(TOKENLIST_FILE)

    print("✅ Mapping abgeschlossen. Schreibe neues CSV...")
    labeled_rows = label_mints(rows, mint_metadata)

    # Optional: nur bestimmte Spalten im Output
    selected_fields = ["wallet", "token_name", "symbol", "amount", "mint"]  # oder None für alle
    write_labeled_csv(labeled_rows, OUTPUT_FILE, selected_fields)

    print(f"📁 Datei gespeichert: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
