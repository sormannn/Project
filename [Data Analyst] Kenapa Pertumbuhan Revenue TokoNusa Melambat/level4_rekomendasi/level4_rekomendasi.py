"""Level 4 - Rekomendasi & storytelling (tugas 11-12).
Jalankan dari root repo (setelah level 1):  python level4_rekomendasi/level4_rekomendasi.py
Output: charts/*.png, tugas11_ringkasan_direksi.md, tugas12_ab_test.md. Semua angka dihitung dari data bersih.
"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm

ROOT = Path(__file__).resolve().parent.parent; OUT = Path(__file__).resolve().parent; CH = OUT / "charts"; CH.mkdir(exist_ok=True)
REF = pd.Timestamp("2026-10-31")
o = pd.read_csv(ROOT / "level1_cleaning/orders_clean.csv", parse_dates=["order_date"])
c = pd.read_csv(ROOT / "level1_cleaning/customers_clean.csv", parse_dates=["signup_date"])
o["gross"] = o.unit_price * o.quantity; o["rev"] = o.gross * (1 - o.discount_pct)
ca = o[o.status == "Completed"].copy(); comp = ca[ca.unit_price.notna()].copy(); comp["bulan"] = comp.order_date.dt.strftime("%Y-%m")

# ---- format Indonesia (koma desimal) ----
def n1(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def pct(x, d=1): return n1(x * 100, d) + "%"
def jt(x, d=0): return "Rp " + n1(x / 1e6, d) + " jt"
def spct(x, d=1): return ("+" if x >= 0 else "-") + pct(abs(x), d)
BULAN = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"}
def per(a, b): return comp[(comp.order_date >= a) & (comp.order_date <= b)]
p26, p25, q26 = per("2026-08-01", "2026-10-31"), per("2025-08-01", "2025-10-31"), per("2026-05-01", "2026-07-31")
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
NAVY, RED, GREY, GREEN = "#1F3864", "#C0392B", "#8C8C8C", "#2E8B57"

# =============== ANGKA UTAMA ===============
rev26, rev25, revq = p26.rev.sum(), p25.rev.sum(), q26.rev.sum()
g_yoy, g_qoq = rev26 / rev25 - 1, rev26 / revq - 1
L = (rev26 - rev25) / np.log(rev26 / rev25)
contrib = {"Pelanggan aktif": p26.customer_id.nunique() / p25.customer_id.nunique(),
           "Order per pelanggan": (len(p26) / p26.customer_id.nunique()) / (len(p25) / p25.customer_id.nunique()), "AOV": p26.rev.mean() / p25.rev.mean()}
contrib = {k: L * np.log(v) / rev25 for k, v in contrib.items()}
CATS = ["Elektronik", "Rumah Tangga", "Olahraga", "Fashion", "Kecantikan"]
s25, s26 = p25.category.value_counts(normalize=True), p26.category.value_counts(normalize=True)
mix = sum((s26[k] - s25[k]) * p25[p25.category == k].rev.mean() for k in CATS); mix_share = mix / (p26.rev.mean() - p25.rev.mean())
d25, d26 = 1 - rev25 / p25.gross.sum(), 1 - rev26 / p26.gross.sum()
aov_e = p26[p26.category == "Elektronik"].rev.mean(); aov_ne = p26[p26.category != "Elektronik"].rev.mean()

x = comp.merge(c[["customer_id", "acquisition_channel", "signup_date"]], on="customer_id", how="left"); x["ch"] = x.acquisition_channel.fillna("Tidak diketahui")
chn = x[x.ch != "Tidak diketahui"].groupby("ch").agg(rev=("rev", "sum"), gross=("gross", "sum")); chn["disc"] = 1 - chn.rev / chn.gross
signed = c.groupby("acquisition_channel").size(); chn["rps"] = chn.rev / signed
nonorg = x[(x.ch != "Tidak diketahui") & (x.ch != "Organic")]; last12 = nonorg[nonorg.order_date > REF - pd.DateOffset(years=1)]
disc_rp12 = (last12.gross - last12.rev).sum(); disc_rate_nonorg = 1 - last12.rev.sum() / last12.gross.sum()
last12_rev_all = comp[comp.order_date > REF - pd.DateOffset(years=1)].rev.sum()

# retention (rata-rata tertimbang M0..M12)
cu = ca.merge(c[["customer_id", "signup_date"]], on="customer_id"); cu["off"] = (cu.order_date.dt.year * 12 + cu.order_date.dt.month) - (cu.signup_date.dt.year * 12 + cu.signup_date.dt.month)
c["cohort"] = c.signup_date.dt.to_period("M"); cu = cu.merge(c[["customer_id", "cohort"]], on="customer_id")
END = REF.year * 12 + REF.month; size = c.groupby("cohort").size(); act = cu.groupby(["cohort", "off"]).customer_id.nunique().unstack(fill_value=0)
ret = []
for k in range(13):
    obs = [p for p in size.index if END - (p.year * 12 + p.month) >= k]; ret.append(act.reindex(index=obs, columns=[k], fill_value=0)[k].sum() / size[obs].sum())
# RFM (sama dengan level 3)
g = comp.groupby("customer_id").agg(last=("order_date", "max"), F=("order_id", "count"), M=("rev", "sum")).reset_index(); g["R"] = (REF - g["last"]).dt.days
g["Rs"] = pd.qcut(g.R.rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int); g["Fs"] = pd.cut(g.F, [0, 1, 2, 3, 5, 999], labels=[1, 2, 3, 4, 5]).astype(int)
def seg(r):
    if r.Rs >= 4 and r.Fs >= 4: return "Champions"
    if r.Rs >= 3 and r.Fs >= 3: return "Loyal"
    if r.Rs >= 4 and r.Fs <= 2: return "Promising"
    if r.Rs <= 2 and r.Fs >= 3: return "At Risk"
    if r.Rs <= 2 and r.Fs <= 2: return "Hibernating"
    return "Need Attention"
g["seg"] = g.apply(seg, axis=1); SEG = ["Champions", "Loyal", "Promising", "Need Attention", "At Risk", "Hibernating"]
sn = g.seg.value_counts(normalize=True).reindex(SEG); sr = (g.groupby("seg").M.sum() / g.M.sum()).reindex(SEG)
gs = g.sort_values("M", ascending=False); top20 = gs.M.iloc[:int(np.ceil(.2 * len(gs)))].sum() / gs.M.sum()
last_signup = c.signup_date.max()

# =============== GRAFIK ===============
m = comp.groupby("bulan").agg(rev=("rev", "sum"), n=("order_id", "count")); m["aov"] = m.rev / m.n
fig, ax = plt.subplots(figsize=(9, 3.8)); ax.bar(m.index, m.rev / 1e6, color=NAVY); ax.set_ylabel("Net revenue (Rp juta)"); ax.set_xticks(range(0, len(m), 3)); ax.set_xticklabels(m.index[::3], rotation=0)
ax2 = ax.twinx(); ax2.plot(m.index, m.aov / 1e6, color=RED, marker="o", ms=3); ax2.set_ylabel("AOV (Rp juta)", color=RED); ax2.spines["right"].set_visible(True)
ax.set_title("Revenue mendatar sejak awal 2026; AOV turun dari puncaknya"); fig.tight_layout(); fig.savefig(CH / "01_revenue_aov_bulanan.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 3.6)); labs = list(contrib) + ["Total revenue"]; vals = [v * 100 for v in contrib.values()] + [g_yoy * 100]
ax.bar(labs, vals, color=[GREEN if v > 0 else RED for v in vals[:-1]] + [NAVY]); ax.axhline(0, color="black", lw=.8)
for i, v in enumerate(vals): ax.text(i, v + (1 if v >= 0 else -2.5), f"{v:+.1f}".replace(".", ",") + " poin", ha="center", fontsize=9)
ax.set_ylabel("Kontribusi ke pertumbuhan (poin %)"); ax.set_title("YoY Agu-Okt: pelanggan naik 21%, tapi AOV menggerus hasilnya"); ax.set_ylim(min(vals) - 6, max(vals) + 6)
fig.tight_layout(); fig.savefig(CH / "02_dekomposisi_yoy.png", dpi=150); plt.close(fig)

cs = chn.sort_values("disc", ascending=False); fig, ax = plt.subplots(figsize=(7.5, 3.6))
ax.bar(cs.index, cs.disc * 100, color=[GREEN if k == "Organic" else NAVY for k in cs.index])
for i, (k, r) in enumerate(cs.iterrows()): ax.text(i, r.disc * 100 + .3, f"{r.disc*100:.1f}%".replace(".", ",") + f"\nRp {r.rps/1e6:.2f} jt/plg".replace(".", ","), ha="center", fontsize=8)
ax.set_ylabel("Diskon efektif (%)"); ax.set_ylim(0, cs.disc.max() * 100 + 4); ax.set_title("Diskon efektif per channel (label: revenue per pelanggan signup)")
fig.tight_layout(); fig.savefig(CH / "03_diskon_channel.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 3.4)); ax.plot(range(13), [r * 100 for r in ret], marker="o", color=NAVY); ax.set_xlabel("Bulan sejak signup"); ax.set_ylabel("% pelanggan aktif")
ax.set_title("Retention memuncak di M2 lalu meluruh"); ax.set_xticks(range(13)); fig.tight_layout(); fig.savefig(CH / "04_retention.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 3.6)); w = .38; xs = np.arange(len(SEG)); ax.bar(xs - w / 2, sn * 100, w, label="% pelanggan", color=GREY); ax.bar(xs + w / 2, sr * 100, w, label="% revenue", color=NAVY)
ax.set_xticks(xs); ax.set_xticklabels(SEG, fontsize=8); ax.legend(); ax.set_ylabel("%"); ax.set_title("Segmen RFM: porsi pelanggan vs porsi revenue"); fig.tight_layout(); fig.savefig(CH / "05_rfm.png", dpi=150); plt.close(fig)

# =============== TUGAS 12: A/B TEST ===============
def nreq(p0, p1, a=.05, pw=.8):
    z = norm.ppf(1 - a / 2) + norm.ppf(pw); pb = (p0 + p1) / 2; return int(np.ceil(z ** 2 * 2 * pb * (1 - pb) / (p1 - p0) ** 2))
def snap(asof, lo, hi, h=60):
    asof = pd.Timestamp(asof); hh = comp[comp.order_date <= asof]; gg = hh.groupby("customer_id").agg(last=("order_date", "max"))
    gg["R"] = (asof - gg["last"]).dt.days; pool = gg[(gg.R >= lo) & (gg.R <= hi)]
    fut = comp[(comp.order_date > asof) & (comp.order_date <= asof + pd.Timedelta(days=h))]; return len(pool), int(pool.index.isin(fut.customer_id).sum())
snaps = [snap(d, 60, 150) for d in pd.date_range("2026-01-31", "2026-08-31", freq="ME")]
pool_m = np.mean([s[0] for s in snaps]); base = sum(s[1] for s in snaps) / sum(s[0] for s in snaps)
avg_ship = o[o.status == "Completed"].shipping_fee.mean(); aov_now = p26.rev.mean()
rows = []
for d in (.05, .08, .10):
    n = nreq(base, base + d); rows.append((d, n, 2 * n, 2 * n / pool_m))
# dampak ilustratif
saving_third = disc_rp12 / 3
price_up = (1 - disc_rate_nonorg * 2 / 3) / (1 - disc_rate_nonorg) - 1       # kenaikan harga bersih bila diskon dipotong 1/3
shift_orders = len(p26) * (s25["Elektronik"] - s26["Elektronik"]); mix_gain = shift_orders * (aov_e - aov_ne)
lift = .08; extra_per_month = pool_m * lift; extra_rev_month = extra_per_month * aov_now; avg_month_rev = p26.rev.sum() / 3

# =============== TULIS MARKDOWN ===============
md11 = f"""# Tugas 11 - Ringkasan untuk direksi: kenapa revenue TokoNusa melambat?

