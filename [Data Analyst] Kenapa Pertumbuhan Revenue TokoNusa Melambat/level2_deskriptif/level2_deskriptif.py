"""Level 2 - Analisis deskriptif (tugas 4-6).
Jalankan dari root repo (setelah level 1):  python level2_deskriptif/level2_deskriptif.py
Output: level2_deskriptif.xlsx (nilai dasar dihitung di pandas, kolom turunan/total/cek = formula Excel).
"""
from pathlib import Path
import pandas as pd
from scipy.stats import chi2_contingency
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "level2_deskriptif.xlsx"
REF_TOTAL = 1_961_551_150          # acuan dari soal / hasil level 1

o = pd.read_csv(ROOT / "level1_cleaning/orders_clean.csv", parse_dates=["order_date"])
c = pd.read_csv(ROOT / "level1_cleaning/customers_clean.csv")
o["gross"] = o.unit_price * o.quantity
o["rev"] = o.gross * (1 - o.discount_pct)
comp = o[(o.status == "Completed") & o.unit_price.notna()].copy()   # basis revenue: 2.282 order
comp["bulan"] = comp.order_date.dt.strftime("%Y-%m")

# ---------- styling helpers ----------
F = "Arial"
HDR = PatternFill("solid", fgColor="1F3864"); TOT = PatternFill("solid", fgColor="D9E1F2")
thin = Side(style="thin", color="BFBFBF"); BORDER = Border(top=thin, bottom=thin, left=thin, right=thin)
def title(ws, text, sub=None):
    ws["A1"] = text; ws["A1"].font = Font(name=F, size=13, bold=True)
    if sub: ws["A2"] = sub; ws["A2"].font = Font(name=F, size=9, italic=True, color="595959")
def header(ws, row, cols):
    for j, h in enumerate(cols, 1):
        cell = ws.cell(row=row, column=j, value=h)
        cell.font = Font(name=F, bold=True, color="FFFFFF"); cell.fill = HDR
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); cell.border = BORDER
def put(ws, row, col, val, fmt=None, bold=False, inp=False, fill=None):
    cell = ws.cell(row=row, column=col, value=val)
    cell.font = Font(name=F, bold=bold, color="0000FF" if inp else "000000")   # biru = input hardcode, hitam = formula
    if fmt: cell.number_format = fmt
    if fill: cell.fill = fill
    cell.border = BORDER
    return cell
