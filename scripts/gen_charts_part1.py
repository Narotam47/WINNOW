#!/usr/bin/env python3
"""WINNOW slides 1-7 chart code."""
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

Path("charts").mkdir(exist_ok=True)

ACCENT = "#2E86AB"
RED    = "#D64045"
LGRAY  = "#E8E8E8"
MID    = "#888888"
DARK   = "#222222"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlecolor": DARK,
    "xtick.color": MID,
    "ytick.color": MID,
})

def new_fig():
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    return fig, ax

def clean(ax, hgrid=True, vgrid=False):
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(LGRAY)
    ax.set_axisbelow(True)
    if hgrid:
        ax.yaxis.grid(True, color=LGRAY, linewidth=0.7, zorder=0)
    if vgrid:
        ax.xaxis.grid(True, color=LGRAY, linewidth=0.7, zorder=0)

def save(fig, n):
    path = f"charts/slide_{n}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {path}")


# ── SLIDE 1: Margin waterfall ─────────────────────────────────────────────────
def slide_1():
    costs = [
        ("Selling price",    550.00),
        ("Procurement",     -269.76),
        ("Packaging",         -9.52),
        ("Inland freight",   -17.86),
        ("Port charges",     -12.00),
        ("Fixed export",     -19.55),
        ("Ocean freight",    -45.45),
        ("Insurance",         -1.87),
        ("Duty (UAE 5%)",    -18.80),
        ("Dest. handling",   -15.00),
        ("Last-mile",        -10.00),
        ("Gross margin",     130.19),
    ]
    labels = [c[0] for c in costs]

    running = 550.0
    bottoms, heights, clrs = [0], [550.0], [ACCENT]
    for _, v in costs[1:-1]:
        new = running + v
        bottoms.append(new)
        heights.append(abs(v))
        clrs.append(RED)
        running = new
    bottoms.append(0)
    heights.append(running)
    clrs.append(ACCENT)

    fig, ax = new_fig()
    clean(ax)
    xs = range(len(labels))
    ax.bar(xs, heights, bottom=bottoms, color=clrs, zorder=3,
           width=0.65, edgecolor="white", linewidth=0.4)

    for i, (b, h) in enumerate(zip(bottoms, heights)):
        if h > 12:
            ax.text(i, b + h / 2,
                    f"${h:.0f}" if h > 30 else f"${h:.1f}",
                    ha="center", va="center", fontsize=7,
                    color="white", fontweight="bold")
        if i in (0, len(labels) - 1):
            suffix = "\n(23.7%)" if i == len(labels) - 1 else ""
            ax.text(i, b + h + 7, f"${h:.0f}{suffix}",
                    ha="center", va="bottom", fontsize=9,
                    color=DARK, fontweight="bold")

    tick_labels = []
    for l in labels:
        words = l.split()
        tick_labels.append("\n".join(words) if len(words) > 1 else l)
    ax.set_xticks(xs)
    ax.set_xticklabels(tick_labels, fontsize=8.5)
    ax.set_ylabel("USD per MT", color=DARK)
    ax.set_ylim(0, 625)
    ax.set_title("Jodhpur → Jebel Ali: landed-cost waterfall at $550/MT",
                 fontsize=13, pad=12)
    save(fig, 1)


# ── SLIDE 2: GCC market structure ─────────────────────────────────────────────
def slide_2():
    markets = ["UAE", "Oman", "Saudi Arabia", "Qatar", "Bahrain", "Kuwait"]
    values  = [6.98, 3.06, 1.91, 0.88, 0.53, 0.32]
    total   = sum(values)
    clrs    = [ACCENT if m == "UAE" else "#9DC6D8" for m in markets]

    fig, ax = new_fig()
    clean(ax, hgrid=False, vgrid=True)
    ys   = range(len(markets))
    bars = ax.barh(ys, values, color=clrs, zorder=3, height=0.58)
    for bar, v in zip(bars, values):
        pct = v / total * 100
        ax.text(v + 0.08, bar.get_y() + bar.get_height() / 2,
                f"${v:.2f}M  ({pct:.0f}%)",
                va="center", fontsize=9.5, color=DARK)
    ax.set_yticks(ys)
    ax.set_yticklabels(markets, fontsize=11)
    ax.set_xlabel("5-year average import value (USD millions, 2019–2023)", color=DARK)
    ax.set_xlim(0, 10.5)
    ax.invert_yaxis()
    ax.set_title("GCC millet import market size — five-year average",
                 fontsize=13, pad=12)
    save(fig, 2)