> Basis angka: order Completed berharga, net revenue = unit_price x qty x (1 - diskon). Periode "3 bulan terakhir" = Agu-Okt 2026. Detail & rekonsiliasi: `level2_deskriptif/` dan `level3_diagnosis/`.

## Slide 1 - Kesimpulan
**Revenue praktis datar walau basis pelanggan naik.** Agu-Okt 2026 = {jt(rev26)}: **{spct(g_yoy)} vs tahun lalu** dan **{spct(g_qoq)} vs Mei-Jul 2026**. Pelanggan aktif naik 21% YoY, tetapi nilai per order (AOV) turun {pct(1 - p26.rev.mean()/p25.rev.mean(), 0)} karena **order bergeser dari Elektronik** (bukan karena diskon atau frekuensi order).
Tiga langkah: (1) rasionalisasi diskon channel berbayar, (2) pulihkan mix Elektronik, (3) reaktivasi pelanggan yang mulai tidak aktif.

## Slide 2 - Apa yang terjadi
![revenue dan AOV bulanan](charts/01_revenue_aov_bulanan.png)
- Kenaikan 2025 sebagian besar efek basis pelanggan yang dibangun dari nol; sejak 2026 revenue bergerak di kisaran Rp 92-144 jt/bulan.
- Agu-Okt 2026: {jt(rev26)}; Mei-Jul 2026: {jt(revq)}; Agu-Okt 2025: {jt(rev25)}.

