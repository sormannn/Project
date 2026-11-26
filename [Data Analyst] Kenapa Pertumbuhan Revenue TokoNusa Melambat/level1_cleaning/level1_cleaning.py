"""Level 1 - Data cleaning & validasi (tugas 1-3).
Jalankan dari root repo:  python level1_cleaning/level1_cleaning.py
Output: orders_clean.csv, customers_clean.csv, cleaning_log.csv (folder ini).
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent

orders = pd.read_csv(ROOT / "data/raw/orders.csv")
cust = pd.read_csv(ROOT / "data/raw/customers.csv")
n_o_raw, n_c_raw = len(orders), len(cust)

log = []
def add(tabel, masalah, kolom, n, perlakuan, alasan):
    log.append(dict(tabel=tabel, masalah=masalah, kolom=kolom, baris_terdampak=n,
                    perlakuan=perlakuan, alasan=alasan))

# 1. Profil awal ---------------------------------------------------------
print("Orders :", orders.shape, "| null:", orders.isna().sum()[lambda s: s > 0].to_dict())
print("Cust   :", cust.shape, "| null:", cust.isna().sum()[lambda s: s > 0].to_dict())

# 2. Duplikat (baris identik penuh) --------------------------------------
n_dup = int(orders.duplicated().sum())
orders = orders.drop_duplicates().copy()
add("orders", "Baris duplikat (seluruh kolom identik)", "semua", n_dup, "Hapus, sisakan 1 baris",
    "Satu order_id tidak mungkin tercatat dua kali; dibiarkan akan menggelembungkan revenue")
assert orders.order_id.is_unique

# 3. Huruf tidak konsisten ----------------------------------------------
n_cat = int((orders.category != orders.category.str.strip().str.title()).sum())
n_sta = int((orders.status != orders.status.str.strip().str.title()).sum())
orders["category"] = orders.category.str.strip().str.title()
orders["status"] = orders.status.str.strip().str.title()
add("orders", "Huruf tidak konsisten (mis. 'fashion')", "category", n_cat, "Standarkan: TRIM + Title Case",
    "Tanpa ini 'Fashion' dan 'fashion' terhitung dua kategori")
add("orders", "Huruf tidak konsisten (mis. 'COMPLETED')", "status", n_sta, "Standarkan: TRIM + Title Case",
    "Filter status Completed akan melewatkan baris huruf besar")

# 4. Format tanggal campur ----------------------------------------------
is_dmy = orders.order_date.str.contains("/")
iso = pd.to_datetime(orders.order_date, format="%Y-%m-%d", errors="coerce")
dmy = pd.to_datetime(orders.order_date, format="%d/%m/%Y", errors="coerce")
orders["order_date"] = iso.fillna(dmy)
assert orders.order_date.notna().all()
add("orders", "Format tanggal campur (dd/mm/yyyy)", "order_date", int(is_dmy.sum()),
    "Parse dengan format eksplisit %d/%m/%Y lalu seragamkan ke YYYY-MM-DD",
    "Tanggal salah baca merusak analisis bulanan/cohort")
add("orders", "Pola tanggal ISO (YYYY-MM-DD)", "order_date", int((~is_dmy).sum()),
    "Parse dengan format eksplisit %Y-%m-%d (JANGAN dayfirst=True)",
    "dayfirst=True menukar hari-bulan pada tanggal ISO dengan hari<=12 (bug umum: 953 baris tertukar, memicu flag palsu 'order sebelum signup')")

# 5. Nilai kosong / tidak valid -----------------------------------------
orders["flag_harga_kosong"] = orders.unit_price.isna()
add("orders", "unit_price kosong", "unit_price", int(orders.flag_harga_kosong.sum()),
    "Flag (flag_harga_kosong); TIDAK diimputasi; keluar dari hitungan revenue",
    "Mengarang harga mengubah angka uang; baris tetap berguna untuk analisis status/jumlah order")
orders["flag_qty_negatif"] = orders.quantity < 0
n_neg = int(orders.flag_qty_negatif.sum())
orders["quantity"] = orders.quantity.abs()
add("orders", "quantity negatif", "quantity", n_neg, "ABS() + flag (flag_qty_negatif)",
    "Asumsi salah input tanda (bukan retur karena retur sudah punya status Returned); perlu konfirmasi pemilik data")
# kolom lain valid?
assert (orders.discount_pct.between(0, 1)).all() and (orders.shipping_fee >= 0).all()
add("orders", "Cek discount_pct (0-1) & shipping_fee (>=0)", "discount_pct, shipping_fee", 0, "Tidak ada perubahan", "Nilai valid")

# 6. Integritas relasi ---------------------------------------------------
orders["flag_customer_tidak_ada"] = ~orders.customer_id.isin(cust.customer_id)
add("orders", "customer_id tidak ada di customers (yatim)", "customer_id", int(orders.flag_customer_tidak_ada.sum()),
    "Flag (flag_customer_tidak_ada); tetap masuk revenue; keluar dari analisis yang butuh atribut pelanggan",
    "Revenue tetap terjadi, hanya atribut (kota/channel/signup) tidak diketahui")

# 7. Customers -----------------------------------------------------------
add("customers", "customer_id duplikat", "customer_id", int(cust.customer_id.duplicated().sum()), "Tidak ada", "Pengecekan lolos")
n_g = int(cust.gender.isna().sum())
cust["gender"] = cust.gender.fillna("Unknown")
add("customers", "gender kosong", "gender", n_g, "Isi 'Unknown'", "Kolom tidak dipakai di analisis; nilai hilang dijaga eksplisit")
cust["signup_date"] = pd.to_datetime(cust.signup_date)
add("customers", "Rentang signup_date", "signup_date", 0, f"Tidak ada ({cust.signup_date.min():%Y-%m-%d} s/d {cust.signup_date.max():%Y-%m-%d})", "Masuk akal")
x = orders.merge(cust[["customer_id", "signup_date"]], on="customer_id")
add("orders", "Order sebelum signup (setelah tanggal diperbaiki)", "order_date", int((x.order_date < x.signup_date).sum()), "Tidak ada", "Pengecekan lolos")
add("orders", "Tanggal di masa depan (> 2026-10-31)", "order_date", int((orders.order_date > "2026-10-31").sum()), "Tidak ada", "Pengecekan lolos")

# 8. Ringkasan baris + definisi revenue ---------------------------------
add("ringkasan", "Jumlah baris orders sebelum -> sesudah", "-", n_o_raw - len(orders), f"{n_o_raw} -> {len(orders)}", "Hanya duplikat yang dihapus")
add("ringkasan", "Jumlah baris customers sebelum -> sesudah", "-", 0, f"{n_c_raw} -> {len(cust)}", "Tidak ada baris dihapus")
comp = orders[orders.status.eq("Completed")]
add("definisi", "net_revenue", "-", 0, "unit_price x quantity x (1 - discount_pct); shipping_fee tidak dihitung",
    "Revenue produk bersih diskon; ongkir bukan pendapatan produk")
add("definisi", "Status yang dihitung", "status", int(len(comp)), "Hanya Completed (Cancelled & Returned dikeluarkan)", "Hanya transaksi yang benar-benar selesai")
add("definisi", "Order Completed tanpa harga", "unit_price", int(comp.unit_price.isna().sum()),
    "Dikeluarkan dari net_revenue DAN jumlah_order DAN pelanggan_aktif", "Pembilang & penyebut AOV dari himpunan order yang sama")
add("definisi", "Order Completed dari customer yatim", "customer_id", int(comp.flag_customer_tidak_ada.sum()),
    "Tetap dihitung di revenue; kota/channel = 'Tidak diketahui'", "Revenue tidak butuh atribut pelanggan")

# 9. Simpan --------------------------------------------------------------
orders_out = orders.copy(); orders_out["order_date"] = orders_out.order_date.dt.strftime("%Y-%m-%d")
cust_out = cust.copy(); cust_out["signup_date"] = cust_out.signup_date.dt.strftime("%Y-%m-%d")
orders_out.to_csv(OUT / "orders_clean.csv", index=False)
cust_out.to_csv(OUT / "customers_clean.csv", index=False)
df = pd.DataFrame(log); df.insert(0, "no", range(1, len(df) + 1))
df.to_csv(OUT / "cleaning_log.csv", index=False)

ok = comp[comp.unit_price.notna()]
total = (ok.unit_price * ok.quantity * (1 - ok.discount_pct)).sum()
print(f"Orders bersih: {len(orders)} | Customers: {len(cust)} | Net revenue: Rp {total:,.0f}")
assert round(total) == 1_961_551_150
