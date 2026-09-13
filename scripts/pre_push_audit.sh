#!/usr/bin/env bash
# WINNOW pre-push audit.
# Run from the project root: ./scripts/pre_push_audit.sh

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PASS=0; FAIL=0
r1=PASS; r2=PASS; r3=PASS; r4=PASS; r5=PASS
actions=()

sep() { echo; echo "────────────────────────────────────────────────────"; }

# ── Check 1 — Large files (>5MB) ──────────────────────────────────────────────
sep
echo "CHECK 1 — Large files (>5MB)"
echo

large=$(find . -not -path './.git/*' -size +5M -type f | sort)
if [[ -z "$large" ]]; then
    echo "  PASS — no files exceed 5MB"
    ((PASS++))
else
    echo "  FAIL — files over 5MB:"
    echo "$large" | while IFS= read -r f; do
        sz=$(ls -lh "$f" | awk '{print $5}')
        echo "    $sz  $f"
    done
    r1=FAIL; ((FAIL++))
    actions+=("Remove or gitignore large files listed above")
fi

# ── Check 2 — Sensitive files ─────────────────────────────────────────────────
sep
echo "CHECK 2 — Sensitive files and hardcoded keys"
echo

sens_pass=true

# Named sensitive files
sens_files=$(find . -not -path './.git/*' -type f \( \
    -name "*.env" -o -name ".env*" -o -name "*secret*" \
    -o -name "*credential*" -o -name "*apikey*" \
    -o -name "*.pem" -o -name "*.key" \) | sort)

if [[ -n "$sens_files" ]]; then
    echo "  FAIL — sensitive filenames found:"
    echo "$sens_files" | while IFS= read -r f; do echo "    $f"; done
    sens_pass=false
else
    echo "  PASS — no sensitive filenames"
fi

# Hardcoded key assignments — must only appear as os.environ / os.getenv
# Exclude: comment lines (#), docstrings (inside """/'''), and this audit script itself
echo
hardcoded=$(grep -rn "COMTRADE_KEY\s*=" --include="*.py" --include="*.sh" \
    --exclude-dir=.git --exclude="pre_push_audit.sh" . 2>/dev/null \
    | grep -v "os\.environ\|os\.getenv\|getenv\|environ" \
    | grep -v "^\s*#\|Usage:" || true)

if [[ -z "$hardcoded" ]]; then
    echo "  PASS — COMTRADE_KEY only via os.environ/os.getenv (usage strings excluded)"
else
    echo "  FAIL — hardcoded key assignment(s):"
    echo "$hardcoded" | while IFS= read -r line; do echo "    $line"; done
    sens_pass=false
fi

# Check for actual key literal values (8+ char alphanumeric after an = in .py files)
echo
token_hits=$(grep -rn -E "COMTRADE_KEY\s*=\s*['\"][A-Za-z0-9]{8}" \
    --include="*.py" --exclude-dir=.git . 2>/dev/null || true)
if [[ -z "$token_hits" ]]; then
    echo "  PASS — no literal API key values in Python files"
else
    echo "  FAIL — literal API key value(s) found:"
    echo "$token_hits" | while IFS= read -r line; do echo "    $line"; done
    sens_pass=false
fi

if $sens_pass; then ((PASS++)); else r2=FAIL; ((FAIL++)); actions+=("Review sensitive files/keys listed above"); fi

# ── Check 3 — Python cache and temp files ────────────────────────────────────
sep
echo "CHECK 3 — Python cache and temp files"
echo

cache_pass=true

cache_files=$(find . -not -path './.git/*' -type f \( \
    -name "*.pyc" -o -name "*.pyo" -o -name ".DS_Store" \
    -o -name "Thumbs.db" -o -name "*.log" -o -name "*.tmp" \
    -o -name ".~lock.*" \) | sort)

cache_dirs=$(find . -not -path './.git/*' -type d -name "__pycache__" | sort)

if [[ -z "$cache_files" && -z "$cache_dirs" ]]; then
    echo "  PASS — no cache or temp files"
    ((PASS++))
else
    if [[ -n "$cache_files" ]]; then
        echo "  FAIL — temp/cache files present:"
        echo "$cache_files" | while IFS= read -r f; do echo "    $f"; done
    fi
    if [[ -n "$cache_dirs" ]]; then
        echo "  FAIL — __pycache__ directories present:"
        echo "$cache_dirs" | while IFS= read -r d; do echo "    $d/"; done
    fi
    r3=FAIL; ((FAIL++))
    actions+=("Delete cache/temp files: rm -rf scripts/__pycache__ && find . -name '*.pyc' -delete && find . -name '.~lock.*' -delete")
fi

# ── Check 4 — Unexpected file types ──────────────────────────────────────────
sep
echo "CHECK 4 — Unexpected file types"
echo