## Slide 3 - Kenapa: AOV, bukan jumlah pelanggan atau frekuensi
![dekomposisi YoY](charts/02_dekomposisi_yoy.png)
- Pelanggan aktif {n1(p25.customer_id.nunique(),0)} -> {n1(p26.customer_id.nunique(),0)} menambah **{n1(contrib['Pelanggan aktif']*100)} poin** pertumbuhan; order per pelanggan nyaris tidak berubah ({n1(contrib['Order per pelanggan']*100)} poin); **AOV menggerus {n1(abs(contrib['AOV'])*100)} poin**.
- **{pct(mix_share, 0)} penurunan AOV adalah efek mix:** share order Elektronik turun dari {pct(s25['Elektronik'])} ke {pct(s26['Elektronik'])}. AOV Elektronik {jt(aov_e,1)} vs {jt(aov_ne,1)} untuk kategori lain (gabungan), dan Elektronik = 56% revenue total.
- **Bukan diskon:** diskon efektif justru turun dari {pct(d25)} ke {pct(d26)}.

## Slide 4 - Pelanggan & channel
![diskon per channel](charts/03_diskon_channel.png)
- Channel berbayar (Ads), Referral, dan Email memberi diskon efektif {pct(chn.drop('Organic').disc.min())}-{pct(chn.drop('Organic').disc.max())}; **Organic hanya {pct(chn.loc['Organic','disc'])}**. Revenue per pelanggan antar channel **tidak berbeda signifikan** (Kruskal-Wallis p=0,30): pelanggan berbayar tidak lebih bernilai, tetapi lebih "disubsidi".
![retention](charts/04_retention.png)
- Pelanggan aktif memuncak {pct(ret[2],0)} di bulan ke-2 setelah signup lalu meluruh (M6 {pct(ret[6],0)}, M12 {pct(ret[12],0)}): sebagian besar pelanggan berhenti setelah beberapa order.
![rfm](charts/05_rfm.png)
- 20% pelanggan teratas = {pct(top20)} revenue. Segmen **At Risk** = {pct(sn['At Risk'],0)} pelanggan dan {pct(sr['At Risk'],0)} revenue historis.

