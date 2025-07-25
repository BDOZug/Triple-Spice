# Wallet Balance Checker (Solana)

Dieses Repository stellt ein Python-Skript bereit, das die Token-Bestände mehrerer Wallets auf der Solana-Blockchain mit berechneten Transaktionsdaten aus einer CSV-Datei abgleicht. Ziel ist es, etwaige Differenzen pro Token und Wallet sichtbar zu machen.

## Features

* Unterstützt Tokens: **SOL, WSOL, USDC, USDT, BONK**
* Verwendet direktes RPC-Querying über `solana-py`
* Verarbeitet historische Transaktionen aus Breezing.io
* Berechnet für jede Wallet:

  * Aktuelle On-Chain-Bestände
  * CSV-basierte (rechnerische) Bestände bis zum letzten Sync-Zeitpunkt
  * Differenzen zwischen beiden
* Exportiert eine CSV-Datei mit allen Ergebnissen

## Anforderungen

* Python >= 3.9
* Abhängige Pakete (siehe `requirements.txt`):

  ```bash
  pip install pandas solana solders
  ```

## Dateien

* `export.py` – Hauptskript für die Balance-Abstimmung
* `Tripe Spice AG (V2)-transactions-*.csv` – Transaktionsdaten aus Breezing
* `walletAddress.csv` – CSV-Datei mit einer Spalte `walletAddress`
* `wallet_balances_compare_allwallets.csv` – Exportierter Bericht nach Ausführung

## Verwendung

1. Stelle sicher, dass die folgenden Dateien im Projektordner vorhanden sind:

   * Transaktions-CSV von Breezing (`Tripe Spice AG (V2)-transactions-....csv`)
   * Walletliste (`walletAddress.csv` mit Spalte `walletAddress`)

2. Führe das Skript aus:

   ```bash
   python export.py
   ```

3. Ergebnis:

   * Die Datei `wallet_balances_compare_allwallets.csv` wird generiert und enthält:

     * Wallet-Adresse
     * On-Chain-Balance je Token
     * CSV-basierte Berechnung je Token
     * Differenz
     * Letzter Sync-Zeitpunkt

## Hinweise

* Das Skript verwendet das öffentliche Solana-Mainnet RPC-Endpoint. Für umfangreiche Wallet-Listen empfiehlt sich ein eigener RPC-Anbieter (z.B. QuickNode, Triton, Helius).
* Die Transaktionsdaten müssen korrekt nach Chain und Token benannt sein (`solana`, `USDC`, `SOL`, ...).

## Lizenz

MIT License

---

Bei Fragen oder Erweiterungswünschen: gerne Issue erstellen oder Pull Request einreichen.
