-- Penyelesaian versi SQL (SQLite). Tabel sumber: penjualan_raw

-- name: cleaning
DROP VIEW IF EXISTS penjualan;
CREATE VIEW penjualan AS
SELECT DISTINCT
    order_id,
    tanggal,
    SUBSTR(tanggal, 1, 7) AS bulan,
    CASE WHEN kota IS NULL THEN 'Tidak Diketahui'
         ELSE UPPER(SUBSTR(TRIM(kota), 1, 1)) || LOWER(SUBSTR(TRIM(kota), 2))
    END AS kota,
    kategori,
    produk,
    CAST(jumlah AS INTEGER) AS jumlah,
    harga_satuan,
    diskon_persen,
    COALESCE(metode_bayar, 'Tidak Diketahui') AS metode_bayar,
    CAST(jumlah AS INTEGER) * harga_satuan * (100 - diskon_persen) / 100 AS pendapatan
FROM penjualan_raw
WHERE jumlah IS NOT NULL;

-- name: kpi
SELECT SUM(pendapatan) AS total_pendapatan,
       COUNT(DISTINCT order_id) AS jumlah_order,
       SUM(jumlah) AS unit_terjual,
       ROUND(1.0 * SUM(pendapatan) / COUNT(DISTINCT order_id)) AS rata_per_order
FROM penjualan;

-- name: bulanan
SELECT bulan, SUM(pendapatan) AS pendapatan
FROM penjualan GROUP BY bulan ORDER BY bulan;

-- name: kategori
SELECT kategori, COUNT(*) AS jumlah_order, SUM(jumlah) AS unit,
       SUM(pendapatan) AS pendapatan,
       ROUND(100.0 * SUM(pendapatan) / (SELECT SUM(pendapatan) FROM penjualan), 1) AS kontribusi_persen
FROM penjualan GROUP BY kategori ORDER BY pendapatan DESC;

-- name: top_produk
SELECT produk, SUM(pendapatan) AS pendapatan
FROM penjualan GROUP BY produk ORDER BY pendapatan DESC LIMIT 5;

-- name: kota
SELECT kota, COUNT(*) AS jumlah_order, SUM(pendapatan) AS pendapatan,
       ROUND(1.0 * SUM(pendapatan) / COUNT(*)) AS rata_per_order
FROM penjualan GROUP BY kota ORDER BY pendapatan DESC;

-- name: metode_bayar
SELECT metode_bayar, COUNT(*) AS jumlah_order,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM penjualan), 1) AS persen
FROM penjualan GROUP BY metode_bayar ORDER BY jumlah_order DESC;
