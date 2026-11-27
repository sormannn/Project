# Case Study Data Analyst: Kenapa Pertumbuhan Revenue TokoNusa Melambat?

Kunci jawaban (solusi referensi) untuk `case_brief.md`, dipisah per level. Semua angka dihitung ulang dari data mentah lewat skrip Python yang bisa dijalankan ulang.

## Struktur

| Folder | Isi | Tugas |
|---|---|---|
| `data/raw/` | `orders.csv`, `customers.csv` (data mentah, sengaja kotor) | - |
| `level1_cleaning/` | `orders_clean.csv`, `customers_clean.csv`, `cleaning_log.csv`, `level1_cleaning.py` | 1-3 |
| `level2_deskriptif/` | `level2_deskriptif.xlsx` (bulanan, kategori, kota, cancel/return, rekonsiliasi), `level2_deskriptif.py` | 4-6 |
| `level3_diagnosis/` | `level3_diagnosis.xlsx` (dekomposisi, channel, cohort heatmap, RFM & Pareto, rekonsiliasi), `level3_diagnosis.py` | 7-10 |
| `level4_rekomendasi/` | `tugas11_ringkasan_direksi.md`, `tugas12_ab_test.md`, `charts/`, `level4_rekomendasi.py` | 11-12 |

## Cara menjalankan
```bash
pip install -r requirements.txt
./run_all.sh        # atau jalankan skrip tiap level berurutan dari root repo
```
File `.xlsx` memakai formula Excel untuk kolom turunan, total, dan pengecekan; nilai dasar dihitung di pandas (font biru = input hardcode, hitam = formula). Sheet `Catatan & Cek` di tiap workbook berisi definisi dan rekonsiliasi (semua total kembali ke **Rp 1.961.551.150**).

## Definisi kunci
- **Net revenue** = `unit_price x quantity x (1 - discount_pct)`, hanya order **Completed** berharga (2.282 order); ongkir tidak dihitung.
- 34 order Completed tanpa harga keluar dari revenue/AOV; 10 order dari customer yatim tetap dihitung (kota/channel = "Tidak diketahui").
- Quantity negatif (25 baris) diubah dengan `ABS()` dan di-flag; asumsi salah input, perlu konfirmasi pemilik data.

## Ringkasan temuan
1. **Revenue praktis datar** di Agu-Okt 2026 (Rp 339 jt): +4,8% YoY, -1,9% vs Mei-Jul 2026.
2. **Penyebab utama: AOV**, bukan pelanggan atau frekuensi. Pelanggan aktif +21% YoY menyumbang +19,6 poin, AOV menggerus 15,5 poin. 86% penurunan AOV adalah efek mix (share order Elektronik turun 25,4% -> 19,4%). Diskon justru turun.
3. **Channel:** Ads/Referral/Email memberi diskon efektif 8-11% vs Organic 1,6%, tanpa revenue per pelanggan yang lebih tinggi (p=0,30).
4. **Retention** memuncak di M2 (33%) lalu meluruh (M12 = 4%); 20% pelanggan teratas = 57% revenue; segmen At Risk = 17% revenue historis.
5. **Rekomendasi:** rasionalisasi diskon channel berbayar, pulihkan mix Elektronik, reaktivasi dini (diuji lewat A/B test, rancangan di tugas 12).

## Catatan pembelajaran
- Jangan parse kolom tanggal campuran dengan `dayfirst=True`: tanggal ISO dengan hari <= 12 tertukar (953 baris) dan menimbulkan flag palsu "order sebelum signup". Pakai `format=` eksplisit per pola.
- Selisih kecil antar kelompok (cancel/return per kategori, metode bayar) tidak signifikan secara statistik dan tidak dijadikan kesimpulan.
- Data signup berakhir 24 Agu 2026 dan biaya iklan tidak ada di data; keduanya dicatat sebagai hal yang perlu diverifikasi.
