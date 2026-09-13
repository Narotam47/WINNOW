#!/usr/bin/env bash
# WINNOW end-to-end verification script.
# Run from the project root: ./scripts/final_check.sh

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PASS=0; FAIL=0
r1=FAIL; r2=FAIL; r3=FAIL; r4=FAIL; r5=FAIL; r6=FAIL; r7=FAIL

sep() { echo; echo "────────────────────────────────────────────────────"; }

# ── 1. Name check ─────────────────────────────────────────────────────────────
sep
echo "CHECK 1 — No MONSOON anywhere"
echo

hits=$(grep -ri "monsoon" --exclude-dir=.git --exclude="final_check.sh" . 2>/dev/null || true)
if [[ -z "$hits" ]]; then
    echo "  PASS — zero occurrences"
    r1=PASS; ((PASS++))
else
    echo "  FAIL — residual occurrences:"
    echo "$hits" | while IFS= read -r line; do echo "    $line"; done
    r1=FAIL; ((FAIL++))
fi

# ── 2. File inventory ─────────────────────────────────────────────────────────
sep
echo "CHECK 2 — File inventory"
echo

inv_pass=true

check_file() {
    local path="$1"
    if [[ -f "$path" ]]; then
        local sz
        sz=$(wc -c < "$path")
        if [[ "$sz" -gt 0 ]]; then
            printf "  PASS  %-55s %s bytes\n" "$path" "$(printf "%'.0f" "$sz")"
        else
            printf "  FAIL  %-55s 0 bytes\n" "$path"
            inv_pass=false
        fi
    else
        printf "  FAIL  %-55s missing\n" "$path"
        inv_pass=false
    fi
}

check_file "data/winnow.db"
check_file "data/raw/apeda_millet_exports.xls"

# comtrade_cache directory
if [[ -d "data/comtrade_cache" ]]; then
    n=$(find data/comtrade_cache -name "*.json" | wc -l | tr -d ' ')
    if [[ "$n" -ge 4 ]]; then
        printf "  PASS  %-55s %s JSON files\n" "data/comtrade_cache/" "$n"
    else
        printf "  FAIL  %-55s only %s JSON files (need ≥4)\n" "data/comtrade_cache/" "$n"
        inv_pass=false
    fi
else
    printf "  FAIL  %-55s directory missing\n" "data/comtrade_cache/"
    inv_pass=false
fi

check_file "scripts/build_database.py"
check_file "scripts/load_apeda.py"
check_file "scripts/build_deck.py"
check_file "scripts/analysis_queries.sql"
check_file "scripts/apeda_probe.py"
check_file "scripts/comtrade_probe.py"

for i in $(seq 1 12); do
    check_file "charts/slide_${i}.png"
done

check_file "outputs/WINNOW_deck.pptx"
check_file "README.md"

if $inv_pass; then r2=PASS; ((PASS++)); else r2=FAIL; ((FAIL++)); fi

# ── 3. Database integrity ─────────────────────────────────────────────────────
sep
echo "CHECK 3 — Database integrity"
echo

db_pass=true

