#!/usr/bin/env python3
"""
Build WINNOW trade database.  Output: data/winnow.db

Data pulls and why each exists:
  gcc_imports_wld  GCC × World imports, HS 100821+100829, 2016-2023.
                   Establishes each market's total millet demand envelope.
  gcc_imports_ind  Same reporters, partner = India (M49 356).
                   Isolates India's supply share per market.
  uae_rx           UAE re-exports (flowCode RX), same HS codes.
                   Enables Jebel Ali netting: true UAE domestic demand =
                   imports minus re-exports.
  ind_exports_gcc  India as reporter, exports (X) to each GCC partner.
                   Cross-validates import-side figures; reveals lanes where
                   the receiving country under-reports or lags in submission.
"""
import os, sys, json, time, sqlite3, urllib.request, urllib.parse, urllib.error
from pathlib import Path

KEY       = os.environ.get("COMTRADE_KEY")
ROOT      = Path(__file__).resolve().parent.parent
CACHE     = ROOT / "data" / "comtrade_cache"
DB        = ROOT / "data" / "winnow.db"
BASE      = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
HS        = "100821,100829"
HS_IND    = "100820,100821,100829"  # adds HS-2012 code; India may report millet under 100820
YRS       = ",".join(str(y) for y in range(2016, 2024))
GCC       = {"784":"UAE","682":"SAU","634":"QAT","512":"OMN","414":"KWT","48":"BHR"}
M49       = {**GCC, "356":"IND", "0":"WLD"}
NAMES     = {"UAE":"United Arab Emirates","SAU":"Saudi Arabia","QAT":"Qatar",
             "OMN":"Oman","KWT":"Kuwait","BHR":"Bahrain","IND":"India","WLD":"World"}
FLOW      = {"M":"import","X":"export","RX":"re_export"}
SUSPECT   = {100, 500, 1000}
GCC_CODES = ",".join(GCC)

def fetch(tag, hs=None, **params):
    path = CACHE / f"{tag}.json"
    if path.exists():
        d = json.loads(path.read_text()).get("data") or []
        print(f"[cache ] {tag}: {len(d)} rows"); return d
    params.update({"cmdCode": hs or HS, "period": YRS})
    url = BASE + "?" + urllib.parse.urlencode(params)
    delay, body = 2, None
    for attempt in range(6):
        req = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": KEY})
        try:
            with urllib.request.urlopen(req, timeout=120) as r: body = r.read(); break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503):
                sys.exit(f"HTTP {e.code} on {tag}: {e.read()[:200].decode('utf8','replace')}")
            print(f"[{e.code}] {tag}: back-off {delay}s (attempt {attempt+1})")
            time.sleep(delay); delay *= 2
    if body is None: sys.exit(f"gave up on {tag} after 6 attempts")
    CACHE.mkdir(parents=True, exist_ok=True); path.write_bytes(body)
    d = json.loads(body).get("data") or []
    n = len(d)
    print(f"[fetch ] {tag}: {n} rows{' <-- SUSPECT' if n in SUSPECT else ''}{' <-- ZERO' if n==0 else ''}")
    return d

def pull_all():
    r  = fetch("gcc_imports_wld", reporterCode=GCC_CODES, partnerCode=0, flowCode="M")
    r += fetch("uae_rx",          reporterCode=784,        partnerCode=0, flowCode="RX")
    # GCC bilateral imports from India (partnerCode=356) always return 0 — GCC countries
    # don't file partner-disaggregated data at HS-6 for this commodity.
    # Use India as reporter instead. Split per partner (comma list unreliable for some
    # reporters), and include HS 100820 for HS-2012 reporters.
    for code, iso3 in GCC.items():
        r += fetch(f"ind_x_{iso3.lower()}", reporterCode=356,
                   partnerCode=int(code), flowCode="X", hs=HS_IND)
    return r


def diagnose_india():
    """Five fresh calls (no cache) to identify why India pulls return 0 rows."""
    def probe(label, **params):
        params["period"] = 2023
        url = BASE + "?" + urllib.parse.urlencode(params)
        print(f"\n[diag] {label}")
        req = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": KEY})
        try:
            with urllib.request.urlopen(req, timeout=60) as r: body = r.read()
            obj = json.loads(body); d = obj.get("data") or []
            print(f"       → {len(d)} rows | count={obj.get('count')}")
            if d:
                s = d[0]
                print(f"       sample: {s.get('reporterISO')}→{s.get('partnerISO')} "
                      f"HS{s.get('cmdCode')} ${s.get('primaryValue',0):,.0f}")
        except Exception as e:
            print(f"       → ERROR: {e}")
    probe("UAE imports from IND (bilateral test)",
          reporterCode=784, partnerCode=356, flowCode="M", cmdCode=HS)
    probe("India exports to UAE, HS 100821+100829",
          reporterCode=356, partnerCode=784, flowCode="X", cmdCode=HS)
    probe("India exports to UAE, HS 100820 (HS-2012 millet)",
          reporterCode=356, partnerCode=784, flowCode="X", cmdCode="100820")
    probe("India total exports (partner=0), HS 100821+100829",
          reporterCode=356, partnerCode=0, flowCode="X", cmdCode=HS)
    probe("India total exports (partner=0), HS 100820",
          reporterCode=356, partnerCode=0, flowCode="X", cmdCode="100820")

