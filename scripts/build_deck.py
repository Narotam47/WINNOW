#!/usr/bin/env python3
"""Build outputs/WINNOW_deck.pptx from charts/slide_N.png.
   pip install python-pptx  →  python scripts/build_deck.py
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

ROOT   = Path(__file__).resolve().parent.parent
CHARTS = ROOT / "charts"
(ROOT / "outputs").mkdir(exist_ok=True)

BLUE = RGBColor(0x2E, 0x86, 0xAB)
DARK = RGBColor(0x22, 0x22, 0x22)
GRAY = RGBColor(0x88, 0x88, 0x88)

# ── Slide content ─────────────────────────────────────────────────────────────
LAYOUTS = ["full_top"] + ["standard"] * 10 + ["full_bottom"]

TITLES = [
    "Enter UAE first with cleaned whole grain at $550/MT: a 23.7% gross margin on an $8.0M adjusted market growing at 4.8% annually",
    "GCC millet imports total $13.7M annually; UAE captures 51%, making it the only single-market entry worth the freight",
    "UAE millet imports grew in six of eight years from 2016 to 2023; the 2020 dip was COVID, not structural",
    "India exports 29,214 MT of bajra to UAE annually — more than to all other GCC markets combined",
    "Kuwait pays $0.44/kg for Indian millet; Oman pays $0.34/kg — a 29% spread driven by grain quality, not geography",
    "Saudi Arabia shrank 84% from 2016 to 2023; the demand it shed did not leave the GCC — it migrated to UAE",
    "India's GCC bajra exports grew 65% by volume over five fiscal years; UAE absorbed nearly half the total every year",
    "The Jodhpur-to-Jebel Ali landed cost is $419.81/MT; procurement at $269.76 is the only component Rajasthan controls",
    "Gross margin ranges from 9.6% to 31.9% across 30 freight and FX scenarios; no combination wipes out profit",
    "The $497/MT breakeven FOB leaves a $53 buffer at ₹84; rupee appreciation is the one risk that closes this gap",
    "Two TEUs per month generates $24,200 in monthly revenue; the model is cash-positive from the first shipment",
    "Register with APEDA, identify one UAE buyer, and book a trial TEU: three actions executable in week one",
]

BULLETS = [
    ["Landed cost from Jodhpur to Jebel Ali is $419.81/MT across ten components; procurement is 64% of total",
     "UAE absorbed $8.01M of millet domestically in 2023 after netting Jebel Ali re-exports",
     "2 TEUs/month at $550/MT generates $24,200 gross revenue; the $130/MT margin is positive from the first container"],
    ["Oman is the second-largest market at $3.06M avg but is dominated by re-export and transit flows via Salalah",
     "Saudi Arabia, Qatar, Bahrain, and Kuwait combined average $3.64M — half of UAE alone",
     "UAE's 51% share has been stable across all five years in the Comtrade dataset"],
    ["UAE total millet imports reached $8.41M in 2023, up 55% from $5.44M in 2016",
     "The adjusted series (net of re-exports) tracks within 5% of total — domestic absorption, not transit trading",
     "2021, 2022, and 2023 each set a new record; post-COVID acceleration is sharper than pre-COVID"],
    ["India's exports to UAE peaked at 33,176 MT in FY2022-23 before normalising to 29,214 MT — still 74% above baseline",
     "UAE absorbs more Indian bajra than Saudi Arabia, Kuwait, Qatar, and Oman combined in every year on record",
     "Unit price fell to $0.336/kg in FY2021-22 as volumes surged, then recovered — commodity-grade bulk compressing price on volume"],
    ["Kuwait receives the highest unit prices despite taking one-sixth of UAE's volume — volume does not explain the premium",
     "Oman's $0.34/kg floor reflects bulk commodity exports likely for re-processing or animal feed",
     "UAE at $0.40/kg sits mid-range; targeting the Kuwait price band ($0.42–$0.44) through grading is a defined price lever"],
    ["Saudi Arabia was the GCC's largest millet market in 2016 at $7.78M; it crossed below UAE in 2017 and never recovered",
     "The 2022 partial rebound ($2.64M) reversed entirely in 2023; two recovery-reversal cycles indicate structural substitution",
     "UAE's 2023 value ($8.41M) now exceeds Saudi Arabia's 2016 peak — the volume migrated, it did not evaporate"],
    ["India's total GCC bajra exports grew from 34,742 MT in FY2019-20 to a peak of 70,478 MT in FY2022-23 — 103% in three years",
     "UAE absorbed 48%–51% of India's total GCC volume in each of the five years — destination concentration is stable",
     "FY2023-24 normalisation to 57,460 MT is a 19% pullback from peak but 65% above the FY2019-20 baseline"],
    ["Procurement ($269.76/MT) is 64% of total landed cost and the only component reducible by sourcing strategy",
     "Ocean freight ($45.45) and UAE duty ($18.80) together add $64.25 — fully external, pass-through costs",
     "Non-procurement subtotal is $150.05/MT — the fixed overhead any Rajasthan-origin exporter must absorb"],
    ["At the worst scenario (₹73/USD, $75/MT freight), gross margin is 9.1% — still cash-positive",
     "FX drives more margin variance than freight: a ₹10 move shifts margin ~4.5 pp; a $16 freight move shifts ~2.9 pp",
     "17 of 30 scenarios produce a margin above 20%; all 30 remain above zero"],
    ["Every ₹1 of rupee appreciation cuts gross margin by ~0.9 pp; a move from ₹84 to ₹73 costs 9 pp",
     "Rupee must strengthen beyond ₹60 to reach zero margin at base freight — a 28% appreciation from current levels",
     "$497 breakeven FOB means a buyer offering less than $497 landed CIF is a no-go; $53 is the negotiating buffer"],
    ["At 2 TEUs/month gross profit is $5,728 — covers a part-time export manager's compensation at Indian market rates",
     "Cost structure is entirely variable at this volume; no fixed overhead beyond APEDA registration required in month one",
     "Scaling from 1 TEU to 2 TEUs doubles gross profit with no change in unit economics — linear until a 3PL is needed"],
    [],
]

SOURCES = [
    "Comtrade HS 100821+100829 (2023); APEDA Product Code 0606 FY2023-24; Jodhpur–Jebel Ali cost model",
    "UN Comtrade HS 100821+100829, annual_summary VIEW (2019–2023 average)",
    "UN Comtrade HS 100821+100829 (2016–2023); re-exports netted via Comtrade flow code RX",
    "APEDA AgriExchange, Product Code 0606 (Millet), FY2019-20 to FY2023-24",
    "APEDA AgriExchange, Product Code 0606 (Millet), FY2023-24",
    "UN Comtrade HS 100821+100829 (2016–2023)",
    "APEDA AgriExchange, Product Code 0606 (Millet), FY2019-20 to FY2023-24",
    "Jodhpur–Jebel Ali cost model; Jebel Ali port tariff (UAE HS 1008 MFN 5%); JNPT rates FY2023-24",
    "Jodhpur–Jebel Ali cost model; sensitivity computed parametrically, 30 freight × FX combinations",
    "Jodhpur–Jebel Ali cost model; RBI USD/INR historical range 2020–2024",
    "Jodhpur–Jebel Ali cost model; 22 MT per 20ft FCL (standard bajra bagging density)",
    "APEDA export portal; Dubai Chamber importer search; UAE ESMA food import requirements",
]

NOTES = [
    "This is the answer — every slide that follows is evidence for one of these three numbers.",
    "Oman's $3.06M looks tempting but nearly all flows through Salalah for re-export; the domestic buyer is much smaller.",
    "The dashed line is what UAE actually consumes; the gap is Jebel Ali re-exports to East Africa.",
    "Unit price drop in FY21-22 is the signal — commodity dumping suppressed price; recovery says market is ready for graded product.",
    "Reference line at $0.441 is the Kuwait ceiling — the price our product should target in UAE retail.",
    "Saudi's decline is structural: local grain policy and domestic sorghum subsidies, not reversible on a 2-year horizon.",
    "Darker UAE segment is constant as a share of the stack every year — that consistency is the argument for supply-chain focus.",
    "The only cost lever is the darkest blue segment — everything to its right is fixed by geography and regulation.",
    "Base case (red box) sits in the upper half of the distribution — deliberately conservative freight and FX assumptions.",
    "Hedge recommendation: six-month forward INR contract on procurement cost; ocean freight is USD-settled.",
    "Left bar is the trial shipment; right bar is steady state — if trial clears customs and buyer pays, you're in business.",
    "If only one track completes in week one, make it the APEDA IEC — without it, nothing else can move.",
]

ACTION_12 = (
    "Deliverable by day 7: APEDA IEC registration submitted  ·  "
    "one buyer NDA requested  ·  freight forwarder quote in hand."
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def prs_new():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    return prs

def blank(prs):
    for layout in prs.slide_layouts:
        if not layout.placeholders:
            return prs.slides.add_slide(layout)
    return prs.slides.add_slide(prs.slide_layouts[6])

def txt(slide, s, l, t, w, h, sz, bold=False, clr=DARK, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run()
    r.text = s; r.font.size = sz; r.font.bold = bold; r.font.color.rgb = clr

def bullets_box(slide, items, src, l, t, w, h):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    first = True
    for b in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph(); first = False
        p.space_before = Pt(5)
        r = p.add_run()
        r.text = f"• {b}"; r.font.size = Pt(13); r.font.color.rgb = DARK
    p = tf.add_paragraph(); p.space_before = Pt(11)
    r = p.add_run()
    r.text = f"Source: {src}"; r.font.size = Pt(9); r.font.color.rgb = GRAY

def img(slide, n, l, t, w_in):
    slide.shapes.add_picture(
        str(CHARTS / f"slide_{n}.png"), Inches(l), Inches(t), width=Inches(w_in))

def set_note(slide, s):
    slide.notes_slide.notes_text_frame.text = s

# ── Layout renderers ──────────────────────────────────────────────────────────
def title_slide(prs):
    sl = blank(prs)
    txt(sl, "WINNOW", 1, 1.8, 11.33, 1.3, Pt(44), bold=True, clr=BLUE, align=PP_ALIGN.CENTER)
    txt(sl, "Should a Rajasthan bajra exporter enter the GCC millet market — and which country first?",
        1, 3.3, 11.33, 1.0, Pt(16), clr=DARK, align=PP_ALIGN.CENTER)
    txt(sl, "Yash Narotam  ·  September 2026",
        1, 6.6, 11.33, 0.5, Pt(12), clr=GRAY, align=PP_ALIGN.CENTER)

def full_top(prs, n, title, bs, src, nt):
    sl = blank(prs)
    txt(sl, title, 0.3, 0.1, 12.7, 0.7, Pt(17), bold=True, clr=BLUE)
    img(sl, n, 2.42, 0.85, 8.5)          # 8.5" wide → ≈5.1" tall; centred
    bullets_box(sl, bs, src, 0.4, 6.05, 12.5, 1.35)
    set_note(sl, nt)

def standard(prs, n, title, bs, src, nt):
    sl = blank(prs)
    txt(sl, title, 0.3, 0.1, 12.7, 0.75, Pt(17), bold=True, clr=BLUE)
    img(sl, n, 0.0, 0.9, 7.9)            # 7.9" wide (≈60%) → ≈4.74" tall
    bullets_box(sl, bs, src, 8.05, 0.9, 5.1, 6.4)
    set_note(sl, nt)

def full_bottom(prs, n, title, src, nt):
    sl = blank(prs)
    txt(sl, title, 0.3, 0.1, 12.7, 0.7, Pt(17), bold=True, clr=BLUE)
    img(sl, n, 1.67, 0.85, 10.0)         # 10" wide → 6.0" tall; centred
    txt(sl, ACTION_12, 0.4, 6.95, 12.5, 0.4, Pt(13), clr=DARK)
    txt(sl, f"Source: {src}", 0.4, 7.2, 12.5, 0.25, Pt(9), clr=GRAY)
    set_note(sl, nt)

# ── Build ─────────────────────────────────────────────────────────────────────
def build():
    prs = prs_new()
    title_slide(prs)
    for i, (lay, ti, bs, src, nt) in enumerate(
            zip(LAYOUTS, TITLES, BULLETS, SOURCES, NOTES), 1):
        if lay == "full_top":
            full_top(prs, i, ti, bs, src, nt)
        elif lay == "full_bottom":
            full_bottom(prs, i, ti, src, nt)
        else:
            standard(prs, i, ti, bs, src, nt)
    out = ROOT / "outputs" / "WINNOW_deck.pptx"
    prs.save(str(out))
    print(f"Saved → {out}")

if __name__ == "__main__":
    build()
