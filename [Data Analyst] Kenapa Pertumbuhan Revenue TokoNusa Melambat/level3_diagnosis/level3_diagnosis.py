"""Level 3 - Diagnosis (tugas 7-10).
Jalankan dari root repo (setelah level 1):  python level3_diagnosis/level3_diagnosis.py
Output: level3_diagnosis.xlsx. Nilai dasar dihitung di pandas (biru); turunan, total, dekomposisi, cek = formula Excel.
"""
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import kruskal, ttest_ind, chi2_contingency
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import ColorScaleRule

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "level3_diagnosis.xlsx"
REF_TOTAL = 1_961_551_150
REF_DATE = pd.Timestamp("2026-10-31")      # tanggal acuan recency & akhir data

o = pd.read_csv(ROOT / "level1_cleaning/orders_clean.csv", parse_dates=["order_date"])
c = pd.read_csv(ROOT / "level1_cleaning/customers_clean.csv", parse_dates=["signup_date"])
o["gross"] = o.unit_price * o.quantity; o["rev"] = o.gross * (1 - o.discount_pct)
comp_all = o[o.status == "Completed"].copy()                   # Completed (untuk aktivitas/cohort)
comp = comp_all[comp_all.unit_price.notna()].copy()            # Completed berharga (basis revenue)

# ---------- styling ----------
F = "Arial"; HDR = PatternFill("solid", fgColor="1F3864"); TOT = PatternFill("solid", fgColor="D9E1F2")
thin = Side(style="thin", color="BFBFBF"); BORDER = Border(top=thin, bottom=thin, left=thin, right=thin)
RP, PCT, INT, DEC = "#,##0", "0.0%", "#,##0", "0.00"
def title(ws, t, sub=None):
    ws["A1"] = t; ws["A1"].font = Font(name=F, size=13, bold=True)
    if sub: ws["A2"] = sub; ws["A2"].font = Font(name=F, size=9, italic=True, color="595959")
def header(ws, row, cols, c0=1):
    for j, h in enumerate(cols, c0):
        k = ws.cell(row=row, column=j, value=h); k.font = Font(name=F, bold=True, color="FFFFFF"); k.fill = HDR
        k.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); k.border = BORDER
def put(ws, r, col, v, fmt=None, bold=False, inp=False, fill=None):
    k = ws.cell(row=r, column=col, value=v); k.font = Font(name=F, bold=bold, color="0000FF" if inp else "000000"); k.border = BORDER
    if fmt: k.number_format = fmt
    if fill: k.fill = fill
    return k
