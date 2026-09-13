Should a Rajasthan bajra exporter enter the GCC millet market — and if so, which country first and on what terms?
The answer is UAE first, with cleaned and graded whole grain at $550/MT CIF Jebel Ali, 2 TEUs per month.
At base-case freight (Drewry WCI) and FX (₹84/USD), the landed-cost model produces a 23.7% gross margin on an $8.0M adjusted market.

## The Analysis

This project models a market-entry decision for a hypothetical Rajasthan-based bajra exporter targeting the GCC. It pulls eight years of UN Comtrade import data and five years of APEDA export data into a SQLite database (`winnow.db`), runs a ten-component landed-cost model from Jodhpur to Jebel Ali, and stress-tests the margin across 30 freight × FX combinations. The output is a 12-slide consulting deck with programmatically generated charts and structured speaker notes. All data collection, transformation, and visualisation is reproducible from the scripts in this repo.

## Recommendation

UAE first. It is the GCC's largest millet market at $8.0M adjusted demand (2023), growing at 4.8% annually, absorbing 47–51% of India's total GCC bajra exports every year on record. India sells into UAE at $0.40/kg against a Kuwait ceiling of $0.44/kg — a quality-premium lever through cleaning and grading. At $550/MT CIF the $419.81 landed cost yields 23.7% gross margin; procurement at $269.76/MT (64% of total) is the only component Rajasthan sourcing can compress. Breakeven FOB is $497, leaving a $53 buffer. Two TEUs per month generates $24,200 in monthly revenue with no fixed-overhead requirement in month one.

## Data Sources

| Source | What it covers | Caveat |
|--------|---------------|--------|
| UN Comtrade (free API) | GCC millet imports + India mirror exports, 2016–2023 | GCC countries do not file partner-disaggregated HS-6; India used as mirror reporter |
| APEDA AgriExchange (free download) | India bajra exports by destination, FY2019–24 | Fiscal year offset vs Comtrade calendar year — used as independent data layer |
| Drewry WCI (public) | JNPT–Jebel Ali ocean freight benchmark | Benchmark rate; actual SME rates will differ |

## Repo Structure

```
winnow-gcc-millet/
├── data/
│   ├── raw/apeda_millet_exports.xls
│   ├── comtrade_cache/
│   └── winnow.db
├── scripts/
│   ├── build_database.py   ← Comtrade pull + SQLite schema
│   ├── load_apeda.py       ← APEDA HTML-XLS parser
│   ├── gen_charts_part1.py ← slides 1–7
│   ├── gen_charts_part2.py ← slides 8–12
│   └── build_deck.py       ← pptx builder
├── charts/
└── outputs/WINNOW_deck.pptx
```

## Reproducing the Analysis

```bash
pip install requests beautifulsoup4 matplotlib python-pptx
export COMTRADE_KEY=<your_key>          # free from comtrade.un.org
python scripts/build_database.py        # pulls Comtrade, writes winnow.db
# download apeda_millet_exports.xls (APEDA AgriExchange, code 0606) → data/raw/
python scripts/load_apeda.py
python scripts/gen_charts_part1.py && python scripts/gen_charts_part2.py
python scripts/build_deck.py            # → outputs/WINNOW_deck.pptx
```

## Key Assumptions

| Assumption | Value | Source |
|-----------|-------|--------|
| Mandi price (bajra) | ₹2,200/quintal | Rajasthan APMC indicative |
| Ocean freight | $45.45/MT | Drewry WCI Q3 2024 |
| Buyer price | $550/MT CIF | APEDA unit-price ceiling proxy |
| FX rate | ₹84/USD | RBI spot Q3 2024 |
| TEU capacity | 22 MT / 20ft FCL | Standard bajra bagging density |
| UAE import duty | 5% of CIF | UAE MFN rate, HS 1008 |

## Limitations

Desk study only — no buyer interviews or mandi price verification. The APEDA fiscal year versus Comtrade calendar year offset makes cross-dividing the two datasets unreliable for market-share calculation; they are used as independent data layers. GCC countries systematically under-report at HS-6, so Comtrade figures understate total millet-derived demand. The freight rate is a public benchmark, not a negotiated SME quote.

## What I Would Do Next

- **Buyer validation**: contact 5–8 UAE importers via Dubai Chamber HS-1008 directory to confirm $550/MT willingness to pay, required certifications (ESMA, FSSAI), and minimum lot size
- **Supply-side verification**: visit Jodhpur-Bikaner APMC to validate ₹2,200/quintal and audit cleaning/grading infrastructure within 50 km
- **Competitive audit**: UAE retail shelf survey to confirm whether India occupies the commodity or premium position at the Kuwait-tier price point
