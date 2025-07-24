import pandas as pd
from solders.pubkey import Pubkey as SoldersPubkey
from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts

# === KONFIGURATION ===
CSV_DATEI = "Tripe Spice AG (V2)-transactions-7_24_2025.csv"
RPC_URL = "https://api.mainnet-beta.solana.com"
TOKEN_MINTS = {
    "So11111111111111111111111111111111111111112": "WSOL",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC",
    "Es9vMFrzaCERQ1DPFjAEyDWpKzQUy5cC59yGZfzbQ7e": "USDT",
    "DezXZX3wAqKdugYUtLwWjFVXocF6vRy7vGHvdZADvw5S": "BONK"
}
SPL_TOKEN_PROGRAM_ID = SoldersPubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")

# === 1. CSV-Daten laden ===
df = pd.read_csv(CSV_DATEI)
df = df[df['chain'] == 'solana']
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['lastSync'] = pd.to_datetime(df['lastSync'], errors='coerce')
latest_sync = df['lastSync'].dropna().max()
wallets = df['walletAddress'].dropna().unique().tolist()

# === 2. RPC-Client vorbereiten ===
client = Client(RPC_URL)

# === 3. Balances aus Transaktionsdaten berechnen ===
df_filtered = df[df['date'] <= latest_sync]
grouped = df_filtered.groupby(['walletAddress', 'token'])['amount'].sum().unstack().fillna(0)

# === 4. On-Chain-Balances vergleichen ===
results = []

for wallet_str in wallets:
    try:
        wallet = SoldersPubkey.from_string(wallet_str)
    except Exception as e:
        print(f"Fehler beim Parsen der Wallet-Adresse {wallet_str}: {e}")
        continue

    row = {"Wallet": wallet_str}

    # On-chain SOL
    try:
        sol_resp = client.get_balance(wallet)
        sol_amount = sol_resp.value / 1e9
        row['SOL_chain'] = sol_amount
    except Exception as e:
        print(f"Fehler bei SOL Balance für {wallet_str}: {e}")
        row['SOL_chain'] = 0

    # On-chain SPL
    try:
        resp = client.get_token_accounts_by_owner(
            wallet,
            TokenAccountOpts(
                program_id="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                encoding="jsonParsed"
            )
        )
        spl_amounts = {v: 0 for v in TOKEN_MINTS.values()}

        for acc in resp.value:
            try:
                info = acc.account.data.parsed['info']
                mint = info['mint']
                amount = float(info['tokenAmount']['uiAmount'])
                symbol = TOKEN_MINTS.get(mint)
                if symbol:
                    spl_amounts[symbol] += amount
                else:
                    print(f"Unbekannter Token Mint {mint} für {wallet_str}")
            except Exception as e:
                print(f"Fehler beim Parsen von SPL Account für {wallet_str}: {e}")

        for sym in spl_amounts:
            row[f"{sym}_chain"] = spl_amounts[sym]

    except Exception as e:
        print(f"Fehler bei SPL Token Balance für {wallet_str}: {e}")
        for sym in TOKEN_MINTS.values():
            row[f"{sym}_chain"] = 0

    # CSV-berechnete Balances einfügen und Differenz berechnen
    for sym in ['SOL', 'WSOL', 'USDC', 'USDT', 'BONK']:
        csv_value = grouped.loc[wallet_str, sym] if wallet_str in grouped.index and sym in grouped.columns else 0
        chain_value = row.get(f"{sym}_chain", 0)
        row[f"{sym}_csv"] = csv_value
        row[f"{sym}_diff"] = chain_value - csv_value

    results.append(row)

# === 5. Exportieren ===
df_result = pd.DataFrame(results)
df_result.to_csv("wallet_balances_compare.csv", index=False)
print("Vergleich exportiert nach wallet_balances_compare.csv")
