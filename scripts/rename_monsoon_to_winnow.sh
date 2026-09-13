#!/usr/bin/env bash
# Rename WINNOW → WINNOW throughout the project.
# Usage: bash scripts/rename_winnow_to_winnow.sh [--yes]
#   --yes   skip the confirmation prompt and apply changes immediately

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKIP_CONFIRM=false
[[ "${1:-}" == "--yes" ]] && SKIP_CONFIRM=true

# ── File-selection helpers ────────────────────────────────────────────────────

find_text_files() {
    find "$ROOT" -type f \( -name "*.py" -o -name "*.sql" -o -name "*.md" \
                            -o -name "*.txt" -o -name "*.sh" \) \
        ! -path "*/data/*" \
        ! -path "*/charts/*" \
        ! -path "*/outputs/*" \
        ! -path "*/.git/*"
}

# Files that contain either pattern
matching_files() {
    find_text_files | xargs grep -l -E "WINNOW|winnow" 2>/dev/null || true
}

# ── Dry run ───────────────────────────────────────────────────────────────────

echo "════════════════════════════════════════════════════════"
echo "  DRY RUN — no files will be changed"
echo "════════════════════════════════════════════════════════"
echo

dry_files=()
while IFS= read -r f; do
    rel="${f#"$ROOT"/}"
    total=$(wc -l < "$f")
    winnow_upper=$(grep -c "WINNOW" "$f" 2>/dev/null || true)
    winnow_lower=$(grep -c "winnow" "$f" 2>/dev/null || true)
    echo "  $rel"
    echo "    lines: $total  |  WINNOW occurrences: $winnow_upper  |  winnow occurrences: $winnow_lower"
    dry_files+=("$f")
done < <(matching_files)

echo
if [[ ${#dry_files[@]} -eq 0 ]]; then
    echo "  No text files contain WINNOW or winnow — nothing to replace."
else
    echo "  ${#dry_files[@]} file(s) would be modified (text replacement)"
fi

echo
echo "  Binary renames (unconditional):"
[[ -f "$ROOT/outputs/WINNOW_deck.pptx" ]] \
    && echo "    outputs/WINNOW_deck.pptx  →  outputs/WINNOW_deck.pptx" \
    || echo "    outputs/WINNOW_deck.pptx  (not found — skipping)"
[[ -f "$ROOT/data/winnow.db" ]] \
    && echo "    data/winnow.db            →  data/winnow.db" \
    || echo "    data/winnow.db            (not found — skipping)"
echo

# ── Confirmation ──────────────────────────────────────────────────────────────

if [[ "$SKIP_CONFIRM" == false ]]; then
    read -r -p "Apply all changes? [y/N] " reply
    echo
    if [[ ! "$reply" =~ ^[Yy]$ ]]; then
        echo "Aborted — no changes made."
        exit 0
    fi
fi

# ── Text replacement ──────────────────────────────────────────────────────────

echo "════════════════════════════════════════════════════════"
echo "  APPLYING CHANGES"
echo "════════════════════════════════════════════════════════"
echo

changed_files=()
while IFS= read -r f; do
    rel="${f#"$ROOT"/}"
    before=$(wc -l < "$f")
    # Two-pass sed: uppercase first, then lowercase
    if [[ "$(uname)" == "Darwin" ]]; then
        sed -i '' 's/WINNOW/WINNOW/g; s/winnow/winnow/g' "$f"
    else
        sed -i 's/WINNOW/WINNOW/g; s/winnow/winnow/g' "$f"
    fi
    after=$(wc -l < "$f")
    echo "  modified: $rel  (lines before: $before  after: $after)"
    changed_files+=("$rel")
done < <(matching_files)

if [[ ${#changed_files[@]} -eq 0 ]]; then
    echo "  No text files matched — nothing replaced."
fi

# ── Binary renames ────────────────────────────────────────────────────────────

echo
echo "  Binary renames:"

if [[ -f "$ROOT/outputs/WINNOW_deck.pptx" ]]; then
    mv "$ROOT/outputs/WINNOW_deck.pptx" "$ROOT/outputs/WINNOW_deck.pptx"
    echo "  renamed: outputs/WINNOW_deck.pptx  →  outputs/WINNOW_deck.pptx"
else
    echo "  skip:    outputs/WINNOW_deck.pptx not found"
fi

if [[ -f "$ROOT/data/winnow.db" ]]; then
    mv "$ROOT/data/winnow.db" "$ROOT/data/winnow.db"
    echo "  renamed: data/winnow.db  →  data/winnow.db"
else
    echo "  skip:    data/winnow.db not found"
fi

# ── Verification ──────────────────────────────────────────────────────────────

echo
echo "════════════════════════════════════════════════════════"
echo "  VERIFICATION — remaining occurrences"
echo "════════════════════════════════════════════════════════"
echo

remaining=$(find_text_files | xargs grep -rn -E "WINNOW|winnow" 2>/dev/null || true)

if [[ -z "$remaining" ]]; then
    echo "  Clean — no remaining WINNOW or winnow in tracked text files."
else
    echo "  WARNING: residual occurrences found:"
    echo "$remaining" | sed "s|$ROOT/||" | while IFS= read -r line; do
        echo "    $line"
    done
fi

# ── Summary ───────────────────────────────────────────────────────────────────

echo
echo "════════════════════════════════════════════════════════"
echo "  SUMMARY — files changed"
echo "════════════════════════════════════════════════════════"
echo
for f in "${changed_files[@]}"; do
    echo "  $f"
done
[[ -f "$ROOT/outputs/WINNOW_deck.pptx" ]] && echo "  outputs/WINNOW_deck.pptx  (renamed)"
[[ -f "$ROOT/data/winnow.db" ]]           && echo "  data/winnow.db            (renamed)"
echo