run_query() {
    local label="$1" sql="$2" expect="$3"
    local result
    result=$(python3 -c "
import sqlite3, sys
conn = sqlite3.connect('data/winnow.db')
try:
    rows = conn.execute('''$sql''').fetchall()
    for r in rows: print('|'.join(str(x) for x in r))
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
conn.close()
" 2>&1)
    if [[ "$result" == *"ERROR"* ]]; then
        echo "  FAIL  $label: $result"
        db_pass=false
    elif [[ -n "$expect" ]]; then
        if echo "$result" | grep -q "^${expect}$"; then
            echo "  PASS  $label: $result"
        else
            echo "  FAIL  $label: got '$result' (expected $expect)"
            db_pass=false
        fi
    else
        if [[ -n "$result" ]]; then
            echo "  PASS  $label:"
            echo "$result" | while IFS= read -r r; do echo "        $r"; done
        else
            echo "  FAIL  $label: no rows returned"
            db_pass=false
        fi
    fi
}

run_query "trade_flows COUNT"   "SELECT COUNT(*) FROM trade_flows"   "106"
run_query "apeda_exports COUNT" "SELECT COUNT(*) FROM apeda_exports" "640"
run_query "annual_summary COUNT" "SELECT COUNT(*) FROM annual_summary" "48"
run_query "country_ref COUNT"   "SELECT COUNT(*) FROM country_ref"   "8"
run_query "UAE 2023 in annual_summary" \
    "SELECT reporter, year, ROUND(total_value,0), ROUND(uae_adjusted_value,0) FROM annual_summary WHERE reporter='UAE' AND year=2023" ""
# APEDA query uses sqlite3 CLI to avoid single-quote collision in the Python heredoc
apeda_row=$(sqlite3 data/winnow.db \
    "SELECT country_iso3, fiscal_year, ROUND(value_usd,0), ROUND(qty_mt,2) FROM apeda_exports WHERE country_iso3='UAE' AND fiscal_year='2023-24'" \
    2>&1)
if [[ -n "$apeda_row" && "$apeda_row" != *"Error"* ]]; then
    echo "  PASS  UAE FY2023-24 in apeda_exports:"
    echo "        $apeda_row"
else
    echo "  FAIL  UAE FY2023-24 in apeda_exports: no row returned"
    db_pass=false
fi

if $db_pass; then r3=PASS; ((PASS++)); else r3=FAIL; ((FAIL++)); fi

# ── 4. Script syntax ──────────────────────────────────────────────────────────
sep
echo "CHECK 4 — Script syntax (py_compile)"
echo

syn_pass=true
for script in build_database.py load_apeda.py build_deck.py apeda_probe.py comtrade_probe.py; do
    out=$(python3 -m py_compile "scripts/$script" 2>&1)
    if [[ -z "$out" ]]; then
        printf "  PASS  scripts/%s\n" "$script"
    else
        printf "  FAIL  scripts/%s: %s\n" "$script" "$out"
        syn_pass=false
    fi
done

if $syn_pass; then r4=PASS; ((PASS++)); else r4=FAIL; ((FAIL++)); fi

# ── 5. Chart integrity ────────────────────────────────────────────────────────
sep
echo "CHECK 5 — Chart integrity (PIL verify)"
echo

chart_out=$(python3 - << 'PYEOF'
from PIL import Image
from pathlib import Path
all_ok = True
for i in range(1, 13):
    p = Path(f"charts/slide_{i}.png")
    try:
        img = Image.open(p)
        img.verify()
        sz = p.stat().st_size
        print(f"  PASS  charts/slide_{i}.png  {sz:,} bytes")
    except Exception as e:
        print(f"  FAIL  charts/slide_{i}.png  {e}")
        all_ok = False
print("__ALL_OK__" if all_ok else "__HAS_FAIL__")
PYEOF
)
echo "$chart_out" | grep -v "^__"
if echo "$chart_out" | grep -q "__ALL_OK__"; then r5=PASS; ((PASS++)); else r5=FAIL; ((FAIL++)); fi

# ── 6. Deck integrity ─────────────────────────────────────────────────────────
sep
echo "CHECK 6 — Deck integrity (zip + slide count)"
echo

deck_out=$(python3 - << 'PYEOF'
import zipfile, sys
from pathlib import Path
p = Path("outputs/WINNOW_deck.pptx")
try:
    with zipfile.ZipFile(p) as z:
        slides = [f for f in z.namelist()
                  if f.startswith("ppt/slides/slide") and f.endswith(".xml")]
        n = len(slides)
        sz = p.stat().st_size
        print(f"  Slide count : {n} (expect 13)")
        print(f"  File size   : {sz:,} bytes")
        print("  PASS" if n == 13 else f"  FAIL — got {n} slides, expected 13")
        print("__OK__" if n == 13 else "__FAIL__")
except Exception as e:
    print(f"  FAIL  {e}")
    print("__FAIL__")
PYEOF
)
echo "$deck_out" | grep -v "^__"
if echo "$deck_out" | grep -q "__OK__"; then r6=PASS; ((PASS++)); else r6=FAIL; ((FAIL++)); fi

# ── 7. README check ───────────────────────────────────────────────────────────
sep
echo "CHECK 7 — README check"
echo

readme_out=$(python3 - << 'PYEOF'
from pathlib import Path
text = Path("README.md").read_text()
lines = text.strip().split("\n")
words = len(text.split())
has_monsoon = "monsoon" in text.lower()
print(f"  First line  : {lines[0][:80]}")
print(f"  Word count  : {words} (expect 400–700)")
print(f"  MONSOON     : {has_monsoon} (expect False)")
ok = not has_monsoon and 400 <= words <= 700 and bool(lines[0].strip())
print("  PASS" if ok else "  FAIL")
print("__OK__" if ok else "__FAIL__")
PYEOF
)
echo "$readme_out" | grep -v "^__"
if echo "$readme_out" | grep -q "__OK__"; then r7=PASS; ((PASS++)); else r7=FAIL; ((FAIL++)); fi

# ── Final summary ─────────────────────────────────────────────────────────────
sep
echo
echo "  === WINNOW FINAL CHECK ==="
echo "  1. Name check:        $r1"
echo "  2. File inventory:    $r2"
echo "  3. Database:          $r3"
echo "  4. Script syntax:     $r4"
echo "  5. Chart integrity:   $r5"
echo "  6. Deck integrity:    $r6"
echo "  7. README:            $r7"
echo
if [[ $FAIL -eq 0 ]]; then
    echo "  Overall:              PASS  ($PASS/7)"
else
    echo "  Overall:              FAIL  ($PASS passed, $FAIL failed)"
fi
echo
