#!/usr/bin/env python3
"""Comtrade free-tier feasibility probe. Throwaway. Stdlib only.
Usage: COMTRADE_KEY=... python3 comtrade_probe.py
Raw JSON lands in WINNOW/data/comtrade_cache/ ; delete it to re-fetch."""
import os, sys, json, time, urllib.request, urllib.parse, urllib.error
from collections import defaultdict

KEY = os.environ.get("COMTRADE_KEY")
if not KEY:
    sys.exit("COMTRADE_KEY not set")

BASE  = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
CACHE = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "data", "comtrade_cache")
HS    = "100821,100829"
YEAR  = 2023                      # edit me; 2024 may be incomplete for late reporters
# M49 numeric, no leading zeros -- Bahrain is 48, not 048
GCC   = {"784": "UAE", "682": "Saudi", "634": "Qatar",
         "512": "Oman", "414": "Kuwait", "48": "Bahrain"}
# row counts that are probably a cap rather than a real answer
SUSPECT = {500, 1000, 2500, 5000, 10000, 50000, 100000, 250000}


def fetch(tag, **params):
    path = os.path.join(CACHE, tag + ".json")
    if os.path.exists(path):
        obj = json.load(open(path))
        print(f"[cache ] {tag}: {len(obj.get('data') or [])} rows")
        return obj
    params.setdefault("cmdCode", HS)
    params.setdefault("flowCode", "M")
    url = BASE + "?" + urllib.parse.urlencode(params)
    delay, body = 2, None
    for _ in range(5):
        req = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": KEY})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                print(f"[{e.code:>5}] {tag}: backing off {delay}s")
                time.sleep(delay); delay *= 2; continue
            sys.exit(f"HTTP {e.code} on {tag}\n{e.read()[:400].decode('utf8','replace')}")
    if body is None:
        sys.exit(f"gave up on {tag} after 5 attempts")
    os.makedirs(CACHE, exist_ok=True)
    with open(path, "wb") as f:        # raw bytes to disk BEFORE parsing
        f.write(body)
    obj = json.loads(body)
    n = len(obj.get("data") or [])
    warn = "   <-- ROUND NUMBER, suspect a cap" if n in SUSPECT else ""
    print(f"[fetch ] {tag}: {n} rows{warn}")
    return obj


def val(r):  return r.get("primaryValue") or 0.0
def wgt(r):  return r.get("netWgt") or 0.0


def q1():
    print(f"\n=== Q1  GCC imports of {HS} from World, {YEAR} ===")
    rows = fetch(f"q1_{YEAR}", reporterCode=",".join(GCC), period=YEAR,
                 partnerCode=0)["data"] or []
    agg = defaultdict(lambda: [0.0, 0.0, 0])
    for r in rows:
        a = agg[str(r["reporterCode"])]
        a[0] += val(r); a[1] += wgt(r); a[2] += 1
    print(f"{'country':8} {'USD':>15} {'net kg':>15}  rows  note")
    for code, name in GCC.items():
        v, w, n = agg.get(code, [0.0, 0.0, 0])
        note = "NO DATA" if n == 0 else ("netWgt absent" if w == 0 else "")
        print(f"{name:8} {v:15,.0f} {w:15,.0f}  {n:>4}  {note}")


def q2():
    print(f"\n=== Q2  Mirror: all reporters' imports FROM UAE, {YEAR} ===")
    # reporterCode omitted entirely == all reporters
    rows = fetch(f"q2_mirror_{YEAR}", period=YEAR, partnerCode=784)["data"] or []
    by = defaultdict(float)
    for r in rows:
        by[r.get("reporterDesc") or str(r["reporterCode"])] += val(r)
    tot = sum(by.values())
    print(f"reporters returning data: {len(by)}   total USD: {tot:,.0f}")
    for name, v in sorted(by.items(), key=lambda x: -x[1])[:10]:
        pct = f"{v / tot * 100:5.1f}%" if tot else "    -"
        print(f"  {name:32} {v:14,.0f}  {pct}")
    # Cleaner route if UAE reports it: its own re-export flow, no mirror needed.
    rx = fetch(f"q2_uae_rx_{YEAR}", reporterCode=784, period=YEAR,
               partnerCode=0, flowCode="RX")["data"] or []
    print(f"\nUAE self-reported re-exports (flowCode=RX): {len(rx)} rows, "
          f"USD {sum(val(r) for r in rx):,.0f}")
    print("  ^ if this is non-empty it beats the mirror estimate outright")


def q3():
    yrs = list(range(YEAR - 7, YEAR + 1))
    print(f"\n=== Q3  Coverage {yrs[0]}-{yrs[-1]} (Y = value > 0) ===")
    rows = fetch("q3_coverage", reporterCode=",".join(GCC),
                 period=",".join(map(str, yrs)), partnerCode=0)["data"] or []
    seen = defaultdict(set)
    for r in rows:
        if val(r) > 0:
            seen[str(r["reporterCode"])].add(int(r.get("refYear") or r["period"]))
    print(f"{'country':8} " + " ".join(f"{y % 100:>3}" for y in yrs) + "   gaps")
    for code, name in GCC.items():
        marks = " ".join(f"{'Y' if y in seen[code] else '.':>3}" for y in yrs)
        gaps = [y for y in yrs if y not in seen[code]]
        print(f"{name:8} {marks}   {len(gaps)}" + (f"  {gaps}" if gaps else ""))


if __name__ == "__main__":
    q1(); q2(); q3()
    print(f"\nRaw JSON cached in {CACHE}/ -- inspect before trusting any of the above.")