# ── SLIDE 3: UAE 8-year demand trend ──────────────────────────────────────────
def slide_3():
    years    = list(range(2016, 2024))
    total    = [5.44, 4.91, 4.91, 6.44, 5.26, 6.50, 8.27, 8.41]
    adjusted = [5.25, 4.69, 4.53, 5.57, 4.33, 5.61, 7.66, 8.01]

    fig, ax = new_fig()
    clean(ax)
    ax.plot(years, total, color=ACCENT, lw=2.2, marker="o", ms=6,
            zorder=3, label="Total imports")
    ax.plot(years, adjusted, color=ACCENT, lw=2.0, ls="--", marker="s",
            ms=5, alpha=0.6, zorder=3, label="Net of re-exports")

    for x, y in zip(years, total):
        va = "bottom"
        ax.text(x, y + 0.15, f"${y:.2f}M", ha="center",
                fontsize=8, color=DARK, va=va)

    ax.axvspan(2019.55, 2020.45, color=LGRAY, alpha=0.7, zorder=0)
    ax.text(2020, 3.75, "COVID\ndip", ha="center", fontsize=8, color=MID)

    ax.set_xticks(years)
    ax.set_ylabel("Millet import value (USD millions)", color=DARK)
    ax.set_ylim(3.2, 9.9)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_title("UAE millet imports 2016–2023: six up-years in eight",
                 fontsize=13, pad=12)
    save(fig, 3)


# ── SLIDE 4: India → UAE exports (APEDA 5-year) ───────────────────────────────
def slide_4():
    years  = ["FY19-20", "FY20-21", "FY21-22", "FY22-23", "FY23-24"]
    qty    = [16762, 27444, 30950, 33176, 29214]
    price  = [0.4554, 0.4128, 0.3360, 0.3874, 0.4016]

    fig, ax = new_fig()
    clean(ax)
    ax2 = ax.twinx()

    xs   = np.arange(len(years))
    bars = ax.bar(xs, qty, color=ACCENT, alpha=0.85, zorder=3, width=0.55)
    for bar, v in zip(bars, qty):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 500,
                f"{v:,.0f}", ha="center", fontsize=9, color=DARK)

    ax2.plot(xs, price, color=RED, lw=2, marker="D", ms=6, zorder=4)
    for x, p in zip(xs, price):
        ax2.text(x, p + 0.010, f"${p:.3f}", ha="center",
                 fontsize=8, color=RED)

    ax.set_xticks(xs)
    ax.set_xticklabels(years, fontsize=10)
    ax.set_ylabel("Volume (MT)", color=DARK)
    ax.set_ylim(0, 41000)
    ax2.set_ylabel("Unit price (USD/kg)", color=RED)
    ax2.tick_params(axis="y", colors=RED, labelsize=9)
    ax2.spines[["top", "right", "left"]].set_visible(False)
    ax2.set_ylim(0.28, 0.57)

    fig.text(0.14, 0.87, "■ Volume (MT)", color=ACCENT, fontsize=9)
    fig.text(0.38, 0.87, "◆ Unit price ($/kg)", color=RED, fontsize=9)

    ax.set_title(
        "India's bajra exports to UAE — volume and unit price (APEDA)",
        fontsize=13, pad=12)
    save(fig, 4)


# ── SLIDE 5: Unit price by GCC market ─────────────────────────────────────────
def slide_5():
    markets = ["Kuwait", "UAE", "Saudi Arabia", "Qatar", "Oman"]
    prices  = [0.4406, 0.4016, 0.3904, 0.3664, 0.3408]
    vols    = [4666, 29214, 16520, 3531, 3529]
    clrs    = ["#1C6B8A", ACCENT, "#5BAAC5", "#9DC6D8", "#C5DEE8"]

    fig, ax = new_fig()
    clean(ax, hgrid=False, vgrid=True)
    ys   = range(len(markets))
    bars = ax.barh(ys, prices, color=clrs, zorder=3, height=0.55)
    for bar, p, v in zip(bars, prices, vols):
        ax.text(p + 0.003, bar.get_y() + bar.get_height() / 2,
                f"${p:.4f}/kg   ({v:,.0f} MT)",
                va="center", fontsize=9.5, color=DARK)

    ax.set_yticks(ys)
    ax.set_yticklabels(markets, fontsize=11)
    ax.set_xlabel("Unit price (USD/kg), FY2023-24", color=DARK)
    ax.set_xlim(0, 0.60)
    ax.invert_yaxis()
    ax.axvline(0.4406, color=ACCENT, lw=1.2, ls=":", zorder=2,
               label="Kuwait ceiling $0.441")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_title("Indian millet unit price by GCC buyer — FY2023-24",
                 fontsize=13, pad=12)
    save(fig, 5)


