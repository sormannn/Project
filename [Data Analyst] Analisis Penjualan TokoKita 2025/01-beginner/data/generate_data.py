"""Membuat dataset SINTETIS penjualan toko fiktif "TokoKita" (2025)."""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 1200

PRODUK = {
    "Elektronik": [("Earphone", 150_000), ("Power Bank", 220_000), ("Smartwatch", 650_000)],
    "Fashion": [("Kaos", 85_000), ("Jaket", 250_000), ("Sepatu", 375_000)],
    "Rumah Tangga": [("Blender", 320_000), ("Panci Set", 280_000), ("Lampu LED", 45_000)],
    "Kecantikan": [("Sunscreen", 75_000), ("Serum", 120_000), ("Parfum", 180_000)],
}

hari = pd.date_range("2025-01-01", "2025-12-31")
bobot_hari = np.where(hari.month.isin([11, 12]), 1.6, np.where(hari.month == 3, 1.35, 1.0))
tanggal = np.sort(rng.choice(hari, N, p=bobot_hari / bobot_hari.sum()))

rows = []
for i, tgl in enumerate(tanggal, start=1):
    kategori = rng.choice(list(PRODUK), p=[0.25, 0.35, 0.20, 0.20])
    produk, harga = PRODUK[kategori][rng.integers(3)]
    rows.append({
        "order_id": f"ORD-{i:05d}",
        "tanggal": pd.Timestamp(tgl).strftime("%Y-%m-%d"),
        "kota": rng.choice(["Jakarta", "Bandung", "Surabaya", "Medan", "Makassar"],
                           p=[0.35, 0.20, 0.22, 0.13, 0.10]),
        "kategori": kategori,
        "produk": produk,
        "jumlah": int(rng.choice([1, 2, 3, 4, 5], p=[0.45, 0.28, 0.15, 0.08, 0.04])),
        "harga_satuan": harga,
        "diskon_persen": int(rng.choice([0, 5, 10, 20], p=[0.55, 0.2, 0.17, 0.08])),
        "metode_bayar": rng.choice(["Transfer Bank", "E-Wallet", "COD", "Kartu Kredit"],
                                   p=[0.3, 0.38, 0.2, 0.12]),
    })
df = pd.DataFrame(rows)
df["jumlah"] = df["jumlah"].astype("Int64")

# Sengaja "mengotori" data untuk latihan cleaning
idx = rng.permutation(N)
for i in idx[:60]:
    df.loc[i, "kota"] = df.loc[i, "kota"].upper()
for i in idx[60:110]:
    df.loc[i, "kota"] = f"  {df.loc[i, 'kota'].lower()} "
df.loc[idx[110:135], "kota"] = None
df.loc[idx[135:165], "metode_bayar"] = None
df.loc[idx[165:180], "jumlah"] = pd.NA
dup = df.iloc[idx[200:225]]
df = pd.concat([df, dup]).sort_values("order_id", kind="stable")

out = Path(__file__).parent / "penjualan_tokokita_raw.csv"
df.to_csv(out, index=False)
print(f"{len(df)} baris disimpan ke {out.name}")
