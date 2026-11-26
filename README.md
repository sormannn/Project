# Case: Kenapa Pertumbuhan Revenue TokoNusa Melambat?

## Konteks
Kamu adalah Data Analyst di **TokoNusa**, e-commerce fiktif di Indonesia. Head of Growth bilang:
> "Revenue 3 bulan terakhir (Agu–Okt 2026) tumbuh lambat dibanding awal tahun, padahal budget iklan naik 30%. Saya butuh tahu kenapa dan apa yang harus kita lakukan. Presentasi ke direksi Jumat."

## Data (folder ini)
| File | Isi |
|---|---|
| `customers.csv` | 1.200 pelanggan: kota, channel akuisisi, tanggal daftar, gender |
| `orders.csv` | Transaksi Jan 2025 – Okt 2026: kategori, harga, qty, diskon, status, metode bayar, ongkir |

Catatan: data **sengaja kotor** (duplikat, nilai kosong, qty negatif, format tanggal & huruf tidak konsisten, customer_id yatim). Bagian dari tantangan.

## Tugas

### Level 1 - Data cleaning & validasi
1. Profil data: jumlah baris, null, duplikat, tipe kolom.
2. Temukan semua masalah kualitas data, putuskan perlakuannya (hapus / impute / flag) dan **dokumentasikan alasannya**.
3. Definisikan "revenue" yang benar: apakah Cancelled dan Returned dihitung? Diskon dan ongkir?

### Level 2 - Analisis deskriptif (SQL / pandas / Excel)
4. Revenue, jumlah order, AOV, dan jumlah pelanggan aktif per bulan.
5. Revenue per kategori & per kota. Mana yang berkontribusi paling besar?
6. Tingkat cancel/return per kategori & metode pembayaran (COD?).

### Level 3 - Diagnosis
7. Breakdown pertumbuhan MoM: karena volume order, AOV, atau jumlah pelanggan?
8. Bandingkan channel akuisisi: jumlah pelanggan baru, revenue/pelanggan, dan **net revenue setelah diskon**. Apakah Ads benar-benar efisien dibanding Organic/Referral?
9. Analisis **cohort retention** bulanan berdasarkan bulan signup.
10. Segmentasi **RFM**; berapa % revenue datang dari 20% pelanggan teratas?

### Level 4 - Rekomendasi & storytelling
11. Buat maksimal **5 slide / 1 dashboard** untuk direksi: temuan utama, penyebab, 3 rekomendasi dengan estimasi dampak.
12. Rancang **A/B test** untuk salah satu rekomendasimu (hipotesis, metrik utama, guardrail, ukuran sampel kasar).

## Bonus
- Hitung CLV sederhana per channel.
- Deteksi anomali (hari dengan lonjakan/penurunan aneh).
- Tulis query SQL yang sama di dua dialek (mis. PostgreSQL & BigQuery).

## Cara menilai diri sendiri
- Apakah asumsi dan definisi metrikmu tertulis jelas?
- Apakah angkamu bisa direkonsiliasi (total per kategori = total keseluruhan)?
- Apakah rekomendasi mengikuti dari data, bukan sekadar deskripsi grafik?
- Bisa dijelaskan ke non-teknis dalam 2 menit?
