import requests
import pandas as pd
import time

# === KONFIGURATION ===
RPC_URL = "https://mainnet.helius-rpc.com/?api-key=a6101a02-6a80-45a5-ba0d-bf462cc9e166"
WALLET_CSV = "BALANCE CHECKER/walletAddress.csv"
CSV_DATEI = "BALANCE CHECKER/Tripe Spice AG transactions.csv"
EXPORT_DATEI = "BALANCE CHECKER/wallet_balances_compare_allwallets.csv"

# === Manuell gepflegte Symbol-Liste für bekannte SPL-Tokens ===
TOKEN_MINTS = {
    "So11111111111111111111111111111111111111112": "WSOL",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERz8Nu9Q8p8tEQQ3QSvWWtFkYwD8FSVhSJ": "USDT",
    "DezXhCz8rSQR3w9NCMGU4zoBZTq9tW7v6wJf3XZC4fXP": "BONK"
}
TOKENS = ['SOL', 'WSOL', 'USDC', 'USDT', 'BONK']


def get_wallet_balances(wallet_address):
    headers = {"Content-Type": "application/json"}

    # === 1. SOL-Balance ===
    sol = 0.0
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [wallet_address]
        }
        r = requests.post(RPC_URL, json=payload, headers=headers)
        sol = r.json().get("result", {}).get("value", 0) / 1e9
    except Exception as e:
        print(f"  ⚠️ Fehler bei SOL für {wallet_address}: {e}")

    # === 2. SPL Tokens ===
    spl_tokens = {sym: 0.0 for sym in TOKENS if sym != "SOL"}
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet_address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"}
            ]
        }
        r = requests.post(RPC_URL, json=payload, headers=headers)
        r.raise_for_status()
        accounts = r.json().get("result", {}).get("value", [])

        for acc in accounts:
            try:
                info = acc["account"]["data"]["parsed"]["info"]
                mint = info["mint"]
                ui_amount = float(info["tokenAmount"]["uiAmount"])
                symbol = TOKEN_MINTS.get(mint)
                if symbol:
                    spl_tokens[symbol] += ui_amount
            except Exception as inner:
                print(f"    ⚠️ Fehler bei Token-Parsing in Wallet {wallet_address}: {inner}")
    except Exception as e:
        print(f"  ⚠️ Fehler bei SPL-Tokens für {wallet_address}: {e}")

    spl_tokens["SOL"] = sol
    return spl_tokens


# === WALLET-LISTE ===
wallet_df = pd.read_csv(WALLET_CSV)
wallet_col = [c for c in wallet_df.columns if c.lower() == "walletaddress"]
wallet_column = wallet_col[0]
wallets = wallet_df[wallet_column].dropna().unique().tolist()

# === TRANSAKTIONSDATEN ===
df = pd.read_csv(CSV_DATEI)
df = df[df['chain'].str.lower() == 'solana']
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['lastSync'] = pd.to_datetime(df['lastSync'], errors='coerce')
latest_sync = df['lastSync'].dropna().max()
df_filtered = df[df['date'] <= latest_sync]
grouped = df_filtered.groupby([wallet_column, 'token'])['amount'].sum().unstack().fillna(0)
wallet_lastsync = df.groupby(wallet_column)['lastSync'].max().astype(str)

# === VERGLEICH ===
results = []
all_symbols = set(grouped.columns.tolist())

for idx, wallet in enumerate(wallets, start=1):
    print(f"[{idx}/{len(wallets)}] Prüfe Wallet: {wallet}")
    row = {"Wallet": wallet}

    balances = get_wallet_balances(wallet)
    all_symbols.update(balances.keys())

    for token in sorted(all_symbols):
        csv_val = grouped.loc[wallet, token] if wallet in grouped.index and token in grouped.columns else 0.0
        chain_val = balances.get(token, 0.0)
        diff = chain_val - csv_val
        row[f"{token}_Mainnet"] = round(chain_val, 6)
        row[f"{token}_CSV"] = round(csv_val, 6)
        row[f"{token}_Diff"] = round(diff, 6)
        print(f"    {token}: Mainnet = {chain_val:.6f}, CSV = {csv_val:.6f}, Diff = {diff:.6f}")

    sync_str = wallet_lastsync.get(wallet, '')
    sync_dt = pd.to_datetime(sync_str)
    row["Last Sync"] = sync_dt.strftime("%Y-%m-%d %H:%M:%S UTC") if not pd.isna(sync_dt) else ""
    results.append(row)
    time.sleep(0.2)

# === EXPORT ===
df_result = pd.DataFrame(results)
df_result.to_csv(EXPORT_DATEI, index=False)
print(f"\n✅ Exportiert nach {EXPORT_DATEI}")