## Slide 5 - Rekomendasi
| # | Rekomendasi | Dasar | Estimasi dampak (ilustratif) |
|---|---|---|---|
| 1 | **Rasionalisasi diskon channel berbayar/Referral/Email**: uji pemotongan sepertiga kedalaman diskon | Diskon ~{pct(disc_rate_nonorg)} vs Organic {pct(chn.loc['Organic','disc'])} tanpa revenue/pelanggan lebih tinggi | Diskon 12 bulan terakhir di channel ini {jt(disc_rp12)}; memotong sepertiganya menghemat sampai ~{jt(saving_third)} (batas atas, jika volume order tidak turun). **Impas bila order turun < {pct(price_up/(1+price_up))}** |
| 2 | **Pulihkan mix Elektronik**: bundling/cross-sell Elektronik, prioritas stok & iklan produk Elektronik | Share Elektronik turun {n1((s25['Elektronik']-s26['Elektronik'])*100)} poin; satu order Elektronik ~ {n1(aov_e/aov_ne,1)}x order lain | Bila share kembali ke level Agu-Okt 2025: ~{n1(shift_orders,0)} order/kuartal bergeser ke Elektronik = **~{jt(mix_gain)} per kuartal** (sensitivitas, bukan prakiraan) |
| 3 | **Reaktivasi dini** pelanggan yang 60-150 hari tidak order (voucher ongkir + pengingat) | Retention meluruh setelah M2-M3; baseline reorder 60 hari di segmen ini {pct(base)} | Lift +8 poin pada ~{n1(pool_m,0)} pelanggan/bulan = ~{n1(extra_per_month,0)} order tambahan/bulan = ~{jt(extra_rev_month)}/bulan (~{pct(extra_rev_month/avg_month_rev,0)} dari revenue bulanan), dikurangi biaya voucher. **Diuji dulu lewat A/B (tugas 12)** |

