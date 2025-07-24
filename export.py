import pandas as pd
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# === KONFIGURATION ===
CSV_DATEI = "daten.csv"  # Stelle sicher, dass diese Datei im selben Ordner liegt
KONTROLLDATUM = "2024-12-31"
WALLET_ADRESSE = "YWmErgPSqc6rshcibxtgeLxDhgfs88MuuuJobd8exRH"
RPC_URL = "https://api.mainnet-beta.solana.com"

# Mapping Mint-Adresse zu Token-Symbol (dies musst du ggf. erweitern)
mint_to_symbol = {
    "So11111111111111111111111111111111111111112": "SOL",  # native SOL
    # Weitere Mints je nach Bedarf ergänzen
}

# === 1. CSV-Daten verarbeiten ===
df = pd.read_csv(CSV_DATEI)
df['date'] = pd.to_datetime(df['date'])
df_kontrolliert = df[df['date'] <= pd.Timestamp(KONTROLLDATUM)]
df_relevant = df_kontrolliert[['direction', 'amount', 'token']].copy()
df_relevant['amount_signed'] = df_relevant.apply(
    lambda row: row['amount'] if row['direction'] == 'in' else -row['amount'],
    axis=1
)
saldo_pro_token = df_relevant.groupby('token')['amount_signed'].sum().reset_index()
saldo_pro_token.columns = ['Token', 'Rechnerische Balance']
saldo_pro_token = saldo_pro_token.set_index('Token')

# === 2. Aktuellen On-Chain Stand abfragen ===
client = Client(RPC_URL)
wallet = Pubkey.from_string(WALLET_ADRESSE)

# SOL-Balance
sol_resp = client.get_balance(wallet)
sol_balance = sol_resp['result']['value'] / 1e9

actual_balances = {"SOL": sol_balance}

# SPL Token Accounts abrufen
spl_resp = client.get_parsed_token_accounts_by_owner(
    wallet,
    {'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'}
)

for acc in spl_resp['result']['value']:
    info = acc['account']['data']['parsed']['info']
    mint = info['mint']
    amt = float(info['tokenAmount']['uiAmount'])
    symbol = mint_to_symbol.get(mint, mint)  # fallback: mint-Adresse als key
    actual_balances[symbol] = actual_balances.get(symbol, 0) + amt

# === 3. Vergleich berechnen ===
df_actual = pd.DataFrame({"Tatsächliche Balance": pd.Series(actual_balances)})
df_merged = saldo_pro_token.join(df_actual, how='outer').fillna(0)
df_merged['Differenz'] = df_merged['Tatsächliche Balance'] - df_merged['Rechnerische Balance']
df_merged['Status'] = df_merged['Differenz'].apply(lambda x: "Match" if abs(x) < 1e-8 else "Abweichung")

# === 4. Ausgabe ===
print("Abstimmungsbericht per 31.12.2024")
print(df_merged.round(8))

# Optional: Export
# df_merged.to_csv("abstimmungsbericht.csv")
