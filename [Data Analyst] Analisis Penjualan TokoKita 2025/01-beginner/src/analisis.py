"""Penyelesaian studi kasus Beginner: analisis penjualan TokoKita 2025."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

# %% 1. Load & kenali data
raw = pd.read_csv(BASE / "data" / "penjualan_tokokita_raw.csv")
print("Ukuran data:", raw.shape)
print(raw.dtypes)
print("\nMissing value:\n", raw.isna().sum())
print("\nBaris duplikat:", raw.duplicated().sum())
print("\nVariasi penulisan kota:", raw["kota"].nunique())

# %% 2. Data cleaning
df = raw.drop_duplicates().copy()
df["kota"] = df["kota"].str.strip().str.title().fillna("Tidak Diketahui")
df["metode_bayar"] = df["metode_bayar"].fillna("Tidak Diketahui")
df = df.dropna(subset=["jumlah"])  # tanpa jumlah, pendapatan tidak bisa dihitung
df["jumlah"] = df["jumlah"].astype(int)
df["tanggal"] = pd.to_datetime(df["tanggal"])
df["bulan"] = df["tanggal"].dt.strftime("%Y-%m")
df["pendapatan"] = df["jumlah"] * df["harga_satuan"] * (100 - df["diskon_persen"]) // 100
df.to_csv(OUT / "penjualan_clean.csv", index=False)
print(f"\nBaris sebelum: {len(raw)}, sesudah cleaning: {len(df)}")

# %% 3. KPI utama
total = df["pendapatan"].sum()
order = df["order_id"].nunique()
print(f"Total pendapatan : Rp{total:,.0f}")
print(f"Jumlah order     : {order:,}")
print(f"Unit terjual     : {df['jumlah'].sum():,}")
print(f"Rata-rata/order  : Rp{total / order:,.0f}")

# %% 4. Pendapatan per bulan
bulanan = df.groupby("bulan")["pendapatan"].sum()
print(bulanan)

# %% 5. Kategori
kategori = (df.groupby("kategori")
              .agg(order=("order_id", "count"), unit=("jumlah", "sum"),
                   pendapatan=("pendapatan", "sum"))
              .sort_values("pendapatan", ascending=False))
kategori["kontribusi_%"] = (kategori["pendapatan"] / total * 100).round(1)
print(kategori)

# %% 6. Top 5 produk
top_produk = df.groupby("produk")["pendapatan"].sum().nlargest(5)
print(top_produk)

# %% 7. Kota
kota = (df.groupby("kota")
          .agg(order=("order_id", "count"), pendapatan=("pendapatan", "sum"))
          .sort_values("pendapatan", ascending=False))
kota["rata_per_order"] = (kota["pendapatan"] / kota["order"]).round(0)
print(kota)

# %% 8. Metode pembayaran
bayar = df["metode_bayar"].value_counts().to_frame("order")
bayar["persen"] = (bayar["order"] / len(df) * 100).round(1)
print(bayar)

# %% 9. Visualisasi
BIRU, TINTA = "#2a78d6", "#52514e"
juta = FuncFormatter(lambda x, _: f"{x / 1e6:,.0f}")

def simpan(seri, judul, nama, horizontal=True):
    fig, ax = plt.subplots(figsize=(9, 4.8))
    if horizontal:
        s = seri.sort_values()
        ax.barh(s.index, s.values, color=BIRU, height=0.6)
        ax.xaxis.set_major_formatter(juta)
        ax.set_xlabel("Pendapatan (juta Rp)", color=TINTA)
        ax.grid(axis="x", color="#e6e5e0")
    else:
        ax.bar(seri.index, seri.values, color=BIRU, width=0.65)
        ax.yaxis.set_major_formatter(juta)
        ax.set_ylabel("Pendapatan (juta Rp)", color=TINTA)
        ax.set_xticks(range(len(seri)),
                      ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                       "Jul", "Agu", "Sep", "Okt", "Nov", "Des"])
        ax.grid(axis="y", color="#e6e5e0")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=TINTA)
    ax.set_title(judul, loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / nama, dpi=150)
    plt.close(fig)

simpan(bulanan, "Pendapatan Bulanan 2025", "01_pendapatan_bulanan.png", horizontal=False)
simpan(kategori["pendapatan"], "Pendapatan per Kategori", "02_kategori.png")
simpan(top_produk, "Top 5 Produk", "03_top_produk.png")
simpan(kota["pendapatan"], "Pendapatan per Kota", "04_kota.png")
print("Grafik tersimpan di folder output/")