**Perlu diverifikasi:** (a) data signup berhenti {last_signup.day} {BULAN[last_signup.month]} {last_signup.year} - tidak ada pelanggan baru Sep-Okt 2026; konfirmasi apakah akuisisi benar-benar berhenti atau data belum lengkap. (b) Biaya iklan tidak ada di data, jadi klaim "budget naik 30%" tidak dapat dihubungkan ke hasil; butuh CAC/ROAS per channel. (c) 25 baris quantity negatif diasumsikan salah input; pengaruhnya kecil (20 baris Completed).

## Keterbatasan
Data sintetis/sampel ~2.700 order sehingga selisih kecil antar kelompok (cancel/return, channel) tidak signifikan dan tidak dijadikan dasar rekomendasi. Estimasi dampak adalah sensitivitas dengan asumsi eksplisit, bukan prakiraan.
"""
(OUT / "tugas11_ringkasan_direksi.md").write_text(md11, encoding="utf-8")

tbl = "\n".join(f"| +{int(d*100)} poin ({base*100:.1f}% -> {(base+d)*100:.1f}%) | {n} | {t} | {mo:.1f} bulan |".replace(".", ",") for d, n, t, mo in rows)
md12 = f"""# Tugas 12 - Rancangan A/B test: reaktivasi dini pelanggan

Rekomendasi yang diuji: **#3 reaktivasi dini** (pelanggan mulai tidak aktif). Dipilih karena target & metriknya terukur di data dan intervensinya murah.

## 1. Hipotesis
- **H0:** pengingat + voucher gratis ongkir tidak mengubah peluang pelanggan order kembali dalam 60 hari.
- **H1:** perlakuan menaikkan proporsi pelanggan yang order kembali (Completed) dalam 60 hari setelah masuk eksperimen.

## 2. Populasi & unit randomisasi
- **Unit:** pelanggan (bukan order), diacak 50:50 ke Kontrol / Perlakuan.
- **Kriteria masuk:** pelanggan dengan >=1 order Completed yang **60-150 hari tidak order** pada saat masuk. Pelanggan masuk **bergulir tiap bulan** (rolling enrollment) saat memenuhi kriteria, dan hanya sekali.
- **Dikeluarkan:** pelanggan dengan order berstatus aktif/proses, dan pelanggan yang sudah menerima voucher lain dalam 30 hari.
- **Ukuran kolam:** rata-rata ~{n1(pool_m,0)} pelanggan memenuhi kriteria per bulan (backtest Jan-Agu 2026).

