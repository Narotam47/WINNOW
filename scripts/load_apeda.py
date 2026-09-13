#!/usr/bin/env python3
"""Load APEDA millet export data into winnow.db. Input: data/raw/apeda_millet_exports.xls"""
import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
XLS  = ROOT / "data" / "raw" / "apeda_millet_exports.xls"
DB   = ROOT / "data" / "winnow.db"

YEARS = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24"]

ISO3 = {
    "U Arab Emts": "UAE", "Saudi Arab": "SAU", "Kuwait": "KWT",
    "Qatar": "QAT", "Oman": "OMN",
}

COMTRADE_2023 = {"UAE": 8_414_162, "SAU": 1_277_124, "KWT": 357_192,
                 "QAT": 784_544,   "OMN": 6_912_187}

SKIP = {"total", "country", "s.no", "sl.no", ""}

def parse_num(s):
    try: return float(s.strip().replace(",", ""))
    except (ValueError, AttributeError): return None

def parse_rows(path):
    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        # Content lives between <td> spacers as text nodes and <div> siblings
        parts = []
        for child in tr.children:
            if getattr(child, "name", None) == "td":
                continue
            text = child.get_text(strip=True) if hasattr(child, "get_text") else str(child).strip()
            if text:
                parts.append(text)
        if len(parts) < 11 or parts[0].lower() in SKIP:
            continue
        name = parts[0]
        vals = [parse_num(parts[i]) for i in range(1, 6)]
        qtys = [parse_num(parts[i]) for i in range(6, 11)]
        if all(v is None for v in vals):
            continue
        rows.append((name, vals, qtys))
    return rows

def load(conn, rows):
    conn.execute("""CREATE TABLE IF NOT EXISTS apeda_exports (
        id           INTEGER PRIMARY KEY,
        country_name TEXT, country_iso3 TEXT, fiscal_year TEXT,
        value_usd    REAL,  qty_mt REAL, unit_price REAL)""")
    conn.execute("DELETE FROM apeda_exports")
    ins = ("INSERT INTO apeda_exports(country_name,country_iso3,fiscal_year,"
           "value_usd,qty_mt,unit_price) VALUES(?,?,?,?,?,?)")
    n = 0
    for name, vals, qtys in rows:
        iso3 = ISO3.get(name)
        for i, fy in enumerate(YEARS):
            v, q = vals[i], qtys[i]
            up = round(v / (q * 1000), 4) if v and q and q > 0 else None
            conn.execute(ins, (name, iso3, fy, v, q, up)); n += 1
    conn.commit()
    print(f"Loaded {n} rows ({len(rows)} countries × 5 years)")

def print_gcc(conn):
    print(f"\n{'ISO3':<5} {'FY':<9} {'Value USD':>14} {'Qty MT':>10} {'USD/kg':>7}")
    print("─" * 48)
    for iso3, fy, v, q, up in conn.execute(
        "SELECT country_iso3,fiscal_year,value_usd,qty_mt,unit_price "
        "FROM apeda_exports WHERE country_iso3 IS NOT NULL "
        "ORDER BY country_iso3, fiscal_year"
    ).fetchall():
        print(f"{iso3:<5} {fy:<9} {v or 0:>14,.0f} {q or 0:>10,.2f} {up or 0:>7.4f}")

def print_share(conn):
    print(f"\n── India share FY2023-24 vs Comtrade 2023 {'─'*20}")
    print(f"{'ISO3':<5} {'APEDA USD':>14} {'Comtrade USD':>14} {'IND%':>7}")
    print("─" * 44)
    for iso3, ct in sorted(COMTRADE_2023.items()):
        row = conn.execute(
            "SELECT value_usd FROM apeda_exports WHERE country_iso3=? AND fiscal_year='2023-24'",
            (iso3,)).fetchone()
        v = row[0] if row else 0
        share = f"{100*v/ct:.1f}%" if ct else "n/a"
        print(f"{iso3:<5} {v or 0:>14,.0f} {ct:>14,.0f} {share:>7}")

if __name__ == "__main__":
    rows = parse_rows(XLS)
    print(f"Parsed {len(rows)} country rows from {XLS.name}")
    conn = sqlite3.connect(DB)
    load(conn, rows); print_gcc(conn); print_share(conn); conn.close()
