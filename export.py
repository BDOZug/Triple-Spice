import pandas as pd
from solders.pubkey import Pubkey as SoldersPubkey
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts
from solders.pubkey import Pubkey as PublicKey

# === KONFIGURATION ===
CSV_DATEI = "Tripe Spice AG (V2)-transactions-7_24_2025.csv"
WALLET_CSV = "walletAddress.csv"
RPC_URL = "https://api.mainnet-beta.solana.com"
TOKEN_MINTS = {
    "So11111111111111111111111111111111111111112": "WSOL",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERQ1DPFjAEyDWpKzQUy5cC59yGZfzbQ7e": "USDT",
    "DezXZX3wAqKdugYUtLwWjFVXocF6vRy7vGHvdZADvw5S": "BONK"
}
TOKENS = ['SOL', 'WSOL', 'USDC', 'USDT', 'BONK']
SPL_TOKEN_PROGRAM_ID = PublicKey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")

# === 1. Wallet-Liste laden ===
wallet_df = pd.read_csv(WALLET_CSV)
wallet_column_name = [col for col in wallet_df.columns if col.lower() == 'walletaddress']
if not wallet_column_name:
    raise KeyError("Spalte 'walletAddress' nicht gefunden im Wallet CSV.")
wallet_column = wallet_column_name[0]
wallets = wallet_df[wallet_column].dropna().unique().tolist()

# === 2. CSV-Daten laden ===
df = pd.read_csv(CSV_DATEI)
df = df[df['chain'].str.lower() == 'solana']
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['lastSync'] = pd.to_datetime(df['lastSync'], errors='coerce')
latest_sync = df['lastSync'].dropna().max()

# === 3. Transaktionen bis Stichtag zusammenfassen ===
df_filtered = df[df['date'] <= latest_sync]
grouped = df_filtered.groupby([wallet_column, 'token'])['amount'].sum().unstack().fillna(0)
wallet_lastsync = df.groupby(wallet_column)['lastSync'].max().astype(str)

# === 4. RPC-Client vorbereiten ===
client = Client(RPC_URL)

# === 5. Vergleich durchführen ===
results = []
for wallet in wallets:
    row = {"Wallet": wallet}
    try:
        wallet_pubkey = PublicKey.from_string(wallet)
    except Exception as e:
        print(f"Fehler bei Wallet Pubkey für {wallet}: {e}")
        continue

    # On-chain SOL
    try:
        sol_resp = client.get_balance(wallet_pubkey)
        sol_amount = sol_resp.value / 1e9
    except Exception as e:
        print(f"Fehler bei SOL Balance für {wallet}: {e}")
        sol_amount = 0.0
    row['SOL_Mainnet'] = sol_amount

    # On-chain SPL
    spl_amounts = {sym: 0.0 for sym in TOKENS if sym != 'SOL'}
    try:
        opts = TokenAccountOpts(
            program_id=SPL_TOKEN_PROGRAM_ID,
            encoding="jsonParsed"
        )
        resp = client.get_token_accounts_by_owner(wallet_pubkey, opts=opts)
        for acc in resp.value:
            try:
                info = acc.account.data.parsed['info'] if isinstance(acc.account.data.parsed, dict) else acc.account.data['parsed']['info']
                mint = info['mint']
                amount = float(info['tokenAmount']['uiAmount'])
                symbol = TOKEN_MINTS.get(mint)
                if symbol:
                    spl_amounts[symbol] += amount
            except Exception as e:
                print(f"Fehler beim Parsen von SPL Token für {wallet}: {e}")
    except Exception as e:
        print(f"Fehler bei SPL Token Balance für {wallet}: {e}")

    # Alle Token vergleichen
    for token in TOKENS:
        csv_value = grouped.loc[wallet, token] if wallet in grouped.index and token in grouped.columns else 0.0
        chain_value = sol_amount if token == 'SOL' else spl_amounts[token]
        row[f"{token}_Mainnet"] = chain_value
        row[f"{token}_CSV"] = csv_value
        row[f"{token}_Diff"] = chain_value - csv_value

    # Letzter Sync-Zeitpunkt
    last_sync_str = wallet_lastsync.get(wallet, '')
    last_sync_dt = pd.to_datetime(last_sync_str)
    row["Last Sync"] = last_sync_dt.strftime("%Y-%m-%d %H:%M:%S UTC") if not pd.isna(last_sync_dt) else ""
    results.append(row)

# === 6. Exportieren ===
df_result = pd.DataFrame(results)
df_result.to_csv("wallet_balances_compare_allwallets.csv", index=False)
print("Exportiert nach wallet_balances_compare_allwallets.csv")