def note(ws, r, text, cols=12, bold=False):
    ws.cell(row=r, column=1, value=text).font = Font(name=F, size=10, bold=bold)
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=cols); ws.row_dimensions[r].height = max(15, 15 * (len(text) // 125 + 1))
def widths(ws, d):
    for k, w in d.items(): ws.column_dimensions[k].width = w
def chart_fix(ch):
    ch.roundedCorners = False; ch.legend = None
    ch.x_axis.delete = False; ch.y_axis.delete = False
    if ch.title is not None: ch.title.overlay = False

wb = Workbook()

# ====================================================================
# T7 - DEKOMPOSISI PERTUMBUHAN
# ====================================================================
ws7 = wb.active; ws7.title = "T7 Dekomposisi"
title(ws7, "Tugas 7 - Kenapa revenue melambat? Dekomposisi: revenue = pelanggan aktif x order/pelanggan x AOV",
      "Metode log-mean Divisia (LMDI): kontribusi faktor = L x ln(x1/x0), L=(R1-R0)/ln(R1/R0); jumlah kontribusi = perubahan revenue persis. Basis: Completed berharga.")
def period(a, b): return comp[(comp.order_date >= a) & (comp.order_date <= b)]
CATS = ["Elektronik", "Rumah Tangga", "Olahraga", "Fashion", "Kecantikan"]
def block(ws, r, ttl, l0, l1, p0, p1, chart_anchor=None):
    """Tulis satu blok pembanding mulai baris r. Return baris berikutnya & dict posisi sel penting."""
    ws.cell(row=r, column=1, value=ttl).font = Font(name=F, bold=True, size=12)
    header(ws, r + 1, ["metrik", l0, l1, "perubahan", "perubahan %"])
    rows = [("Net revenue (Rp)", p0.rev.sum(), p1.rev.sum(), RP), ("Pelanggan aktif (unik)", p0.customer_id.nunique(), p1.customer_id.nunique(), INT),
            ("Jumlah order", len(p0), len(p1), INT)]
    for i, (k, a, b, fmt) in enumerate(rows):
        rr = r + 2 + i; put(ws, rr, 1, k); put(ws, rr, 2, float(a), fmt, inp=True); put(ws, rr, 3, float(b), fmt, inp=True)
        put(ws, rr, 4, f"=C{rr}-B{rr}", fmt); put(ws, rr, 5, f"=C{rr}/B{rr}-1", PCT)
    rREV, rCU, rN = r + 2, r + 3, r + 4
    rOPC, rAOV, rGR, rDISC = r + 5, r + 6, r + 7, r + 8
    put(ws, rOPC, 1, "Order per pelanggan"); put(ws, rAOV, 1, "AOV (Rp)"); put(ws, rGR, 1, "Revenue sebelum diskon (Rp)"); put(ws, rDISC, 1, "Diskon efektif (1 - net/gross)")
    for col in "BC":
        j = "BC".index(col) + 2
        put(ws, rOPC, j, f"={col}{rN}/{col}{rCU}", DEC); put(ws, rAOV, j, f"={col}{rREV}/{col}{rN}", RP)
        put(ws, rGR, j, float((p0 if col == "B" else p1).gross.sum()), RP, inp=True); put(ws, rDISC, j, f"=1-{col}{rREV}/{col}{rGR}", PCT)
    put(ws, rOPC, 4, f"=C{rOPC}-B{rOPC}", DEC); put(ws, rOPC, 5, f"=C{rOPC}/B{rOPC}-1", PCT)
    put(ws, rAOV, 4, f"=C{rAOV}-B{rAOV}", RP); put(ws, rAOV, 5, f"=C{rAOV}/B{rAOV}-1", PCT)
    put(ws, rGR, 4, f"=C{rGR}-B{rGR}", RP); put(ws, rGR, 5, f"=C{rGR}/B{rGR}-1", PCT)
    put(ws, rDISC, 4, f"=C{rDISC}-B{rDISC}", "0.0%"); put(ws, rDISC, 5, "")
    # dekomposisi
    d = r + 10
    ws.cell(row=d, column=1, value="Dekomposisi perubahan revenue").font = Font(name=F, bold=True)
    put(ws, d + 1, 1, "L (log-mean revenue)"); put(ws, d + 1, 2, f"=(C{rREV}-B{rREV})/LN(C{rREV}/B{rREV})", RP)
    header(ws, d + 2, ["faktor", "kontribusi (Rp)", "kontribusi thd pertumbuhan (poin %)"])
    facs = [("Pelanggan aktif", rCU), ("Order per pelanggan", rOPC), ("AOV", rAOV)]
    for i, (k, src) in enumerate(facs):
        rr = d + 3 + i; put(ws, rr, 1, k); put(ws, rr, 2, f"=$B${d+1}*LN(C{src}/B{src})", RP); put(ws, rr, 3, f"=B{rr}/$B${rREV}", PCT)
    rT = d + 6
    put(ws, rT, 1, "Total kontribusi", bold=True, fill=TOT); put(ws, rT, 2, f"=SUM(B{d+3}:B{d+5})", RP, True, fill=TOT); put(ws, rT, 3, f"=SUM(C{d+3}:C{d+5})", PCT, True, fill=TOT)
    put(ws, rT + 1, 1, "Perubahan revenue aktual"); put(ws, rT + 1, 2, f"=D{rREV}", RP); put(ws, rT + 1, 3, f"=E{rREV}", PCT)
    put(ws, rT + 2, 1, "Selisih (harus 0)"); put(ws, rT + 2, 2, f"=ROUND(B{rT}-B{rT+1},2)", RP); put(ws, rT + 2, 3, "")
    pos = dict(rev=rREV, cu=rCU, n=rN, opc=rOPC, aov=rAOV, disc=rDISC, fac0=d + 3, chk=rT + 2)
    # tabel per kategori: mix vs dalam-kategori
    k0 = rT + 4
    ws.cell(row=k0, column=1, value="Per kategori - AOV turun karena mix atau karena harga/diskon dalam kategori?").font = Font(name=F, bold=True)
    header(ws, k0 + 1, ["kategori", f"revenue {l0}", f"revenue {l1}", "perubahan revenue", f"order {l0}", f"order {l1}", f"share order {l0}", f"share order {l1}",
                        f"AOV {l0}", f"AOV {l1}", "efek mix (Rp/order)", "efek dalam-kategori (Rp/order)"])
    for i, cat in enumerate(CATS):
        rr = k0 + 2 + i; a, b = p0[p0.category == cat], p1[p1.category == cat]; rt = k0 + 2 + len(CATS)
        put(ws, rr, 1, cat); put(ws, rr, 2, float(a.rev.sum()), RP, inp=True); put(ws, rr, 3, float(b.rev.sum()), RP, inp=True); put(ws, rr, 4, f"=C{rr}-B{rr}", RP)
        put(ws, rr, 5, len(a), INT, inp=True); put(ws, rr, 6, len(b), INT, inp=True)
        put(ws, rr, 7, f"=E{rr}/E${rt}", PCT); put(ws, rr, 8, f"=F{rr}/F${rt}", PCT)
        put(ws, rr, 9, f"=B{rr}/E{rr}", RP); put(ws, rr, 10, f"=C{rr}/F{rr}", RP)
        put(ws, rr, 11, f"=(H{rr}-G{rr})*I{rr}", RP); put(ws, rr, 12, f"=H{rr}*(J{rr}-I{rr})", RP)
    rt = k0 + 2 + len(CATS)
    put(ws, rt, 1, "TOTAL", bold=True, fill=TOT)
    for j, col in zip([2, 3, 4, 5, 6, 7, 8, 11, 12], "BCDEFGHKL"):
        put(ws, rt, j, f"=SUM({col}{k0+2}:{col}{rt-1})", PCT if col in "GH" else RP, True, fill=TOT)
    put(ws, rt, 9, f"=B{rt}/E{rt}", RP, True, fill=TOT); put(ws, rt, 10, f"=C{rt}/F{rt}", RP, True, fill=TOT)
    put(ws, rt + 1, 1, "Cek: mix + dalam-kategori = perubahan AOV"); put(ws, rt + 1, 11, f"=ROUND(K{rt}+L{rt}-D{rAOV},2)", RP)
    pos.update(cat0=k0 + 2, catT=rt, catchk=rt + 1)
    return rt + 3, pos

P_A = (period("2026-05-01", "2026-07-31"), period("2026-08-01", "2026-10-31"))
P_B = (period("2025-08-01", "2025-10-31"), period("2026-08-01", "2026-10-31"))
nxt, posA = block(ws7, 4, "A. Kuartal ke kuartal: Mei-Jul 2026 -> Agu-Okt 2026", "Mei-Jul 2026", "Agu-Okt 2026", *P_A)
nxt, posB = block(ws7, nxt + 1, "B. Tahun ke tahun: Agu-Okt 2025 -> Agu-Okt 2026", "Agu-Okt 2025", "Agu-Okt 2026", *P_B)
# insight (dihitung dari data)
def stats7(p0, p1):
    r0, r1 = p0.rev.sum(), p1.rev.sum(); L = (r1 - r0) / np.log(r1 / r0)
    cu = (p1.customer_id.nunique() / p0.customer_id.nunique()); opc = (len(p1) / p1.customer_id.nunique()) / (len(p0) / p0.customer_id.nunique()); aov = (p1.rev.mean() / p0.rev.mean())
    return {k: L * np.log(v) / r0 for k, v in dict(cu=cu, opc=opc, aov=aov).items()} | dict(g=r1 / r0 - 1)
sa, sb = stats7(*P_A), stats7(*P_B)
def mix_share(p0, p1):
    s0, s1 = p0.category.value_counts(normalize=True), p1.category.value_counts(normalize=True)
    a0 = p0.groupby("category").rev.mean(); mix = sum((s1[k] - s0[k]) * a0[k] for k in CATS); tot = p1.rev.mean() - p0.rev.mean(); return mix / tot, s0["Elektronik"], s1["Elektronik"]
ms, e0, e1 = mix_share(*P_B)
d0, d1 = 1 - P_B[0].rev.sum() / P_B[0].gross.sum(), 1 - P_B[1].rev.sum() / P_B[1].gross.sum()
note(ws7, nxt, f"Insight A (QoQ): revenue Agu-Okt 2026 {sa['g']:+.1%} vs Mei-Jul 2026 - praktis datar; pelanggan aktif, order/pelanggan, dan AOV semuanya bergerak < 2 poin. Tidak ada satu penyebab tunggal; basis pelanggan stagnan.", bold=True)
note(ws7, nxt + 1, f"Insight B (YoY): revenue hanya {sb['g']:+.1%} walau pelanggan aktif naik 21%: kenaikan pelanggan menyumbang {sb['cu']*100:+.1f} poin pertumbuhan, order/pelanggan {sb['opc']*100:+.1f} poin, tetapi AOV menggerus {sb['aov']*100:+.1f} poin. "
     f"{ms:.0%} dari penurunan AOV berasal dari MIX: share order Elektronik turun dari {e0:.1%} ke {e1:.1%} (AOV Elektronik sekitar 4-11x kategori lain). Bukan karena diskon - diskon efektif justru turun ({d0:.1%} -> {d1:.1%}).", bold=True)
note(ws7, nxt + 2, "Catatan: pelanggan aktif dihitung unik dalam periode 3 bulan. Data signup berakhir 24 Agu 2026 (tidak ada pelanggan baru Sep-Okt 2026) sehingga basis pelanggan bergantung pada pelanggan yang sudah ada; biaya iklan tidak ada di data sehingga hubungan dengan kenaikan budget iklan 30% tidak dapat diuji.")
widths(ws7, {"A": 40, "B": 18, "C": 22, "D": 16, "E": 16, "F": 14, "G": 14, "H": 14, "I": 14, "J": 14, "K": 18, "L": 22})
ch = BarChart(); ch.type = "col"; ch.title = "YoY: kontribusi faktor thd pertumbuhan revenue (poin %)"
ch.add_data(Reference(ws7, min_col=3, min_row=posB["fac0"], max_row=posB["fac0"] + 2)); ch.set_categories(Reference(ws7, min_col=1, min_row=posB["fac0"], max_row=posB["fac0"] + 2))
chart_fix(ch); ch.y_axis.number_format = "0%"; ch.height, ch.width = 8, 14; ws7.add_chart(ch, "G" + str(posB["rev"] - 2))

# ====================================================================
# T8 - CHANNEL AKUISISI
# ====================================================================
ws8 = wb.create_sheet("T8 Channel")
title(ws8, "Tugas 8 - Perbandingan channel akuisisi (revenue bersih setelah diskon)", "Basis revenue: Completed berharga. Pelanggan signup = semua pelanggan di customers.csv per channel (termasuk yang belum pernah order).")
x = comp.merge(c[["customer_id", "acquisition_channel"]], on="customer_id", how="left"); x["ch"] = x.acquisition_channel.fillna("Tidak diketahui")
oo = o.merge(c[["customer_id", "acquisition_channel"]], on="customer_id", how="left"); oo["ch"] = oo.acquisition_channel.fillna("Tidak diketahui")
signed = c.groupby("acquisition_channel").size()
ch_tab = x.groupby("ch").agg(rev=("rev", "sum"), gross=("gross", "sum"), n=("order_id", "count"), act=("customer_id", "nunique"))
st = pd.crosstab(oo.ch, oo.status)
order_ch = list(signed.index.difference([])) ; order_ch = sorted(signed.index, key=lambda k: -ch_tab.loc[k].rev) + ["Tidak diketahui"]
cols = ["channel", "pelanggan_signup", "pelanggan_aktif", "net_revenue", "revenue_sebelum_diskon", "diskon_efektif", "rev_per_pelanggan_signup", "rev_per_pelanggan_aktif", "jumlah_order", "aov", "pct_cancel", "pct_return"]
header(ws8, 3, cols); rt8 = 4 + len(order_ch)
for i, k in enumerate(order_ch):
    r = 4 + i; row = ch_tab.loc[k]; unk = k == "Tidak diketahui"
    put(ws8, r, 1, k); put(ws8, r, 2, "n/a" if unk else int(signed[k]), INT, inp=not unk); put(ws8, r, 3, int(row.act), INT, inp=True)
    put(ws8, r, 4, float(row.rev), RP, inp=True); put(ws8, r, 5, float(row.gross), RP, inp=True); put(ws8, r, 6, f"=1-D{r}/E{r}", PCT)
    put(ws8, r, 7, "n/a" if unk else f"=D{r}/B{r}", RP); put(ws8, r, 8, f"=D{r}/C{r}", RP)
    put(ws8, r, 9, int(row.n), INT, inp=True); put(ws8, r, 10, f"=D{r}/I{r}", RP)
    tot = int(st.loc[k].sum()); put(ws8, r, 11, int(st.loc[k, "Cancelled"]) / tot, PCT, inp=True); put(ws8, r, 12, int(st.loc[k, "Returned"]) / tot, PCT, inp=True)
put(ws8, rt8, 1, "TOTAL", bold=True, fill=TOT)
put(ws8, rt8, 2, f"=SUM(B4:B{rt8-1})", INT, True, fill=TOT); put(ws8, rt8, 3, int(comp.customer_id.nunique()), INT, True, inp=True, fill=TOT)
for j, col in [(4, "D"), (5, "E"), (9, "I")]: put(ws8, rt8, j, f"=SUM({col}4:{col}{rt8-1})", RP, True, fill=TOT)
put(ws8, rt8, 6, f"=1-D{rt8}/E{rt8}", PCT, True, fill=TOT); put(ws8, rt8, 7, f"=D{rt8}/B{rt8}", RP, True, fill=TOT); put(ws8, rt8, 8, f"=D{rt8}/C{rt8}", RP, True, fill=TOT)
put(ws8, rt8, 10, f"=D{rt8}/I{rt8}", RP, True, fill=TOT)
put(ws8, rt8, 11, float((oo.status == "Cancelled").mean()), PCT, True, inp=True, fill=TOT); put(ws8, rt8, 12, float((oo.status == "Returned").mean()), PCT, True, inp=True, fill=TOT)
cust_rev = comp.groupby("customer_id").rev.sum(); cc = c.set_index("customer_id").join(cust_rev).fillna({"rev": 0})
p_kw = kruskal(*[g.rev.values for _, g in cc.groupby("acquisition_channel")]).pvalue
d = x[x.ch != "Tidak diketahui"].copy(); d["ads"] = d.ch.str.contains("Ads")
p_t = ttest_ind(d[d.ads].discount_pct, d[~d.ads].discount_pct, equal_var=False).pvalue
m_ads, m_non = d[d.ads].discount_pct.mean(), d[~d.ads].discount_pct.mean()
p_cc = chi2_contingency(pd.crosstab(oo.ch, oo.status))[1]
r = rt8 + 2
ws8.cell(row=r, column=1, value="Uji statistik (dihitung di Python, hardcode sebagai referensi)").font = Font(name=F, bold=True)
tests = [("Revenue per pelanggan signup antar channel (Kruskal-Wallis)", p_kw, "p > 0,05: tidak ada bukti channel menghasilkan revenue/pelanggan berbeda"),
         ("Rata-rata discount_pct: channel Ads vs non-Ads (Welch t-test)", p_t, f"Ads {m_ads:.1%} vs non-Ads {m_non:.1%}; sangat signifikan"),
         ("Cancel/return antar channel (chi-square)", p_cc, "p > 0,05: kualitas order tidak berbeda antar channel")]
for i, (k, p, e) in enumerate(tests):
    ws8.cell(row=r + 1 + i, column=1, value=k).font = Font(name=F); put(ws8, r + 1 + i, 4, float(p), "0.0000", inp=True); ws8.cell(row=r + 1 + i, column=5, value=e).font = Font(name=F, size=9, italic=True)
dsc = ch_tab.assign(d=lambda t: 1 - t.rev / t.gross).d
note(ws8, r + 5, f"Insight: Organic punya diskon efektif terendah ({dsc['Organic']:.1%}) sedangkan Ads, Referral, dan Email berada di {dsc[[k for k in dsc.index if k not in ('Organic','Tidak diketahui')]].min():.1%}-{dsc[[k for k in dsc.index if k not in ('Organic','Tidak diketahui')]].max():.1%}. "
     f"Namun revenue per pelanggan antar channel tidak berbeda signifikan (p={p_kw:.2f}) - jadi channel berbayar tidak terbukti menghasilkan pelanggan yang lebih bernilai, tetapi 'membeli' pelanggan dengan diskon yang lebih besar. Organic = revenue bersih per pelanggan sekelas Ads tanpa subsidi diskon.", bold=True)
note(ws8, r + 6, "Keterbatasan: biaya iklan (CAC/ROAS) tidak ada di data, jadi 'efisien' hanya bisa dinilai relatif lewat revenue bersih per pelanggan dan diskon. Referral & Email berukuran kecil (113 dan 67 pelanggan) sehingga angkanya kurang stabil. Pelanggan yatim tidak punya channel ('Tidak diketahui').")
widths(ws8, {"A": 18, "B": 14, "C": 14, "D": 16, "E": 18, "F": 12, "G": 18, "H": 18, "I": 12, "J": 12, "K": 11, "L": 11})
ch = BarChart(); ch.type = "col"; ch.title = "Diskon efektif per channel"
ch.add_data(Reference(ws8, min_col=6, min_row=4, max_row=rt8 - 1)); ch.set_categories(Reference(ws8, min_col=1, min_row=4, max_row=rt8 - 1))
chart_fix(ch); ch.y_axis.number_format = "0%"; ch.height, ch.width = 8, 14; ws8.add_chart(ch, f"A{r+9}")

# ====================================================================
# T9 - COHORT RETENTION
# ====================================================================
ws9 = wb.create_sheet("T9 Cohort")
title(ws9, "Tugas 9 - Cohort retention bulanan (cohort = bulan signup)", "Aktif = punya >=1 order Completed pada bulan ke-N sejak bulan signup. Customer yatim tidak punya tanggal signup -> dikeluarkan. Sel kosong = belum teramati (bukan churn).")
cu = comp_all.merge(c[["customer_id", "signup_date"]], on="customer_id")
cu["off"] = (cu.order_date.dt.year * 12 + cu.order_date.dt.month) - (cu.signup_date.dt.year * 12 + cu.signup_date.dt.month)
c["cohort"] = c.signup_date.dt.to_period("M"); cu = cu.merge(c[["customer_id", "cohort"]], on="customer_id")
cohorts = sorted(c.cohort.unique()); size = c.groupby("cohort").size()
END = REF_DATE.year * 12 + REF_DATE.month
act = cu.groupby(["cohort", "off"]).customer_id.nunique().unstack(fill_value=0)
NOFF = max(END - (p.year * 12 + p.month) for p in cohorts) + 1
put_row0 = 5
ws9.cell(row=4, column=1, value="A. Jumlah pelanggan aktif per bulan-ke-N").font = Font(name=F, bold=True)
header(ws9, 5, ["cohort", "ukuran_cohort"] + [f"M{k}" for k in range(NOFF)])
r_first = 6; r_last = r_first + len(cohorts) - 1
for i, p in enumerate(cohorts):
    r = r_first + i; put(ws9, r, 1, str(p)); put(ws9, r, 2, int(size[p]), INT, inp=True)
    maxoff = END - (p.year * 12 + p.month)
    for k in range(NOFF):
        if k <= maxoff:
            v = int(act.loc[p, k]) if (p in act.index and k in act.columns) else 0
            put(ws9, r, 3 + k, v, INT, inp=True)
        else: put(ws9, r, 3 + k, None)
put(ws9, r_last + 1, 1, "TOTAL ukuran", bold=True, fill=TOT); put(ws9, r_last + 1, 2, f"=SUM(B{r_first}:B{r_last})", INT, True, fill=TOT)
B0 = r_last + 4
ws9.cell(row=B0 - 1, column=1, value="B. Retention % = pelanggan aktif / ukuran cohort (heatmap)").font = Font(name=F, bold=True)
header(ws9, B0, ["cohort", "ukuran_cohort"] + [f"M{k}" for k in range(NOFF)])
for i, p in enumerate(cohorts):
    r = B0 + 1 + i; ra = r_first + i; put(ws9, r, 1, str(p)); put(ws9, r, 2, f"=B{ra}", INT)
    for k in range(NOFF):
        col = ws9.cell(row=ra, column=3 + k).column_letter
        put(ws9, r, 3 + k, f'=IF({col}{ra}="","",{col}{ra}/$B{ra})', "0%")
rW = B0 + 1 + len(cohorts)
put(ws9, rW, 1, "Rata-rata tertimbang", bold=True, fill=TOT); put(ws9, rW, 2, "", fill=TOT)
for k in range(NOFF):
    col = ws9.cell(row=r_first, column=3 + k).column_letter
    put(ws9, rW, 3 + k, f"=SUM({col}{r_first}:{col}{r_last})/SUMPRODUCT(--({col}{r_first}:{col}{r_last}<>\"\"),$B${r_first}:$B${r_last})", "0%", True, fill=TOT)
ws9.conditional_formatting.add(f"C{B0+1}:{ws9.cell(row=B0+1, column=2+NOFF).column_letter}{rW-1}",
                               ColorScaleRule(start_type="min", start_color="F8696B", mid_type="percentile", mid_value=50, mid_color="FFEB84", end_type="max", end_color="63BE7B"))
# insight dari data
tot_act = act.reindex(columns=range(NOFF), fill_value=0)
w = []
for k in range(NOFF):
    obs = [p for p in cohorts if END - (p.year * 12 + p.month) >= k]; w.append(tot_act.loc[obs, k].sum() / size[obs].sum() if obs else np.nan)
w = np.array(w)
ws9.cell(row=rW + 2, column=1).value = None
pk = int(np.nanargmax(w))
note(ws9, rW + 2, f"Insight: retention memuncak di M{pk} ({w[pk]:.0%} pelanggan sebuah cohort aktif) lalu meluruh stabil: M6 = {w[6]:.0%}, M12 = {w[12]:.0%}. "
     "Artinya pelanggan cenderung melakukan beberapa order dalam ~3-5 bulan pertama lalu berhenti, bukan menjadi pelanggan rutin jangka panjang. "
     "Konsekuensinya basis pelanggan aktif hanya bertahan bila pelanggan baru terus masuk (data signup berhenti 24 Agu 2026) atau ada program reaktivasi. M0 rendah karena order pertama sering jatuh di bulan berikutnya.", cols=14, bold=True)
note(ws9, rW + 3, "Catatan: cohort baru hanya punya sedikit bulan pengamatan (data berhenti Okt 2026) -> pojok kanan bawah kosong secara alami. Ukuran cohort ~40-75 pelanggan sehingga angka per sel berfluktuasi +-5-8 poin, dan rata-rata di M15+ memakai sangat sedikit cohort; baca pola rata-rata M0-M12, bukan sel individual.", cols=14)
widths(ws9, {"A": 22, "B": 14})
for k in range(NOFF): ws9.column_dimensions[ws9.cell(row=5, column=3 + k).column_letter].width = 6.5

# ====================================================================
# T10 - RFM & PARETO
# ====================================================================
wd = wb.create_sheet("T10 Pelanggan")   # detail per pelanggan (dibuat dulu agar summary bisa merujuk)
ws10 = wb.create_sheet("T10 RFM", index=wb.sheetnames.index("T10 Pelanggan"))
g = comp.groupby("customer_id").agg(last=("order_date", "max"), F=("order_id", "count"), M=("rev", "sum")).reset_index()
g["R"] = (REF_DATE - g["last"]).dt.days
g["R_skor"] = pd.qcut(g.R.rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
g["F_skor"] = pd.cut(g.F, [0, 1, 2, 3, 5, 999], labels=[1, 2, 3, 4, 5]).astype(int)
g["M_skor"] = pd.qcut(g.M.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
def seg(r):
    R, Fq = r.R_skor, r.F_skor
    if R >= 4 and Fq >= 4: return "Champions"
    if R >= 3 and Fq >= 3: return "Loyal"
    if R >= 4 and Fq <= 2: return "Promising"
    if R <= 2 and Fq >= 3: return "At Risk"
    if R <= 2 and Fq <= 2: return "Hibernating"
    return "Need Attention"
g["segmen"] = g.apply(seg, axis=1)
g = g.sort_values("M", ascending=False).reset_index(drop=True); g["rank_revenue"] = g.index + 1
title(wd, "Detail RFM per pelanggan (urut revenue terbesar)", f"Tanggal acuan recency = {REF_DATE:%Y-%m-%d}. Basis: Completed berharga. Skor R: kuintil recency (5 = paling baru); F: 1 / 2 / 3 / 4-5 / 6+ order; M: kuintil revenue.")
header(wd, 3, ["customer_id", "recency_hari", "frequency", "monetary", "R", "F", "M", "segmen", "rank_revenue"])
for i, row in g.iterrows():
    r = 4 + i
    for j, (v, fmt) in enumerate([(row.customer_id, None), (int(row.R), INT), (int(row.F), INT), (float(row.M), RP), (int(row.R_skor), None), (int(row.F_skor), None), (int(row.M_skor), None), (row.segmen, None), (int(row.rank_revenue), INT)], 1):
        k = wd.cell(row=r, column=j, value=v); k.font = Font(name=F, color="0000FF" if j in (2, 3, 4, 5, 6, 7, 8) else "000000")
        if fmt: k.number_format = fmt
wd_last = 3 + len(g); widths(wd, {"A": 14, "B": 14, "C": 12, "D": 16, "E": 6, "F": 6, "G": 6, "H": 16, "I": 14})
title(ws10, "Tugas 10 - Segmentasi RFM & konsentrasi revenue (Pareto)", "Ringkasan memakai COUNTIF/SUMIF ke sheet 'T10 Pelanggan'.")
header(ws10, 4, ["segmen", "pelanggan", "% pelanggan", "net_revenue", "% revenue", "rata2 revenue/pelanggan", "rata2 order", "definisi"])
SEG = ["Champions", "Loyal", "Promising", "Need Attention", "At Risk", "Hibernating"]
DEF = {"Champions": "R>=4 dan F>=4", "Loyal": "R>=3 dan F>=3 (bukan Champions)", "Promising": "R>=4 dan F<=2 (baru/belum sering)", "Need Attention": "R=3 dan F<=2",
       "At Risk": "R<=2 dan F>=3 (dulu sering, sekarang lama tidak order)", "Hibernating": "R<=2 dan F<=2"}
rng = lambda col: f"'T10 Pelanggan'!${col}$4:${col}${wd_last}"
rs_t = 5 + len(SEG)
for i, s in enumerate(SEG):
    r = 5 + i; put(ws10, r, 1, s); put(ws10, r, 2, f'=COUNTIF({rng("H")},A{r})', INT); put(ws10, r, 3, f"=B{r}/B${rs_t}", PCT)
    put(ws10, r, 4, f'=SUMIF({rng("H")},A{r},{rng("D")})', RP); put(ws10, r, 5, f"=D{r}/D${rs_t}", PCT); put(ws10, r, 6, f"=IF(B{r}=0,0,D{r}/B{r})", RP)
    put(ws10, r, 7, f'=IF(B{r}=0,0,SUMIF({rng("H")},A{r},{rng("C")})/B{r})', DEC); ws10.cell(row=r, column=8, value=DEF[s]).font = Font(name=F, size=9)
put(ws10, rs_t, 1, "TOTAL", bold=True, fill=TOT)
for j, col in [(2, "B"), (4, "D")]: put(ws10, rs_t, j, f"=SUM({col}5:{col}{rs_t-1})", RP, True, fill=TOT)
put(ws10, rs_t, 3, f"=SUM(C5:C{rs_t-1})", PCT, True, fill=TOT); put(ws10, rs_t, 5, f"=SUM(E5:E{rs_t-1})", PCT, True, fill=TOT); put(ws10, rs_t, 6, f"=D{rs_t}/B{rs_t}", RP, True, fill=TOT)
put(ws10, rs_t, 7, f'=SUM({rng("C")})/B{rs_t}', DEC, True, fill=TOT)
# Pareto
p0 = rs_t + 3
ws10.cell(row=p0 - 1, column=1, value="Pareto: konsentrasi revenue per desil pelanggan (urut revenue)").font = Font(name=F, bold=True)
header(ws10, p0, ["desil", "dari rank", "sampai rank", "pelanggan", "net_revenue", "% revenue", "% kumulatif"])
n = len(g); bounds = np.array_split(np.arange(1, n + 1), 10)
for i, b in enumerate(bounds):
    r = p0 + 1 + i; put(ws10, r, 1, f"Desil {i+1}" + (" (teratas)" if i == 0 else "")); put(ws10, r, 2, int(b[0]), INT, inp=True); put(ws10, r, 3, int(b[-1]), INT, inp=True)
    put(ws10, r, 4, f"=C{r}-B{r}+1", INT); put(ws10, r, 5, f'=SUMIFS({rng("D")},{rng("I")},">="&B{r},{rng("I")},"<="&C{r})', RP)
    put(ws10, r, 6, f"=E{r}/$E${p0+11}", PCT); put(ws10, r, 7, f"=SUM(F${p0+1}:F{r})", PCT)
rpt = p0 + 11
put(ws10, rpt, 1, "TOTAL", bold=True, fill=TOT); put(ws10, rpt, 4, f"=SUM(D{p0+1}:D{rpt-1})", INT, True, fill=TOT); put(ws10, rpt, 5, f"=SUM(E{p0+1}:E{rpt-1})", RP, True, fill=TOT)
put(ws10, rpt, 6, f"=SUM(F{p0+1}:F{rpt-1})", PCT, True, fill=TOT); put(ws10, rpt, 2, "", fill=TOT); put(ws10, rpt, 3, "", fill=TOT); put(ws10, rpt, 7, "", fill=TOT)
put(ws10, rpt + 1, 1, "Revenue dari 20% pelanggan teratas", bold=True); put(ws10, rpt + 1, 6, f"=G{p0+2}", PCT, True)
top20 = g.M.iloc[:int(np.ceil(0.2 * n))].sum() / g.M.sum()
seg_rev = g.groupby("segmen").M.sum() / g.M.sum(); seg_n = g.segmen.value_counts(normalize=True)
risk_rev = seg_rev.get("At Risk", 0); risk_n = seg_n.get("At Risk", 0)
r_min = int(g[g.segmen == "At Risk"].R.min()); n80 = int(np.argmax(g.M.cumsum().values / g.M.sum() >= 0.8) + 1)
note(ws10, rpt + 3, f"Insight: 20% pelanggan teratas ({int(np.ceil(0.2*n))} dari {n}) menyumbang {top20:.1%} revenue; 80% revenue baru tercapai di ~{n80/n:.0%} pelanggan teratas. Terkonsentrasi, tetapi tidak seekstrem aturan 80/20. "
     f"Champions {seg_n['Champions']:.0%} pelanggan -> {seg_rev['Champions']:.0%} revenue. Segmen At Risk (dulu >=3 order, kini >= {r_min} hari tidak order) = {risk_n:.0%} pelanggan dan {risk_rev:.0%} revenue historis dengan rata-rata Rp {g[g.segmen=='At Risk'].M.mean()/1e6:.1f} jt/pelanggan: sasaran win-back paling jelas.", cols=8, bold=True)
note(ws10, rpt + 4, "Definisi & asumsi: recency dihitung dari 2026-10-31; skor R/M memakai kuintil rank (ties dipecah berdasar urutan), skor F memakai ambang tetap supaya deterministik. Segmen mengikuti aturan berurutan di kolom 'definisi'. Pelanggan yatim ikut dihitung karena RFM tidak butuh atribut pelanggan.", cols=8)
widths(ws10, {"A": 34, "B": 12, "C": 12, "D": 16, "E": 16, "F": 22, "G": 14, "H": 52})
ch = BarChart(); ch.type = "col"; ch.title = "% revenue per segmen RFM"
ch.add_data(Reference(ws10, min_col=5, min_row=5, max_row=rs_t - 1)); ch.set_categories(Reference(ws10, min_col=1, min_row=5, max_row=rs_t - 1))
chart_fix(ch); ch.y_axis.number_format = "0%"; ch.height, ch.width = 8, 14; ws10.add_chart(ch, "J4")

# ====================================================================
# CATATAN & CEK
# ====================================================================
wc = wb.create_sheet("Catatan & Cek"); title(wc, "Definisi & rekonsiliasi level 3")
defs = [("Basis revenue", "Completed berharga (2.282 order), net_revenue = unit_price x qty x (1 - diskon) - sama dengan level 2."),
        ("Pelanggan aktif T7", "Pelanggan unik dengan >=1 order Completed berharga dalam periode 3 bulan."),
        ("Aktif di cohort (T9)", "Pelanggan dengan >=1 order Completed (semua, termasuk tanpa harga) di bulan ke-N; aktivitas tidak butuh harga."),
        ("RFM (T10)", f"Tanggal acuan {REF_DATE:%Y-%m-%d}; basis Completed berharga; 846 pelanggan punya revenue."),
        ("Uji statistik", "Kruskal-Wallis, Welch t-test, chi-square (scipy); p-value ada di sheet T8.")]
for i, (k, v) in enumerate(defs): wc.cell(row=3 + i, column=1, value=k).font = Font(name=F, bold=True); wc.cell(row=3 + i, column=2, value=v).font = Font(name=F)
r = 3 + len(defs) + 1; wc.cell(row=r, column=1, value="REKONSILIASI").font = Font(name=F, bold=True, size=12)
items = [("Acuan total net_revenue (level 1)", REF_TOTAL, RP, True),
         ("T8 total net_revenue channel", f"='T8 Channel'!D{rt8}", RP, False), ("T10 total revenue per segmen", f"='T10 RFM'!D{rs_t}", RP, False), ("T10 total revenue per desil", f"='T10 RFM'!E{rpt}", RP, False),
         ("Selisih T8 vs acuan", f"=B{r+2}-B{r+1}", RP, False), ("Selisih T10 segmen vs acuan", f"=B{r+3}-B{r+1}", RP, False), ("Selisih T10 desil vs acuan", f"=B{r+4}-B{r+1}", RP, False),
         ("T7 cek dekomposisi A (harus 0)", f"='T7 Dekomposisi'!B{posA['chk']}", RP, False), ("T7 cek dekomposisi B (harus 0)", f"='T7 Dekomposisi'!B{posB['chk']}", RP, False),
         ("T7 cek mix+dalam-kategori A (harus 0)", f"='T7 Dekomposisi'!K{posA['catchk']}", RP, False), ("T7 cek mix+dalam-kategori B (harus 0)", f"='T7 Dekomposisi'!K{posB['catchk']}", RP, False),
         ("T9 jumlah ukuran cohort (harus = 1.200 pelanggan)", f"='T9 Cohort'!B{r_last+1}", INT, False), ("T10 jumlah pelanggan di segmen", f"='T10 RFM'!B{rs_t}", INT, False)]
for i, (k, v, fmt, inp) in enumerate(items):
    wc.cell(row=r + 1 + i, column=1, value=k).font = Font(name=F); cell = wc.cell(row=r + 1 + i, column=2, value=v); cell.number_format = fmt; cell.font = Font(name=F, color="0000FF" if inp else "000000")
rs_ = r + 1 + len(items)
wc.cell(row=rs_, column=1, value="STATUS").font = Font(name=F, bold=True)
wc.cell(row=rs_, column=2, value=f'=IF(AND(B{r+5}=0,B{r+6}=0,B{r+7}=0,B{r+8}=0,B{r+9}=0,B{r+10}=0,B{r+11}=0,B{r+12}=1200,B{r+13}={len(g)}),"OK: semua rekonsiliasi lolos","CEK ULANG")').font = Font(name=F, bold=True, color="006100")
widths(wc, {"A": 48, "B": 90})
wb.save(OUT); print("saved", OUT)