unexpected=$(find . -not -path './.git/*' -type f \
    | grep -vE '\.(py|sql|md|sh|txt|png|pptx|xls|json|db|gitignore)$' \
    | grep -v '/.git/' \
    | grep -v '/comtrade_cache/' \
    | sort)

if [[ -z "$unexpected" ]]; then
    echo "  PASS — no unexpected file types"
    ((PASS++))
else
    echo "  FAIL — unexpected files:"
    echo "$unexpected" | while IFS= read -r f; do
        ext="${f##*.}"
        sz=$(wc -c < "$f" 2>/dev/null || echo "?")
        printf "    %-55s  (ext: .%s, %s bytes)\n" "$f" "$ext" "$sz"
    done
    r4=FAIL; ((FAIL++))
    actions+=("Review and remove unexpected files listed above")
fi

# ── Check 5 — .gitignore coverage ────────────────────────────────────────────
sep
echo "CHECK 5 — .gitignore check"
echo

gi_pass=true
if [[ ! -f ".gitignore" ]]; then
    echo "  FAIL — .gitignore not found"
    gi_pass=false
else
    echo "  Current .gitignore:"
    while IFS= read -r line; do echo "    $line"; done < .gitignore
    echo

    required_patterns=(
        "__pycache__/"
        "*.pyc"
        ".DS_Store"
        ".env"
        "data/comtrade_cache/"
        "data/winnow.db"
        "data/raw/"
        "outputs/.~lock.*"
    )

    missing=()
    for pat in "${required_patterns[@]}"; do
        if grep -qF "$pat" .gitignore 2>/dev/null; then
            printf "  PASS  %-30s  present\n" "$pat"
        else
            printf "  FAIL  %-30s  MISSING\n" "$pat"
            missing+=("$pat")
            gi_pass=false
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo
        echo "  Missing patterns: ${missing[*]}"
        actions+=("Add missing .gitignore patterns: ${missing[*]}")
    fi
fi

if $gi_pass; then ((PASS++)); else r5=FAIL; ((FAIL++)); fi

# ── Check 6 — Git-tracked files ───────────────────────────────────────────────
sep
echo "CHECK 6 — Git-tracked files (git ls-files)"
echo

if git -C "$ROOT" rev-parse --git-dir > /dev/null 2>&1; then
    tracked=$(git ls-files | sort)
    if [[ -z "$tracked" ]]; then
        echo "  (no files staged — repo exists but nothing tracked yet)"
    else
        echo "$tracked" | while IFS= read -r f; do
            sz=$(wc -c < "$f" 2>/dev/null | tr -d ' ')
            printf "  %-55s %s bytes\n" "$f" "$sz"
        done
    fi
else
    echo "  NOTE: not a git repository yet — run 'git init' before push"
    echo "  Files that WOULD be tracked (applying .gitignore rules):"
    echo
    # Simulate what git would track using .gitignore patterns
    python3 - << 'PYEOF'
import os, re
from pathlib import Path

root = Path(".")
gitignore = Path(".gitignore")

patterns = []
if gitignore.exists():
    for line in gitignore.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line)

def is_ignored(path_str):
    parts = Path(path_str).parts
    for pat in patterns:
        # directory pattern
        if pat.endswith("/"):
            dirname = pat.rstrip("/")
            if any(p == dirname for p in parts):
                return True
        # glob pattern
        elif "*" in pat:
            name = Path(path_str).name
            import fnmatch
            if fnmatch.fnmatch(name, pat):
                return True
        # exact match anywhere in path
        else:
            if pat in parts or Path(path_str).name == pat:
                return True
    return False

files = []
for f in sorted(root.rglob("*")):
    if not f.is_file():
        continue
    rel = str(f.relative_to(root))
    if rel.startswith(".git/") or "/.git/" in rel:
        continue
    if is_ignored(rel):
        continue
    sz = f.stat().st_size
    files.append((rel, sz))

for rel, sz in files:
    print(f"  {rel:<55}  {sz:,} bytes")
print(f"\n  Total: {len(files)} file(s) would be committed")
PYEOF
fi

# ── Final summary ─────────────────────────────────────────────────────────────
sep
echo
echo "  === WINNOW PRE-PUSH AUDIT ==="
echo "  1. Large files (>5MB):    $r1"
echo "  2. Sensitive files/keys:  $r2"
echo "  3. Cache/temp files:      $r3"
echo "  4. Unexpected file types: $r4"
echo "  5. .gitignore coverage:   $r5"
echo "  6. Git-tracked files:     (see above)"
echo

if [[ ${#actions[@]} -eq 0 ]]; then
    echo "  Action items before push: none — ready to push"
else
    echo "  Action items before push:"
    for a in "${actions[@]}"; do
        echo "    • $a"
    done
fi
echo
