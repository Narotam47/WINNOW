#!/usr/bin/env python3
"""WINNOW slides 8-12 chart code. Paste after slide_7() in the full script."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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


# ── SLIDE 8: Landed cost stack (horizontal) ───────────────────────────────────
def slide_8():
    items = [
        ("Procurement",     269.76, "#1A5C78"),
        ("Packaging",         9.52, "#2473A0"),
        ("Inland freight",   17.86, "#2E86AB"),
        ("Port charges",     12.00, "#4499BE"),
        ("Fixed export",     19.55, "#6AB0D0"),
        ("Ocean freight",    45.45, "#93C9DF"),
        ("Insurance",         1.87, "#BDE0EE"),
        ("UAE duty 5%",      18.80, "#C0392B"),
        ("Dest. handling",   15.00, "#D9534F"),
        ("Last-mile",        10.00, "#E8837F"),
    ]
    labels = [i[0] for i in items]
    vals   = [i[1] for i in items]
    clrs   = [i[2] for i in items]
    total  = sum(vals)  # 419.81

    fig, ax = new_fig()
    ax.spines[["top", "right", "bottom", "left"]].set_visible(False)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    left = 0.0
    for label, v, c in zip(labels, vals, clrs):
        ax.barh(0, v, left=left, color=c, height=0.45, zorder=3)
        if v >= 9:
            ax.text(left + v / 2, 0,
                    f"${v:.0f}" if v > 20 else f"${v:.1f}",
                    ha="center", va="center", fontsize=7.5,
                    color="white", fontweight="bold")
        left += v

    ax.text(total + 4, 0, f"Total: ${total:.2f}/MT",
            va="center", fontsize=11, color=DARK, fontweight="bold")

    # Legend below bar
    patches = [mpatches.Patch(color=c, label=f"{l}  ${v:.2f}")
               for l, v, c in zip(labels, vals, clrs)]
    ax.legend(handles=patches, fontsize=8.5, loc="upper center",
              bbox_to_anchor=(0.45, -0.12), ncol=2, frameon=False,
              columnspacing=1.5, handlelength=1.2)

    ax.set_xlim(0, 475)
    ax.set_ylim(-0.6, 0.8)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_title(
        "Jodhpur → Jebel Ali landed cost components ($419.81/MT total)",
        fontsize=13, pad=12)
    save(fig, 8)


# ── SLIDE 9: Sensitivity heatmap ─────────────────────────────────────────────
def slide_9():
    fx_vals      = [73, 79, 84, 89, 94]      # ₹/USD
    freight_vals = [35, 43, 51, 59, 67, 75]  # $/MT

    # INR-denominated costs at ₹84: procurement+packaging+inland+port+fixed_export
    INR_BASE  = 328.69
    FIXED_USD = 45.67   # insurance + duty + dest_handling + last_mile
    SELL      = 550.0

    grid = np.array([
        [(SELL - INR_BASE * 84 / fx - fr - FIXED_USD) / SELL * 100
         for fx in fx_vals]
        for fr in freight_vals
    ])

    fig, ax = new_fig()
    ax.spines[["top", "right", "bottom", "left"]].set_visible(False)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    im = ax.imshow(grid, cmap="Blues", aspect="auto", vmin=8, vmax=34)

    for i in range(len(freight_vals)):
        for j in range(len(fx_vals)):
            v = grid[i, j]
            txt_clr = "white" if v > 21 else DARK
            ax.text(j, i, f"{v:.1f}%", ha="center", va="center",
                    fontsize=10.5, color=txt_clr, fontweight="bold")

    # Base case: freight=43 (index 1), FX=84 (index 2)
    base_rect = plt.Rectangle((1.5, 0.5), 1, 1,
                               fill=False, edgecolor=RED, lw=2.5)
    ax.add_patch(base_rect)
    ax.text(2, -0.62, "Base\ncase", ha="center", fontsize=8,
            color=RED, fontweight="bold")

    ax.set_xticks(range(len(fx_vals)))
    ax.set_xticklabels([f"₹{f}" for f in fx_vals], fontsize=11)
    ax.set_yticks(range(len(freight_vals)))
    ax.set_yticklabels([f"${f}/MT" for f in freight_vals], fontsize=10)
    ax.set_xlabel(
        "FX rate ₹/USD  ←  stronger rupee  ·  weaker rupee  →",
        color=DARK, fontsize=10, labelpad=10)
    ax.set_ylabel("Ocean freight ($/MT)", color=DARK, fontsize=10)

    cbar = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label("Gross margin %", color=DARK, fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    ax.set_title(
        "Gross margin sensitivity: ocean freight × FX rate  (selling price $550/MT)",
        fontsize=13, pad=14)
    save(fig, 9)


# ── SLIDE 10: FX risk — margin at five rupee scenarios ───────────────────────
def slide_10():
    fx_vals = [73, 79, 84, 89, 94]
    labels  = ["₹73\n(−13%)", "₹79\n(−6%)", "₹84\nBase", "₹89\n(+6%)", "₹94\n(+12%)"]
    # freight held at $43 (nearest to base $45.45)
    INR_BASE  = 328.69
    FIXED_USD = 45.67
    freight   = 43.0
    SELL      = 550.0

    margins = [(SELL - INR_BASE * 84 / fx - freight - FIXED_USD) / SELL * 100
               for fx in fx_vals]
    # [15.1, 20.3, 24.1, 27.5, 30.4]

    clrs = [RED if m < 16 else ACCENT for m in margins]

    fig, ax = new_fig()
    clean(ax)
    xs   = range(5)
    bars = ax.bar(xs, margins, color=clrs, zorder=3, width=0.52)

    for bar, m in zip(bars, margins):
        ax.text(bar.get_x() + bar.get_width() / 2, m + 0.4,
                f"{m:.1f}%", ha="center", va="bottom",
                fontsize=12, color=DARK, fontweight="bold")

    # Reference lines
    ax.axhline(10, color=RED, lw=1.3, ls=":", zorder=4)
    ax.text(4.65, 10.5, "10% floor", color=RED, fontsize=8.5)
    ax.axhline(0, color=DARK, lw=0.8, zorder=4)

    # Annotate base case
    ax.annotate("", xy=(2, margins[2]),
                xytext=(2, margins[2] + 1), fontsize=0)  # invisible; label done by bar

    # Breakeven annotation
    ax.text(0.5, 3.5,
            "$497 breakeven FOB → $53 below\ncurrent $550 selling price",
            fontsize=8.5, color=MID,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=LGRAY))

    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=10.5)
    ax.set_ylabel("Gross margin (%)", color=DARK)
    ax.set_xlabel("FX rate ₹/USD  (% change vs ₹84 base)", color=DARK)
    ax.set_ylim(0, 37)
    ax.set_title(
        "Rupee appreciation erodes margin — FX sensitivity at base-case freight",
        fontsize=13, pad=12)
    save(fig, 10)


# ── SLIDE 11: 2 TEU revenue model ────────────────────────────────────────────
def slide_11():
    # 22 MT per 20ft FCL; 2 TEUs = 44 MT
    mt_per_teu = 22.0
    sell_price = 550.0
    cost_per_mt = 419.81

    units = [1, 2]
    labels = ["1 TEU\n(22 MT / month)", "2 TEUs\n(44 MT / month)"]
    revenue = [mt_per_teu * n * sell_price for n in units]   # 12100, 24200
    cost    = [mt_per_teu * n * cost_per_mt for n in units]  # 9235.82, 18471.64
    gp      = [r - c for r, c in zip(revenue, cost)]        # 2864.18, 5728.36

    fig, ax = new_fig()
    clean(ax)
    xs = [0, 1]
    ax.bar(xs, cost, color=LGRAY, label="Landed cost", zorder=3, width=0.45)
    ax.bar(xs, gp,   bottom=cost, color=ACCENT, label="Gross profit",
           zorder=3, width=0.45)

    for i, (r, c, g) in enumerate(zip(revenue, cost, gp)):
        # Revenue label above bar
        ax.text(i, r + 280, f"${r:,.0f}", ha="center", va="bottom",
                fontsize=12, color=DARK, fontweight="bold")
        # Cost label inside grey
        ax.text(i, c / 2, f"Cost\n${c:,.0f}", ha="center", va="center",
                fontsize=9, color=MID)
        # GP label inside blue
        ax.text(i, c + g / 2,
                f"GP  ${g:,.0f}\n({g / r * 100:.1f}%)",
                ha="center", va="center", fontsize=9.5,
                color="white", fontweight="bold")

    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylabel("Monthly USD", color=DARK)
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.set_ylim(0, 29500)
    ax.set_title(
        "Revenue and gross profit model: 1 TEU vs 2 TEUs per month",
        fontsize=13, pad=12)
    save(fig, 11)


# ── SLIDE 12: Week-1 action Gantt ────────────────────────────────────────────
def slide_12():
    actions = [
        ("Enroll on APEDA export portal\n(IEC + product registration)",        1, 2),
        ("Contact 3 UAE importers via\nDubai Chamber HS-1008 directory",        2, 4),
        ("Request ECA food-grade certificate\nquote from BIS-accredited lab",   3, 5),
        ("Get freight forwarder pro forma\nJNPT → Jebel Ali, 1 × 20ft FCL",    4, 7),
    ]
    labels = [a[0] for a in actions]
    starts = [a[1] for a in actions]
    ends   = [a[2] for a in actions]

    fig, ax = new_fig()
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    ys = list(range(len(actions)))
    for y, label, s, e in zip(ys, labels, starts, ends):
        ax.barh(y, e - s, left=s, height=0.42, color=ACCENT,
                zorder=3, alpha=0.88)
        ax.text(s - 0.12, y, label, ha="right", va="center",
                fontsize=10, color=DARK)
        ax.text((s + e) / 2, y, f"Day {s}–{e}",
                ha="center", va="center", fontsize=9,
                color="white", fontweight="bold")

    ax.set_xlim(0, 9)
    ax.set_ylim(-0.7, len(actions) - 0.3)
    ax.set_xticks(range(1, 8))
    ax.set_xticklabels([f"Day {d}" for d in range(1, 8)], fontsize=10)
    ax.xaxis.grid(True, color=LGRAY, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.set_yticks([])
    ax.invert_yaxis()
    ax.text(0.5, -0.08,
            "All four tracks run in parallel. Illustrative — not from collected data.",
            transform=ax.transAxes, fontsize=8, color=MID, ha="center")
    ax.set_title("Week 1 action plan: four parallel tracks to first shipment",
                 fontsize=13, pad=12)
    save(fig, 12)


if __name__ == "__main__":
    print("Generating slides 8-12...")
    slide_8()
    slide_9()
    slide_10()
    slide_11()
    slide_12()
    print("Done.")
