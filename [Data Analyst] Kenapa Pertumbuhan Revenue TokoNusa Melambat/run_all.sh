#!/usr/bin/env bash
# Jalankan seluruh pipeline dari root repo (urutan level penting).
set -e
python level1_cleaning/level1_cleaning.py
python level2_deskriptif/level2_deskriptif.py
python level3_diagnosis/level3_diagnosis.py
python level4_rekomendasi/level4_rekomendasi.py
echo "Selesai. Catatan: file .xlsx yang dibuat ulang berisi formula; buka di Excel/LibreOffice agar nilainya terhitung."