# ── SLIDE 6: UAE vs Saudi Arabia divergence ───────────────────────────────────
def slide_6():
    years = list(range(2016, 2024))
    uae   = [5.44, 4.91, 4.91, 6.44, 5.26, 6.50, 8.27, 8.41]
    sau   = [7.78, 4.61, 2.55, 2.65, 1.58, 1.40, 2.64, 1.28]

    fig, ax = new_fig()
    clean(ax)
    ax.plot(years, uae, color=ACCENT, lw=2.5, marker="o", ms=7,
            zorder=3, label="UAE")
    ax.plot(years, sau, color=RED, lw=2.5, ls="--", marker="s",
            ms=6, zorder=3, label="Saudi Arabia")

    for x, y in zip(years, uae):
        ax.text(x, y + 0.18, f"${y:.2f}M", ha="center",
                fontsize=8, color=ACCENT)
    for x, y in zip(years, sau):
        ax.text(x, y - 0.32, f"${y:.2f}M", ha="center",
                fontsize=8, color=RED)

    ax.fill_between(years, uae, sau,
                    where=[u > s for u, s in zip(uae, sau)],
                    alpha=0.07, color=ACCENT)
    ax.annotate("Crossover\n2017", xy=(2017, 4.91),
                xytext=(2016.2, 6.6), fontsize=8.5, color=DARK,
                arrowprops=dict(arrowstyle="->", color=DARK, lw=0.9))

    ax.set_xticks(years)
    ax.set_ylabel("Millet import value (USD millions)", color=DARK)
    ax.set_ylim(0, 10.8)
    ax.legend(frameon=False, fontsize=10, loc="upper right")
    ax.set_title("UAE vs Saudi Arabia millet imports 2016–2023",
                 fontsize=13, pad=12)
    save(fig, 6)


# ── SLIDE 7: India GCC exports stacked by country ─────────────────────────────
def slide_7():
    fy = ["FY19-20", "FY20-21", "FY21-22", "FY22-23", "FY23-24"]
    data = {
        "UAE":          [16762, 27444, 30950, 33176, 29214],
        "Saudi Arabia": [13282, 19817, 18824, 24188, 16520],
        "Qatar":        [1172,  3542,  4111,  4181,  3531],
        "Oman":         [1164,  3149,  6171,  4959,  3529],
        "Kuwait":       [2362,  2450,  3592,  3974,  4666],
    }
    palette = ["#1A5C78", ACCENT, "#5BAAC5", "#9DC6D8", "#C5DEE8"]

    fig, ax = new_fig()
    clean(ax)
    xs     = np.arange(len(fy))
    bottom = np.zeros(len(fy))
    for (country, vals), clr in zip(data.items(), palette):
        v = np.array(vals, dtype=float)
        ax.bar(xs, v, bottom=bottom, color=clr, label=country,
               zorder=3, width=0.60)
        for i, (b, vi) in enumerate(zip(bottom, v)):
            if vi > 2000:
                ax.text(i, b + vi / 2, f"{vi:,.0f}",
                        ha="center", va="center", fontsize=7.5,
                        color="white", fontweight="bold")
        bottom += v

    totals = [sum(data[c][i] for c in data) for i in range(len(fy))]
    for i, t in enumerate(totals):
        ax.text(i, t + 900, f"{t:,.0f} MT",
                ha="center", fontsize=8.5, color=DARK, fontweight="bold")

    ax.set_xticks(xs)
    ax.set_xticklabels(fy, fontsize=10)
    ax.set_ylabel("Export volume (MT)", color=DARK)
    ax.set_ylim(0, 88000)
    ax.legend(frameon=False, fontsize=9, loc="upper left",
              bbox_to_anchor=(0.01, 0.97))
    ax.set_title("India's bajra exports to GCC by market — APEDA (MT)",
                 fontsize=13, pad=12)
    save(fig, 7)


if __name__ == "__main__":
    print("Generating slides 1-7...")
    slide_1(); slide_2(); slide_3(); slide_4()
    slide_5(); slide_6(); slide_7()
    print("Done.")
