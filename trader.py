"""Round 2 trading algorithm — Trader class.

Strategy summary (see rd-2-claude-data_analysis.md on round-2-data branch):
- ASH_COATED_OSMIUM (ACO): stationary ~10000 with strong tick mean-reversion.
  Extreme-trigger loads (±max pos at user-defined bounds) PLUS continuous
  opportunistic crossing whenever the book offers price ≥ 2 ticks of edge vs
  fair = 10000, PLUS passive quoting inside the spread when wide.
- INTARIAN_PEPPER_ROOT (PEPPER): deterministic +1000/day linear up-drift.
  Accumulate to position limit early, hold, liquidate before end of run.
"""

from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict


class Trader:
    # --- Products ---
    OSMIUM = "ASH_COATED_OSMIUM"
    PEPPER = "INTARIAN_PEPPER_ROOT"
    POS_LIMIT = 80

    # --- OSMIUM: mean-revert around 10000 ---
    OSMIUM_FAIR = 10000
    OSMIUM_LOWER = 9990.136   # mid at/below this -> load max long
    OSMIUM_UPPER = 10010.89   # mid at/above this -> load max short
    OSMIUM_BUY_EDGE = 2       # buy any ask <= fair - edge
    OSMIUM_SELL_EDGE = 2      # sell any bid >= fair + edge
    OSMIUM_PASSIVE_LOT = 15   # passive quote size inside spread
    OSMIUM_PASSIVE_MIN_SPREAD = 6  # only quote inside when spread this wide

    # --- PEPPER: ride the +1000/day drift ---
    PEPPER_STOP_BUYING_AT = 750_000   # ts after which we stop accumulating
    PEPPER_LIQUIDATE_AT = 999_400   # ts at/after which we unwind

    def bid(self):
        """Round 2 Market Access Fee — blind auction, top 50% gets +25% flow.
        Tune freely; too low risks missing extra volume, too high eats into PnL.
        """
        return 5000

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}
        pos = state.position
        ts = state.timestamp

        if self.OSMIUM in state.order_depths:
            result[self.OSMIUM] = self._osmium(
                state.order_depths[self.OSMIUM], pos.get(self.OSMIUM, 0)
            )

        if self.PEPPER in state.order_depths:
            result[self.PEPPER] = self._pepper(
                state.order_depths[self.PEPPER], pos.get(self.PEPPER, 0), ts
            )

        return result, 0, ""

    def _osmium(self, od: OrderDepth, pos: int) -> List[Order]:
        orders: List[Order] = []
        if not od.sell_orders or not od.buy_orders:
            return orders

        asks = sorted(od.sell_orders.items())                # asc by price
        bids = sorted(od.buy_orders.items(), reverse=True)   # desc by price
        best_bid, best_ask = bids[0][0], asks[0][0]
        mid = (best_bid + best_ask) / 2.0

        buy_cap = self.POS_LIMIT - pos       # max aggregated buy this tick
        sell_cap = pos + self.POS_LIMIT      # max aggregated sell this tick

        # --- Extreme trigger: mid at LOWER -> load max long by crossing asks ---
        if mid <= self.OSMIUM_LOWER:
            for ap, av in asks:
                if buy_cap <= 0:
                    break
                qty = min(buy_cap, -av)
                if qty > 0:
                    orders.append(Order(self.OSMIUM, ap, qty))
                    buy_cap -= qty
            return orders

        # --- Extreme trigger: mid at UPPER -> load max short by hitting bids ---
        if mid >= self.OSMIUM_UPPER:
            for bp, bv in bids:
                if sell_cap <= 0:
                    break
                qty = min(sell_cap, bv)
                if qty > 0:
                    orders.append(Order(self.OSMIUM, bp, -qty))
                    sell_cap -= qty
            return orders

        # --- Opportunistic cross: any ask priced below fair - edge is profit ---
        for ap, av in asks:
            if buy_cap <= 0:
                break
            if ap <= self.OSMIUM_FAIR - self.OSMIUM_BUY_EDGE:
                qty = min(buy_cap, -av)
                orders.append(Order(self.OSMIUM, ap, qty))
                buy_cap -= qty
            else:
                break

        # --- Opportunistic hit: any bid priced above fair + edge is profit ---
        for bp, bv in bids:
            if sell_cap <= 0:
                break
            if bp >= self.OSMIUM_FAIR + self.OSMIUM_SELL_EDGE:
                qty = min(sell_cap, bv)
                orders.append(Order(self.OSMIUM, bp, -qty))
                sell_cap -= qty
            else:
                break

        # --- Passive market-making inside a wide spread ---
        spread = best_ask - best_bid
        if spread >= self.OSMIUM_PASSIVE_MIN_SPREAD:
            join_bid = best_bid + 1
            join_ask = best_ask - 1
            if buy_cap > 0 and join_bid < self.OSMIUM_FAIR:
                q = min(self.OSMIUM_PASSIVE_LOT, buy_cap)
                orders.append(Order(self.OSMIUM, join_bid, q))
            if sell_cap > 0 and join_ask > self.OSMIUM_FAIR:
                q = min(self.OSMIUM_PASSIVE_LOT, sell_cap)
                orders.append(Order(self.OSMIUM, join_ask, -q))

        return orders

    def _pepper(self, od: OrderDepth, pos: int, ts: int) -> List[Order]:
        orders: List[Order] = []
        if not od.sell_orders and not od.buy_orders:
            return orders

        asks = sorted(od.sell_orders.items())
        bids = sorted(od.buy_orders.items(), reverse=True)

        buy_cap = self.POS_LIMIT - pos
        sell_cap = pos + self.POS_LIMIT

        # --- End of run: dump everything ---
        if ts >= self.PEPPER_LIQUIDATE_AT:
            if pos > 0 and bids:
                remaining = min(pos, sell_cap)
                for bp, bv in bids:
                    if remaining <= 0:
                        break
                    qty = min(remaining, bv)
                    orders.append(Order(self.PEPPER, bp, -qty))
                    remaining -= qty
            return orders

        # --- Accumulation window: buy max ---
        if ts < self.PEPPER_STOP_BUYING_AT and buy_cap > 0 and asks:
            for ap, av in asks:
                if buy_cap <= 0:
                    break
                qty = min(buy_cap, -av)
                if qty > 0:
                    orders.append(Order(self.PEPPER, ap, qty))
                    buy_cap -= qty

        return orders
