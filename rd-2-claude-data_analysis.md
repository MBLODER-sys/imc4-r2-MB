# Round 2 — Data Analysis (Claude)

Analysis of `prices_round_2_day_{-1,0,1}.csv` and `trades_round_2_day_{-1,0,1}.csv`.
Each day = 10,000 order-book snapshots per product (100 ts step). Rows where both
best-bid and best-ask were NaN (`mid = 0`) were dropped as empty-book snapshots.
All analysis below uses the *cleaned* samples (~9,200/10,000 per product/day).

Priority target: **TG01 = `ASH_COATED_OSMIUM`** (ACO).

---

## 1. TL;DR strategy-relevant takeaways

### ASH_COATED_OSMIUM (TG01) — stationary, strong mean-reversion
- **Fair value ≈ 10,000.** Median mid = 10000 / 10001 / 10002 across the 3 days.
  Across-day mid mean = 10000.2; std only ~4.5.
- **Very tight support**: 76% of mids ∈ [9995, 10005]; 97% ∈ [9990, 10010];
  99.9% ∈ [9985, 10015]. Range never exceeds ±22 from 10000.
- **Strong tick-level mean reversion**: AR(1) of tick returns ≈ **−0.49** on all
  three days — roughly half of any price move is reversed next tick.
- **Order-book imbalance is a strong directional signal**:
  `corr(imbalance_t, mid_return_{t+1}) ≈ +0.58`. Bigger bid side at L1 ⇒ up-tick.
- **Typical spread = 16** (≈63% of ticks). Other modes: 18, 19, 21. Tight
  spreads (5–12) occur ~5% — high-quality cross opportunities.
- L1 volumes symmetric: bid_vol1 ≈ ask_vol1 ≈ 14 (std 5, range 2–30).
- Deep book: L2 present ~65% of ticks, L3 only ~2.4%.
- Trade flow: ~465 trades/day, qty_mean ≈ 5, qty_max = 10, total volume
  ≈ 2,375/day, trade prices centered at 10000 with std ≈ 9.
- Position limit 80 ⇒ ample headroom vs typical qty/trade (5) and L1 vol (14).

**Implication — build a mean-reverting market maker:**
1. Treat fair value as **10,000** (or a very short EWMA of mid, say α≈0.2).
2. On each tick compute `edge = fair − mid`. If `|edge| ≥ ~2`, aggressively
   lean in the reverting direction; at `|edge| ≥ ~4–5`, size up to limits.
3. Add an **imbalance overlay**: `imb = (bid_v1 − ask_v1) / (bid_v1 + ask_v1)`.
   Shade quotes up if `imb > 0`, down if `imb < 0`; skew size similarly.
4. Passive quoting: post 1–2 ticks inside the typical 16-wide spread
   (e.g., buy 9999, sell 10001) when inventory neutral; widen/skew with
   inventory or imbalance.
5. Cross the book when sell orders exist at ≤ 9998 or buy orders at ≥ 10002;
   very profitable given 99% of mids fall back toward 10000 within a few ticks.

### INTARIAN_PEPPER_ROOT (IPR) — deterministic up-drift + mean reversion
- **Exact linear up-drift of +1000 per day** on all three days:
  - day −1: first mid 11001.5 → last 11999.5 (mean 11501)
  - day 0:  first mid 11998.5 → last 13000.0 (mean 12501)
  - day 1:  first mid 13000.0 → last 13999.5 (mean 13500)
- Regression slope = **1.000 × 10⁻³ per timestamp unit** = **+1 per 10 ticks**
  (ts step is 100). This is strikingly consistent across days.
- **Around the trend it mean-reverts** just like ACO: AR(1) of tick returns ≈ **−0.49**.
- Spread: mean 13 → 14 → 15 (grows ~1 per day). L1 volumes ~11.5 each side.
- Trade qty_max = 8 (vs 10 for ACO); ~333 trades/day, volume ~1,680/day.
- Trade price_mean is **above** mid_mean on each day (e.g., day 0: 12535 vs
  12501) — market takers lifting the offer as the price trends up (trend
  followers crossing on the way up).

**Implication — trend-adjusted market maker:**
1. Fair value model: `fv(t) = fv_start_of_day + 0.01 * (timestamp − ts_start)`.
   For unknown day, initialize `fv_start` from first observed mid; confirm slope
   live via EWMA of returns (expected slope = 0.01 per ts, i.e., +1 per 10 ticks).
2. Because the drift is small relative to the noise std (tick σ ≈ 1.9 vs drift
   0.1/tick), each trade decision is dominated by mean reversion around
   `fv(t)` — same playbook as ACO but with the moving target.
3. **Do NOT fade the trend blindly**: holding a short at 12000 on day 0 bleeds
   ~1000 by day-end. Cap short inventory when mid is below `fv(t)`.

### Market-Access-Fee (MAF) framing
- Both products offer modest edge per tick (mean-reversion amplitude ~2–5).
  +25% flow ≈ +25% gross PnL if strategy scales linearly (position limit 80 is
  rarely binding at our typical 5–10 lot flow, so extra flow should translate).