_VIEW = """CREATE VIEW IF NOT EXISTS annual_summary AS
SELECT reporter_iso3 AS reporter, year,
  SUM(CASE WHEN partner_iso3='WLD' THEN value_usd  ELSE 0 END) AS total_value,
  -- india_value: try bilateral import rows first; fall back to India's mirror export rows
  COALESCE(
    NULLIF(SUM(CASE WHEN partner_iso3='IND' THEN value_usd ELSE 0 END), 0),
    (SELECT SUM(e.value_usd) FROM trade_flows e
     WHERE e.reporter_iso3='IND' AND e.flow_type='export'
     AND e.partner_iso3=tf.reporter_iso3 AND e.year=tf.year)
  ) AS india_value,
  ROUND(100.0 * COALESCE(
    NULLIF(SUM(CASE WHEN partner_iso3='IND' THEN value_usd ELSE 0 END), 0),
    (SELECT SUM(e.value_usd) FROM trade_flows e
     WHERE e.reporter_iso3='IND' AND e.flow_type='export'
     AND e.partner_iso3=tf.reporter_iso3 AND e.year=tf.year)
  ) / NULLIF(SUM(CASE WHEN partner_iso3='WLD' THEN value_usd ELSE 0 END), 0), 2) AS india_share_pct,
  SUM(CASE WHEN partner_iso3='WLD' THEN value_usd ELSE 0 END)
    - CASE WHEN reporter_iso3='UAE'
           THEN COALESCE((SELECT SUM(r.value_usd) FROM trade_flows r
                          WHERE r.reporter_iso3='UAE' AND r.flow_type='re_export'
                          AND r.year=tf.year),0) ELSE 0 END      AS uae_adjusted_value,
  CASE WHEN SUM(CASE WHEN partner_iso3='WLD' THEN net_weight_kg ELSE 0 END)>0
       THEN SUM(CASE WHEN partner_iso3='WLD' THEN value_usd ELSE 0 END)
           /SUM(CASE WHEN partner_iso3='WLD' THEN net_weight_kg ELSE 0 END)
       ELSE NULL END                                              AS unit_price_avg,
  NULL AS yoy_growth,        -- compute via LAG or Python at query time
  NULL AS unit_price_3yr_avg -- compute via rolling window at query time
FROM trade_flows tf WHERE flow_type='import' GROUP BY reporter_iso3, year;"""

def build_schema(conn):
    conn.executescript("""
    DROP VIEW IF EXISTS annual_summary;
    CREATE TABLE IF NOT EXISTS country_ref (
        iso3 TEXT PRIMARY KEY, name TEXT, gcc_member INTEGER);
    CREATE TABLE IF NOT EXISTS trade_flows (
        flow_id INTEGER PRIMARY KEY, reporter_iso3 TEXT, partner_iso3 TEXT,
        hs_code TEXT, flow_type TEXT, year INTEGER,
        value_usd REAL, net_weight_kg REAL, unit_price REAL,
        multi_partner INTEGER DEFAULT 0);""")
    try: conn.execute("ALTER TABLE trade_flows ADD COLUMN multi_partner INTEGER DEFAULT 0")
    except Exception: pass  # column already exists in pre-existing DB
    conn.execute(_VIEW)
    gcc_set = set(GCC.values())
    conn.executemany("INSERT OR IGNORE INTO country_ref VALUES (?,?,?)",
        [(k, NAMES[k], 1 if k in gcc_set else 0) for k in NAMES])
    conn.commit()