## 3. Perlakuan
- **Kontrol:** tidak ada komunikasi tambahan.
- **Perlakuan:** satu pesan (email/WA) berisi rekomendasi produk berdasarkan kategori yang pernah dibeli + **voucher gratis ongkir** berlaku 14 hari (biaya per voucher terpakai ~ Rp {n1(avg_ship,0)} = rata-rata shipping_fee di data).

## 4. Metrik
| Jenis | Metrik | Definisi |
|---|---|---|
| **Utama** | Reorder rate 60 hari | % pelanggan dengan >=1 order Completed dalam 60 hari sejak masuk |
| Sekunder | Net revenue per pelanggan 60 hari | Rata-rata net revenue (Completed) per pelanggan yang diacak (termasuk yang tidak order) |
| Sekunder | Net revenue setelah biaya voucher | Net revenue - (jumlah voucher terpakai x biaya ongkir) |
| **Guardrail** | Cancel + return rate dari order baru | Tidak boleh naik > 2 poin vs kontrol |
| **Guardrail** | Opt-out / keluhan komunikasi | Tidak boleh naik signifikan |
| **Guardrail** | Biaya per order tambahan | (voucher terpakai x biaya ongkir) / (order perlakuan - order kontrol); harus lebih kecil dari net revenue per order tambahan |

## 5. Ukuran sampel
Baseline dari backtest data: **{pct(base)}** pelanggan di segmen ini order kembali dalam 60 hari. Uji dua sisi, alpha = 5%, power = 80% (uji dua proporsi).

| Lift minimum yang ingin dideteksi (MDE) | Sampel per kelompok | Total | Lama pengumpulan (kolam ~{n1(pool_m,0)}/bulan) |
|---|---|---|---|
{tbl}

**Keputusan:** target MDE **+8 poin**: cukup besar untuk bernilai bisnis (setara ~{jt(extra_rev_month)}/bulan sebelum biaya voucher, lihat tugas 11) dan masih bisa dicapai dalam **~{rows[1][3]:.0f} bulan** dengan kolam sebesar ini. Bila bisnis tidak bisa menunggu selama itu, perluas kriteria masuk (mis. 45-180 hari) atau terima MDE yang lebih besar (+10 poin). Lift < 5 poin tidak akan terdeteksi dengan data sebesar ini.

## 6. Durasi & aturan keputusan
1. Kunci rancangan sebelum mulai (hipotesis, metrik, MDE, durasi); **jangan mengintip dan berhenti lebih awal** hanya karena p<0,05.
2. Setiap pelanggan diamati penuh 60 hari setelah masuk; analisis setelah kohort terakhir selesai.
3. Analisis: uji dua proporsi (atau regresi logistik dengan kategori produk & lama menjadi pelanggan sebagai kovariat); laporkan selisih dan interval kepercayaan 95%.
4. **Rilis** jika reorder rate naik signifikan DAN net revenue setelah biaya voucher positif DAN guardrail aman. **Ulangi/ubah desain** jika lift tidak signifikan. **Hentikan** jika guardrail dilanggar.

## 7. Risiko & catatan
- Data historis tidak memuat biaya komunikasi, margin, atau opt-in; hitung ROI setelah itu tersedia.
- Pastikan randomisasi dilakukan oleh sistem (hash customer_id), bukan manual, dan cek keseimbangan awal (recency, jumlah order, kategori) antar kelompok.
- Efek novelty: voucher pertama bisa menghasilkan lonjakan yang tidak bertahan; lacak juga order ke-2 setelah voucher.
"""
(OUT / "tugas12_ab_test.md").write_text(md12, encoding="utf-8")
print("selesai | baseline", round(base, 3), "pool/bulan", round(pool_m, 1), "| contoh n/arm", [(d, n) for d, n, _, _ in rows])
