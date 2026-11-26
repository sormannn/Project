# Tugas 12 - Rancangan A/B test: reaktivasi dini pelanggan

Rekomendasi yang diuji: **#3 reaktivasi dini** (pelanggan mulai tidak aktif). Dipilih karena target & metriknya terukur di data dan intervensinya murah.

## 1. Hipotesis
- **H0:** pengingat + voucher gratis ongkir tidak mengubah peluang pelanggan order kembali dalam 60 hari.
- **H1:** perlakuan menaikkan proporsi pelanggan yang order kembali (Completed) dalam 60 hari setelah masuk eksperimen.

## 2. Populasi & unit randomisasi
- **Unit:** pelanggan (bukan order), diacak 50:50 ke Kontrol / Perlakuan.
- **Kriteria masuk:** pelanggan dengan >=1 order Completed yang **60-150 hari tidak order** pada saat masuk. Pelanggan masuk **bergulir tiap bulan** (rolling enrollment) saat memenuhi kriteria, dan hanya sekali.
- **Dikeluarkan:** pelanggan dengan order berstatus aktif/proses, dan pelanggan yang sudah menerima voucher lain dalam 30 hari.
- **Ukuran kolam:** rata-rata ~144 pelanggan memenuhi kriteria per bulan (backtest Jan-Agu 2026).

## 3. Perlakuan
- **Kontrol:** tidak ada komunikasi tambahan.
- **Perlakuan:** satu pesan (email/WA) berisi rekomendasi produk berdasarkan kategori yang pernah dibeli + **voucher gratis ongkir** berlaku 14 hari (biaya per voucher terpakai ~ Rp 13.472 = rata-rata shipping_fee di data).

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
Baseline dari backtest data: **17,8%** pelanggan di segmen ini order kembali dalam 60 hari. Uji dua sisi, alpha = 5%, power = 80% (uji dua proporsi).

| Lift minimum yang ingin dideteksi (MDE) | Sampel per kelompok | Total | Lama pengumpulan (kolam ~144/bulan) |
|---|---|---|---|
| +5 poin (17,8% -> 22,8%) | 1018 | 2036 | 14,1 bulan |
| +8 poin (17,8% -> 25,8%) | 419 | 838 | 5,8 bulan |
| +10 poin (17,8% -> 27,8%) | 277 | 554 | 3,8 bulan |

**Keputusan:** target MDE **+8 poin**: cukup besar untuk bernilai bisnis (setara ~Rp 10 jt/bulan sebelum biaya voucher, lihat tugas 11) dan masih bisa dicapai dalam **~6 bulan** dengan kolam sebesar ini. Bila bisnis tidak bisa menunggu selama itu, perluas kriteria masuk (mis. 45-180 hari) atau terima MDE yang lebih besar (+10 poin). Lift < 5 poin tidak akan terdeteksi dengan data sebesar ini.

## 6. Durasi & aturan keputusan
1. Kunci rancangan sebelum mulai (hipotesis, metrik, MDE, durasi); **jangan mengintip dan berhenti lebih awal** hanya karena p<0,05.
2. Setiap pelanggan diamati penuh 60 hari setelah masuk; analisis setelah kohort terakhir selesai.
3. Analisis: uji dua proporsi (atau regresi logistik dengan kategori produk & lama menjadi pelanggan sebagai kovariat); laporkan selisih dan interval kepercayaan 95%.
4. **Rilis** jika reorder rate naik signifikan DAN net revenue setelah biaya voucher positif DAN guardrail aman. **Ulangi/ubah desain** jika lift tidak signifikan. **Hentikan** jika guardrail dilanggar.

## 7. Risiko & catatan
- Data historis tidak memuat biaya komunikasi, margin, atau opt-in; hitung ROI setelah itu tersedia.
- Pastikan randomisasi dilakukan oleh sistem (hash customer_id), bukan manual, dan cek keseimbangan awal (recency, jumlah order, kategori) antar kelompok.
- Efek novelty: voucher pertama bisa menghasilkan lonjakan yang tidak bertahan; lacak juga order ke-2 setelah voucher.