- Rough expected gross PnL upside from MAF per round (not rigorous, placeholder):
  order of magnitude ~10k–40k XIRECs depending on algo quality. Bid should be
  well under that cap to preserve net PnL. See Task 3 follow-up for a precise
  bid sizing once we finalize the algorithm.

---

## 2. ASH_COATED_OSMIUM — detailed stats per day (cleaned)

| metric | day −1 | day 0 | day 1 |
|---|---|---|---|
| snapshots kept | 9,237 | 9,257 | 9,214 |
| mid mean | 10000.83 | 10001.58 | 10000.15 |
| mid median | 10001 | 10002 | 10000 |
| mid std | 3.86 | 5.22 | 4.48 |
| mid min / max | 9986 / 10014 | 9982 / 10020 | 9985 / 10014 |
| mid q01 / q99 | 9991 / 10009.5 | 9988 / 10014 | 9990.5 / 10010 |
| tick-return std | 1.90 | 1.86 | 1.89 |
| tick `|return|` mean | 1.24 | 1.22 | 1.22 |
| **AR(1) of returns** | **−0.489** | **−0.469** | **−0.488** |
| spread mean / median | 16.22 / 16 | 16.25 / 16 | 16.23 / 16 |
| spread min / max | 5 / 21 | 5 / 21 | 5 / 22 |
| bid_vol1 mean (std) | 14.20 (5.35) | 14.31 (5.43) | 14.24 (5.35) |
| ask_vol1 mean (std) | 14.23 (5.38) | 14.18 (5.32) | 14.20 (5.38) |
| **corr(imb_t, ret_{t+1})** | **+0.592** | **+0.585** | **+0.580** |
| corr(mid−10000_t, ret_{t+1}) | −0.246 | −0.178 | −0.211 |
| P(`|mid−10000|` ≤ 2) | 0.478 | 0.382 | 0.390 |
| P(`|mid−10000|` ≤ 5) | 0.823 | 0.695 | 0.763 |
| trades / day | 459 | 471 | 465 |
| trade qty total | 2,348 | 2,404 | 2,375 |
| trade qty mean / max | 5.12 / 10 | 5.10 / 10 | 5.11 / 10 |
| trade price mean | 10000.88 | 10000.98 | 10000.09 |
| trade price std | 8.97 | 9.83 | 9.22 |
| trade price range | [9982, 10019] | [9979, 10020] | [9980, 10018] |

**Spread distribution — ACO day 0 (cleaned):**

| spread | count |
|---|---|
| 5 | 56 |
| 6 | 99 |
| 7 | 47 |
| 8 | 23 |
| 9 | 98 |
| 10 | 217 |
| 11 | 94 |
| 12 | 44 |
| 13 | 42 |
| 15 | 17 |
| **16** | **5,855** |
| 17 | 20 |
| 18 | 1,162 |
| 19 | 1,228 |
| 20 | 3 |
| 21 | 252 |

The mode at spread=16, with second modes at 18/19/21, suggests two bot regimes:
a "tight" regime occasionally at ≤12 (opportunity to get crossed), and the
dominant "wide" regime at 16–21 where we can quote inside profitably.

**Top ACO mid values across all 3 days (cleaned, n = 27,708):**

| mid | count |
|---|---|
| 10001 | 2,317 |
| 10002 | 2,310 |
| 10000 | 1,985 |
| 10003 | 1,876 |
| 9999 | 1,675 |
| 10004 | 1,501 |
| 9998 | 1,415 |
| 9997 | 1,343 |
| 10005 | 1,175 |
| 9996 | 991 |
| 10006 | 898 |
| 10007 | 701 |
| 9995 | 689 |
| 10000.5 | 526 |
| 9994 | 525 |
| 10008 | 515 |

Probability mass:
- P(mid ∈ [9995, 10005]) = **0.760**
- P(mid ∈ [9990, 10010]) = **0.970**
- P(mid ∈ [9985, 10015]) = **0.999**

---

## 3. INTARIAN_PEPPER_ROOT — detailed stats per day (cleaned)

| metric | day −1 | day 0 | day 1 |
|---|---|---|---|
| snapshots kept | 9,246 | 9,230 | 9,248 |
| mid mean | 11501.16 | 12501.43 | 13500.11 |
| mid median | 11502 | 12501.75 | 13499.5 |
| mid std | 288.27 | 288.46 | 289.16 |
| mid min / max | 10998 / 12002 | 11998 / 13000 | 12997 / 14001 |
| first / last mid | 11001.5 / 11999.5 | 11998.5 / 13000.0 | 13000.0 / 13999.5 |
| **linear slope (per ts unit)** | **1.000e-3** | **1.000e-3** | **1.000e-3** |
| per-10k ts drift | +10.00 | +10.00 | +10.00 |
| tick-return std | 1.75 | 1.88 | 2.03 |
| tick `|return|` mean | 1.08 | 1.15 | 1.25 |
| **AR(1) of returns** | **−0.492** | **−0.496** | **−0.496** |
| spread mean / median | 13.07 / 13 | 14.12 / 14 | 15.18 / 15 |
| spread min / max | 2 / 19 | 2 / 21 | 2 / 22 |
| bid_vol1 mean | 11.59 | 11.60 | 11.58 |
| ask_vol1 mean | 11.57 | 11.56 | 11.56 |
| trades / day | 331 | 332 | 333 |
| trade qty total | 1,669 | 1,671 | 1,693 |
| trade qty mean / max | 5.04 / 8 | 5.03 / 8 | 5.08 / 8 |
| trade price mean | 11540.49 | 12535.24 | 13526.27 |
| trade price std | 284.99 | 287.63 | 289.88 |
| trade price range | [10996, 11998] | [11998, 12987] | [12998, 13999] |

