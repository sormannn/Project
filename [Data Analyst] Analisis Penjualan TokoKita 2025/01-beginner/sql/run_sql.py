"""Menjalankan queries.sql di SQLite (in-memory) tanpa perlu instal database."""
from pathlib import Path
import re
import sqlite3
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

def jalankan():
    con = sqlite3.connect(":memory:")
    pd.read_csv(BASE / "data" / "penjualan_tokokita_raw.csv").to_sql(
        "penjualan_raw", con, index=False)
    teks = (BASE / "sql" / "queries.sql").read_text(encoding="utf-8")
    bagian = re.split(r"^-- name: (\w+)\s*$", teks, flags=re.M)[1:]
    hasil = {}
    for nama, sql in zip(bagian[::2], bagian[1::2]):
        if nama == "cleaning":
            con.executescript(sql)
        else:
            hasil[nama] = pd.read_sql_query(sql, con)
    return hasil

if __name__ == "__main__":
    for nama, tabel in jalankan().items():
        print(f"\n=== {nama} ===\n{tabel.to_string(index=False)}")