def note(ws, row, text, bold=False, width_cols=8):
    ws.cell(row=row, column=1, value=text).font = Font(name=F, size=10, bold=bold)
    ws.cell(row=row, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=width_cols)
    ws.row_dimensions[row].height = max(15, 15 * (len(text) // 110 + 1))
def widths(ws, ws_widths):
    for k, w in ws_widths.items(): ws.column_dimensions[k].width = w
RP, PCT, INT = "#,##0", "0.0%", "#,##0"

wb = Workbook()

# =========================== T4 BULANAN ===========================
ws = wb.active; ws.title = "T4 Bulanan"
title(ws, "Tugas 4 - Tabel bulanan (Completed, berharga)", "Biru = nilai dasar dari pandas; hitam = formula. net_revenue = unit_price x qty x (1 - diskon)")
cols = ["bulan", "net_revenue", "jumlah_order", "aov", "pelanggan_aktif", "mom_growth_%"]
header(ws, 3, cols)
g = comp.groupby("bulan").agg(rev=("rev", "sum"), n=("order_id", "count"), cu=("customer_id", "nunique"))
r0 = 4
for i, (m, row) in enumerate(g.iterrows()):
    r = r0 + i
    put(ws, r, 1, m); put(ws, r, 2, float(row.rev), RP, inp=True); put(ws, r, 3, int(row.n), INT, inp=True)
    put(ws, r, 4, f"=B{r}/C{r}", RP); put(ws, r, 5, int(row.cu), INT, inp=True)
    put(ws, r, 6, "n/a" if i == 0 else f"=(B{r}-B{r-1})/B{r-1}", PCT)
rl = r0 + len(g) - 1; rt = rl + 1
put(ws, rt, 1, "TOTAL", bold=True, fill=TOT); put(ws, rt, 2, f"=SUM(B{r0}:B{rl})", RP, True, fill=TOT)
put(ws, rt, 3, f"=SUM(C{r0}:C{rl})", INT, True, fill=TOT); put(ws, rt, 4, f"=B{rt}/C{rt}", RP, True, fill=TOT)
put(ws, rt, 5, int(comp.customer_id.nunique()), INT, True, inp=True, fill=TOT); put(ws, rt, 6, "", fill=TOT)
ws.cell(row=rt, column=5).comment = None
P = lambda a, b: comp[(comp.order_date >= a) & (comp.order_date <= b)].rev.sum()
a26, a25, m26 = P("2026-08-01", "2026-10-31"), P("2025-08-01", "2025-10-31"), P("2026-05-01", "2026-07-31")
note(ws, rt + 2, f"Insight: Kenaikan 2025 sebagian besar efek basis pelanggan yang tumbuh dari nol (data mulai Jan 2025). Sejak 2026 revenue mendatar di kisaran Rp 92-144 jt/bulan "
     f"sementara AOV turun dari Rp 1,18 jt (Agu 2025) ke Rp 0,69-0,99 jt. Agu-Okt 2026 = Rp {a26/1e6:,.0f} jt: {a26/a25-1:+.1%} vs Agu-Okt 2025 dan {a26/m26-1:+.1%} vs Mei-Jul 2026.")
note(ws, rt + 3, "Catatan: pelanggan_aktif di baris TOTAL = pelanggan unik seluruh periode (bukan jumlah kolom), karena satu pelanggan bisa aktif di banyak bulan. "
     "Pertumbuhan Feb-Mar 2025 (1.443% dan 360%) bukan tren: basis Jan 2025 hanya 1 order.")
widths(ws, {"A": 12, "B": 18, "C": 14, "D": 14, "E": 16, "F": 14})
bar = BarChart(); bar.type = "col"; bar.title = "Net revenue (batang) & jumlah order (garis)"; bar.y_axis.title = "Net revenue (Rp)"
bar.add_data(Reference(ws, min_col=2, min_row=3, max_row=rl), titles_from_data=True); bar.set_categories(Reference(ws, min_col=1, min_row=r0, max_row=rl))
ln = LineChart(); ln.add_data(Reference(ws, min_col=3, min_row=3, max_row=rl), titles_from_data=True); ln.y_axis.axId = 200; ln.y_axis.title = "Jumlah order"; ln.y_axis.crosses = "max"
bar.y_axis.delete = False; bar.x_axis.delete = False; ln.y_axis.delete = False
bar.roundedCorners = False; bar.title.overlay = False; bar.legend.overlay = False; bar.y_axis.title.overlay = False; ln.y_axis.title.overlay = False
bar += ln; bar.height, bar.width = 9, 20; bar.legend.position = "b"
ws.add_chart(bar, "H3")
T4_TOTAL_ROW = rt

# =========================== T5 KATEGORI & KOTA ===========================
def revenue_table(ws, df, key, label, tot_ref_cell=None):
    header(ws, 3, [label, "net_revenue", "pct_kontribusi", "jumlah_order", "aov"])
    df = df.sort_values("rev", ascending=False)
    n = len(df); rt = 4 + n
    for i, (k, row) in enumerate(df.iterrows()):
        r = 4 + i
        put(ws, r, 1, k); put(ws, r, 2, float(row.rev), RP, inp=True); put(ws, r, 3, f"=B{r}/$B${rt}", PCT)
        put(ws, r, 4, int(row.n), INT, inp=True); put(ws, r, 5, f"=B{r}/D{r}", RP)
    put(ws, rt, 1, "TOTAL", bold=True, fill=TOT); put(ws, rt, 2, f"=SUM(B4:B{rt-1})", RP, True, fill=TOT)
    put(ws, rt, 3, f"=SUM(C4:C{rt-1})", PCT, True, fill=TOT); put(ws, rt, 4, f"=SUM(D4:D{rt-1})", INT, True, fill=TOT)
    put(ws, rt, 5, f"=B{rt}/D{rt}", RP, True, fill=TOT)
    widths(ws, {"A": 20, "B": 18, "C": 16, "D": 14, "E": 14})
    return rt

ws = wb.create_sheet("T5 Kategori"); title(ws, "Tugas 5a - Net revenue per kategori")
kat = comp.groupby("category").agg(rev=("rev", "sum"), n=("order_id", "count"))
rt_kat = revenue_table(ws, kat, "category", "kategori")
e = kat.loc["Elektronik"]
note(ws, rt_kat + 2, f"Insight: Elektronik menyumbang {e.rev/kat.rev.sum():.1%} revenue dari hanya {e.n/kat.n.sum():.0%} order (AOV Rp {e.rev/e.n/1e6:.1f} jt, ~10x Kecantikan). "
     "Revenue sangat bergantung pada satu kategori: pergeseran mix order dari/ke Elektronik langsung menggerakkan total revenue.", width_cols=6)

ws = wb.create_sheet("T5 Kota"); title(ws, "Tugas 5b - Net revenue per kota (join ke customers)")
x = comp.merge(c[["customer_id", "city", "acquisition_channel", "signup_date"]], on="customer_id", how="left")
x["city"] = x.city.fillna("Tidak diketahui")
kota = x.groupby("city").agg(rev=("rev", "sum"), n=("order_id", "count"))
kota = pd.concat([kota.drop("Tidak diketahui").sort_values("rev", ascending=False), kota.loc[["Tidak diketahui"]]])
# tabel kota: 'Tidak diketahui' ditaruh paling bawah (bukan kota sungguhan)
header(ws, 3, ["kota", "net_revenue", "pct_kontribusi", "jumlah_order", "aov"]); rtk = 4 + len(kota)
for i, (k, row) in enumerate(kota.iterrows()):
    r = 4 + i
    put(ws, r, 1, k); put(ws, r, 2, float(row.rev), RP, inp=True); put(ws, r, 3, f"=B{r}/$B${rtk}", PCT)
    put(ws, r, 4, int(row.n), INT, inp=True); put(ws, r, 5, f"=B{r}/D{r}", RP)
put(ws, rtk, 1, "TOTAL", bold=True, fill=TOT); put(ws, rtk, 2, f"=SUM(B4:B{rtk-1})", RP, True, fill=TOT)
put(ws, rtk, 3, f"=SUM(C4:C{rtk-1})", PCT, True, fill=TOT); put(ws, rtk, 4, f"=SUM(D4:D{rtk-1})", INT, True, fill=TOT); put(ws, rtk, 5, f"=B{rtk}/D{rtk}", RP, True, fill=TOT)
widths(ws, {"A": 20, "B": 18, "C": 16, "D": 14, "E": 14})
kk = kota.drop("Tidak diketahui"); sh = kk.rev / kota.rev.sum()
note(ws, rtk + 2, f"Insight: revenue tersebar merata - 10 kota berada di {sh.min():.1%}-{sh.max():.1%} ({kk.rev.idxmax()} tertinggi, {kk.rev.idxmin()} terendah), tidak ada kota dominan. "
     f"Baris 'Tidak diketahui' ({int(kota.loc['Tidak diketahui','n'])} order customer yatim) hanya {kota.loc['Tidak diketahui','rev']/kota.rev.sum():.1%} dan ditampilkan agar total tetap cocok.", width_cols=6)

# =========================== T6 CANCEL / RETURN ===========================
def status_table(ws, key, label):
    t = pd.crosstab(o[key], o.status)
    t["tot"] = t.sum(axis=1); t["pc"] = t.Cancelled / t.tot; t = t.sort_values("pc", ascending=False)
    header(ws, 3, [label, "total_order", "cancelled", "returned", "pct_cancel", "pct_return"]); rt = 4 + len(t)
    for i, (k, row) in enumerate(t.iterrows()):
        r = 4 + i
        put(ws, r, 1, k); put(ws, r, 2, int(row.tot), INT, inp=True); put(ws, r, 3, int(row.Cancelled), INT, inp=True); put(ws, r, 4, int(row.Returned), INT, inp=True)
        put(ws, r, 5, f"=C{r}/B{r}", PCT); put(ws, r, 6, f"=D{r}/B{r}", PCT)
    put(ws, rt, 1, "TOTAL", bold=True, fill=TOT)
    for j, col in enumerate("BCD", 2): put(ws, rt, j, f"=SUM({col}4:{col}{rt-1})", INT, True, fill=TOT)
    put(ws, rt, 5, f"=C{rt}/B{rt}", PCT, True, fill=TOT); put(ws, rt, 6, f"=D{rt}/B{rt}", PCT, True, fill=TOT)
    widths(ws, {"A": 20, "B": 14, "C": 12, "D": 12, "E": 12, "F": 12})
    pc = chi2_contingency(pd.crosstab(o[key], o.status == "Cancelled"))[1]; pr = chi2_contingency(pd.crosstab(o[key], o.status == "Returned"))[1]
    return t, rt, pc, pr
ws = wb.create_sheet("T6 Cancel Kategori"); title(ws, "Tugas 6a - Cancel & return per kategori (penyebut: SEMUA order)")
tk, rt6a, pc_k, pr_k = status_table(ws, "category", "kategori")
note(ws, rt6a + 2, f"Insight: cancel tertinggi di {tk.index[0]} ({tk.iloc[0].Cancelled/tk.iloc[0].tot:.1%} vs rata-rata {tk.Cancelled.sum()/tk.tot.sum():.1%}), tetapi selisih antar kategori TIDAK signifikan secara statistik "
     f"(chi-square cancel p={pc_k:.2f}; return p={pr_k:.2f}). Jadi belum ada bukti satu kategori bermasalah.", width_cols=6)
ws = wb.create_sheet("T6 Cancel Metode"); title(ws, "Tugas 6b - Cancel & return per metode pembayaran (penyebut: SEMUA order)")
tm, rt6b, pc_m, pr_m = status_table(ws, "payment_method", "metode_pembayaran")
cod = tm.loc["COD"]
note(ws, rt6b + 2, f"Insight: COD tidak menonjol (cancel {cod.Cancelled/cod.tot:.1%}, return {cod.Returned/cod.tot:.1%}; rata-rata {tm.Cancelled.sum()/tm.tot.sum():.1%} / {tm.Returned.sum()/tm.tot.sum():.1%}). "
     f"Kartu Kredit cancel tertinggi ({tm.loc['Kartu Kredit'].Cancelled/tm.loc['Kartu Kredit'].tot:.1%}) namun masih borderline (p={pc_m:.3f}); return p={pr_m:.2f}. Perlu data lebih banyak sebelum disimpulkan.", width_cols=6)

# =========================== CATATAN & CEK ===========================
ws = wb.create_sheet("Catatan & Cek"); title(ws, "Definisi & rekonsiliasi (konsisten dengan level1_cleaning/cleaning_log.csv)")
defs = [("Status dihitung", "Completed saja (Cancelled & Returned dikeluarkan) - untuk tugas 4 & 5."),
        ("net_revenue", "unit_price x quantity x (1 - discount_pct); shipping_fee tidak dihitung."),
        ("Order tanpa harga", f"{int(((o.status=='Completed')&o.unit_price.isna()).sum())} order Completed tanpa harga dikeluarkan dari revenue, jumlah_order, dan pelanggan_aktif (AOV konsisten: 2.282 order)."),
        ("Customer yatim", "Tetap dihitung di tugas 4; di tugas 5b muncul sebagai 'Tidak diketahui'."),
        ("Tugas 6", "Penyebut = semua status (2.697 order), termasuk order tanpa harga karena yang dihitung hanya status."),
        ("Uji signifikansi", "Chi-square (scipy) pada tabel cancel/return vs kelompok; nilai p ditulis di insight tiap sheet.")]
for i, (k, v) in enumerate(defs):
    ws.cell(row=3 + i, column=1, value=k).font = Font(name=F, bold=True); ws.cell(row=3 + i, column=2, value=v).font = Font(name=F)
r = 3 + len(defs) + 1
ws.cell(row=r, column=1, value="REKONSILIASI").font = Font(name=F, bold=True, size=12)
rows = [("Total net_revenue T4 bulanan", f"='T4 Bulanan'!B{T4_TOTAL_ROW}", RP),
        ("Total net_revenue T5 kategori", f"='T5 Kategori'!B{rt_kat}", RP),
        ("Total net_revenue T5 kota", f"='T5 Kota'!B{rtk}", RP),
        ("Angka acuan (level 1)", REF_TOTAL, RP),
        ("Selisih T4 vs acuan", f"=B{r+1}-B{r+4}", RP), ("Selisih T5 kategori vs acuan", f"=B{r+2}-B{r+4}", RP), ("Selisih T5 kota vs acuan", f"=B{r+3}-B{r+4}", RP),
        ("Total order T4 / T5 kat / T5 kota", f"='T4 Bulanan'!C{T4_TOTAL_ROW}&\" / \"&'T5 Kategori'!D{rt_kat}&\" / \"&'T5 Kota'!D{rtk}", None),
        ("Total order T6 kategori", f"='T6 Cancel Kategori'!B{rt6a}", INT), ("Total order T6 metode", f"='T6 Cancel Metode'!B{rt6b}", INT),
        ("Jumlah baris orders_clean.csv", len(o), INT),
        ("Cancelled kategori vs metode", f"='T6 Cancel Kategori'!C{rt6a}&\" vs \"&'T6 Cancel Metode'!C{rt6b}", None),
        ("Returned kategori vs metode", f"='T6 Cancel Kategori'!D{rt6a}&\" vs \"&'T6 Cancel Metode'!D{rt6b}", None)]
for i, (k, v, fmt) in enumerate(rows):
    ws.cell(row=r + 1 + i, column=1, value=k).font = Font(name=F)
    cell = ws.cell(row=r + 1 + i, column=2, value=v); cell.font = Font(name=F, color="0000FF" if not str(v).startswith("=") else "000000")
    if fmt: cell.number_format = fmt
rs = r + 1 + len(rows)
ws.cell(row=rs, column=1, value="STATUS").font = Font(name=F, bold=True)
ws.cell(row=rs, column=2, value=f'=IF(AND(B{r+5}=0,B{r+6}=0,B{r+7}=0,B{r+9}=B{r+11},B{r+10}=B{r+11}),"OK: semua tabel kembali ke total yang sama","CEK ULANG")').font = Font(name=F, bold=True, color="006100")
widths(ws, {"A": 36, "B": 70})
wb.save(OUT); print("saved", OUT)
