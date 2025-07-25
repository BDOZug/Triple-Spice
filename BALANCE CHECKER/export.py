import requests
import pandas as pd
import time

# === BASIS-PFAD ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DATEI = os.path.join(BASE_DIR, "Tripe Spice AG transactions.csv")
WALLET_CSV = os.path.join(BASE_DIR, "walletAddress.csv")

# === KONFIGURATION ===
RPC_URL = "https://mainnet.helius-rpc.com/?api-key=a6101a02-6a80-45a5-ba0d-bf462cc9e166"
WALLET_CSV = "BALANCE CHECKER/walletAddress.csv"
CSV_DATEI = "BALANCE CHECKER/Tripe Spice AG transactions.csv"
EXPORT_DATEI = "BALANCE CHECKER/wallet_balances_compare_allwallets.csv"

# Token Mappings
TOKEN_MINTS = {
    "So11111111111111111111111111111111111111112": "WSOL",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERz8Nu9Q8p8tEQQ3QSvWWtFkYwD8FSVhSJ": "USDT",
    "DezXhCz8rSQR3w9NCMGU4zoBZTq9tW7v6wJf3XZC4fXP": "BONK"
}
TOKENS = ['SOL', 'WSOL', 'USDC', 'USDT', 'BONK']


# === FUNKTION: Wallet-Balances via Helius ===
def get_wallet_balances(wallet_address):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet_address]
    }
    sol = 0.0
    try:
        r = requests.post(RPC_URL, json=payload, headers=headers)
        r.raise_for_status()
        result = r.json().get("result", {})
        sol = result.get("value", 0) / 1e9
    except Exception as e:
        print(f"  ⚠️ Fehler bei SOL für {wallet_address}: {e}")

    # SPL Tokens via Helius-Methode
    spl_tokens = {sym: 0.0 for sym in TOKENS if sym != "SOL"}
    try:
        token_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet_address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"}
            ]
        }
        resp = requests.post(RPC_URL, json=token_payload, headers=headers).json()
        accounts = resp.get("result", {}).get("value", [])
        for acc in accounts:
            info = acc["account"]["data"]["parsed"]["info"]
            mint = info["mint"]
            ui_amount = float(info["tokenAmount"]["uiAmount"])
            symbol = TOKEN_MINTS.get(mint)
            if symbol:
                spl_tokens[symbol] += ui_amount
    except Exception as e:
        print(f"  ⚠️ Fehler bei SPL-Tokens für {wallet_address}: {e}")

    return sol, spl_tokens


# === WALLET CSV einlesen ===
wallet_df = pd.read_csv(WALLET_CSV)
wallet_col = [c for c in wallet_df.columns if c.lower() == "walletaddress"]
if not wallet_col:
    raise Exception("Spalte 'walletAddress' nicht gefunden!")
wallet_column = wallet_col[0]
wallets = wallet_df[wallet_column].dropna().unique().tolist()

# === Transaktionsdaten laden ===
df = pd.read_csv(CSV_DATEI)
df = df[df['chain'].str.lower() == 'solana']
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['lastSync'] = pd.to_datetime(df['lastSync'], errors='coerce')
latest_sync = df['lastSync'].dropna().max()
df_filtered = df[df['date'] <= latest_sync]
grouped = df_filtered.groupby([wallet_column, 'token'])['amount'].sum().unstack().fillna(0)
wallet_lastsync = df.groupby(wallet_column)['lastSync'].max().astype(str)

# === Wallets durchgehen ===
results = []
for idx, wallet in enumerate(wallets, start=1):
    print(f"[{idx}/{len(wallets)}] Prüfe Wallet: {wallet}")
    row = {"Wallet": wallet}

    sol_amount, spl_amounts = get_wallet_balances(wallet)

    # Vergleich mit CSV-Werten
    for token in TOKENS:
        csv_value = grouped.loc[wallet, token] if wallet in grouped.index and token in grouped.columns else 0.0
        chain_value = sol_amount if token == "SOL" else spl_amounts.get(token, 0.0)
        diff = chain_value - csv_value
        row[f"{token}_Mainnet"] = chain_value
        row[f"{token}_CSV"] = csv_value
        row[f"{token}_Diff"] = diff
        print(f"    {token}: Mainnet = {chain_value:.6f}, CSV = {csv_value:.6f}, Diff = {diff:.6f}")

    last_sync_str = wallet_lastsync.get(wallet, '')
    last_sync_dt = pd.to_datetime(last_sync_str)
    row["Last Sync"] = last_sync_dt.strftime("%Y-%m-%d %H:%M:%S UTC") if not pd.isna(last_sync_dt) else ""
    results.append(row)

    time.sleep(0.2)  # Rate-Limit-freundlich

# === Export CSV ===
df_result = pd.DataFrame(results)
df_result.to_csv(EXPORT_DATEI, index=False)
print(f"\n✅ Exportiert nach {EXPORT_DATEI}")