**IPR spread distribution — day 0 (cleaned):**

| spread | count |
|---|---|
| 2 | 56 |
| 3 | 123 |
| 4 | 67 |
| 5 | 9 |
| 6 | 25 |
| 7 | 17 |
| 8 | 19 |
| 9 | 57 |
| 10 | 43 |
| 12 | 12 |
| **13** | **3,079** |
| **14** | **3,037** |
| 15 | 1 |
| 16 | 940 |
| 17 | 1,425 |
| 18 | 61 |
| 19 | 89 |
| 20 | 149 |
| 21 | 21 |

Bimodal around 13/14 and 16/17 — similar two-regime structure as ACO but
narrower overall. Very tight spreads (2–10) ~4% of time — prime crossing
opportunities.

---

## 4. Key model relationships (for Trader implementation)

### 4.1 Fair-value estimators
- **ACO**: `fv_ACO = 10000`. Could alternatively use `EWMA(mid, α=0.1)` to
  adapt slowly; test shows SMA/EWMA deviations have std ~378 (polluted by
  zero-mid rows) — cleaned std ≈ 4. Anchor-to-10000 wins at this sample size.
- **IPR**: `fv_IPR(ts, day) = f0 + 0.01 * ts_in_round`, where `f0` is the first
  observed mid at start of the round. Robust fallback: `fv = EWMA(mid, α=0.02)`
  and add an estimated drift term `+0.01/tick`.

### 4.2 Signals & rules of thumb
- **`edge = fv − mid`**. Signal quality of edge for ACO: corr with next return
  ≈ −0.2 (expected magnitude of reversion ≈ 20% per tick).
- **`imb = (bidv − askv)/(bidv + askv)`**. Stronger than edge for 1-step-ahead:
  corr ≈ +0.58. Predictive gain from using imbalance > using mid alone.
- **Expected next-return model (linear, approximate)**:
  `E[r_{t+1}] ≈ 0.20 * edge + 1.0 * imb * σ_tick`  with `σ_tick ≈ 1.9`.
  (coefficients rough; re-fit live if needed.)

### 4.3 Position sizing heuristics
- Position limit 80, typical qty/trade 5, L1 vol 14 ⇒ we can take 5-lot
  clips aggressively without hitting the limit unless we accumulate >16
  consecutive same-side trades.
- Keep a soft inventory band ±40 for ACO; widen quotes as |pos| grows;
  fully unwind before day end is not required (round-over-round position
  carry rules: assume positions reset — if not, need end-of-day flattening).

### 4.4 Execution opportunities (crossing)
- **ACO**: cross sell orders priced ≤ **9998** (buy) or buy orders priced
  ≥ **10002** (sell). Expected mean reversion pays ≥ 2 per lot on average.
- **IPR**: cross when `(ask ≤ fv − 2)` or `(bid ≥ fv + 2)`, using the drift-
  adjusted `fv(ts)`. Be more conservative near start/end of day where the
  slope hand-off between days could introduce boundary error.

---

## 5. Data-quality notes

- ~3% of rows per product/day have `mid = 0` (both sides empty) and were
  excluded — at runtime, treat such ticks as "do nothing, preserve last FV".
- L3 book level is populated <2.5% of the time for ACO, <1.6% for IPR — don't
  rely on L3 for signals.
- Trade rows have empty `buyer`/`seller` strings in the historical files
  (counterparty redacted, as spec says). Live trades with `SUBMISSION` tag
  will let us distinguish our own fills.

---

## 6. Open questions to revisit

1. Does the IPR +1000/day drift continue in Round 2 final simulation (the
   three provided days are perfectly aligned — this looks designed-in, not
   random)? If yes, the drift is a *known* alpha we should bake in as a hard
   rule, not re-estimate.
2. Is the `+0.01 per timestamp` slope rounded exactly or just very close? The
   fitted slope was 1.000003e-3, 9.999919e-4, 1.000029e-3 — noise-level
   deviation, effectively constant.
3. Does the Round-2 MAF (+25% flow) preserve the same bot spread/imbalance
   distribution? Spec says "volumes and prices of these quotes fit perfectly
   in the distribution of the already available quotes" — assume yes, our
   strategy should be scale-invariant to that extra flow.
4. Sanity-check: the two-regime spread distribution (tight ~5%, wide ~95%)
   may indicate two different bot personalities. Worth per-tick classifying
   and adapting quote aggressiveness.