def load(conn, rows):
    from collections import defaultdict
    conn.execute("DELETE FROM trade_flows"); conn.commit()
    # Pre-aggregate on natural key (reporter, partner, hs, flow, year) to collapse
    # motCode / customsCode splits that Oman and Kuwait return instead of a single total.
    agg = defaultdict(lambda: [0.0, 0.0, 0])  # [value_usd, net_weight_kg, source_row_count]
    for r in rows:
        key = (M49.get(str(r["reporterCode"]), str(r["reporterCode"])),
               M49.get(str(r["partnerCode"]),  str(r["partnerCode"])),
               str(r.get("cmdCode", "")),
               FLOW.get(r.get("flowCode", ""), "unknown"),
               int(r.get("period", 0)))
        a = agg[key]
        a[0] += r.get("primaryValue") or 0.0
        w = r.get("netWgt"); a[1] += float(w) if w and float(w) > 0 else 0.0
        a[2] += 1
    ins = ("INSERT INTO trade_flows(reporter_iso3,partner_iso3,hs_code,flow_type,"
           "year,value_usd,net_weight_kg,unit_price,multi_partner) VALUES(?,?,?,?,?,?,?,?,?)")
    null_wgt = multi = 0
    for (reporter, partner, hs, flow, year), (v, w, n) in agg.items():
        wt = w if w > 0 else None
        if wt is None: null_wgt += 1
        if n > 1: multi += 1
        conn.execute(ins, (reporter, partner, hs, flow, year, v, wt,
                           round(v/wt, 4) if wt and v else None, 1 if n > 1 else 0))
    conn.commit()
    print(f"Loaded {len(agg)} rows from {len(rows)} API rows "
          f"({multi} aggregated from motCode/customsCode splits, {null_wgt} null netWgt).")

def validate(conn):
    checks = []
    for iso3 in GCC.values():
        n = conn.execute("SELECT COUNT(*) FROM trade_flows "
            "WHERE reporter_iso3=? AND partner_iso3='WLD' AND flow_type='import'",
            (iso3,)).fetchone()[0]
        checks.append((f"row_count_{iso3}", 14 <= n <= 20, f"{n} rows (expect 16)"))
    bad = conn.execute(
        "SELECT COUNT(*) FROM trade_flows WHERE value_usd=0 AND net_weight_kg=0").fetchone()[0]
    checks.append(("no_zero_zero_rows", bad == 0, f"{bad} bad rows"))
    rx_yrs = conn.execute("SELECT COUNT(DISTINCT year) FROM trade_flows "
        "WHERE reporter_iso3='UAE' AND flow_type='re_export'").fetchone()[0]
    checks.append(("uae_rx_4plus_years", rx_yrs >= 4, f"{rx_yrs}/8 years"))
    ind_pts = conn.execute("SELECT COUNT(DISTINCT partner_iso3) FROM trade_flows "
        "WHERE reporter_iso3='IND' AND flow_type='export'").fetchone()[0]
    checks.append(("india_exports_4plus_partners", ind_pts >= 4, f"{ind_pts}/6 partners"))
    flagged = conn.execute("SELECT reporter_iso3, hs_code, year, unit_price FROM trade_flows "
        "WHERE unit_price IS NOT NULL AND (unit_price<0.20 OR unit_price>8.00)").fetchall()
    for row in flagged:
        print(f"  [warn] ${row[3]:.3f}/kg outside $0.20-$8.00: {row[0]} HS{row[1]} {row[2]}")
    checks.append(("unit_price_range", True, f"{len(flagged)} flagged (warn-only)"))
    print("\n── Validation ──────────────────────────────")
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<35} {detail}")

def cagr(v0, v1):
    return round(((v1/v0)**(1/7)-1)*100, 1) if v0 and v1 and v0 > 0 else None

def print_summary(conn):
    print(f"\n── 2023 Beachhead Summary {'─'*54}")
    print(f"{'Mkt':<5} {'Import USD':>14} {'IND%':>6} {'UAE-adj USD':>14} {'$/kg':>6} {'8yr CAGR':>9}")
    print("─" * 57)
    for iso3 in GCC.values():
        r3 = conn.execute("SELECT total_value,india_share_pct,uae_adjusted_value,unit_price_avg"
            " FROM annual_summary WHERE reporter=? AND year=2023", (iso3,)).fetchone()
        r0 = conn.execute("SELECT total_value FROM annual_summary WHERE reporter=? AND year=2016",
            (iso3,)).fetchone()
        if not r3: print(f"{iso3:<5}  [no 2023 data — check coverage]"); continue
        tv, sh, adj, up = r3
        low = " ← LOW PRICE" if iso3=="SAU" and up and up < 0.80 else ""
        c = cagr(r0[0] if r0 else None, tv)
        print(f"{iso3:<5} {tv or 0:>14,.0f} {sh or 0:>5.1f}% {adj or tv or 0:>14,.0f}"
              f" {up or 0:>5.2f}  {(str(c)+'%') if c else 'n/a':>8}{low}")

if __name__ == "__main__":
    if not KEY: sys.exit("COMTRADE_KEY not set")
    CACHE.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    build_schema(conn); rows = pull_all(); load(conn, rows)
    # If all India export pulls returned 0, run the diagnostic before failing silently.
    ind_rows = sum(1 for r in rows if M49.get(str(r.get("reporterCode")), "") == "IND")
    if ind_rows == 0:
        print("\n[!] All India export pulls returned 0 rows — running diagnostic:")
        diagnose_india()
        print("\nSee diagnostic above. Delete the ind_x_*.json cache files and re-run after fix.")
    validate(conn); print_summary(conn); conn.close()
    print(f"\nDatabase written: {DB}")
