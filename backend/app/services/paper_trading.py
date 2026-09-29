"""PaperTradingService: modo práctica con plata ficticia y precios diferidos."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.paper import (
    INITIAL_CASH,
    PaperAccount,
    PaperPosition,
    PaperTransaction,
)
from app.schemas.paper import (
    HistoryPoint,
    PaperHistory,
    PaperSnapshot,
    PositionOut,
    TransactionOut,
)
from app.services.market_data.engine import MarketDataEngine
from app.services.market_data.yahoo import YahooFinanceProvider

_EPS = 1e-6


class PaperError(ValueError):
    """Error de operación de práctica (fondos, símbolo, etc.)."""


class PaperTradingService:
    def __init__(self, db: Session, provider: object | None = None) -> None:
        self.db = db
        self.provider = provider or YahooFinanceProvider()

    # ------------------------------------------------------------ cuenta
    def get_or_create_account(self, user_id: str) -> PaperAccount:
        acc = self.db.scalar(select(PaperAccount).where(PaperAccount.user_id == user_id))
        if acc is None:
            acc = PaperAccount(user_id=user_id, cash=INITIAL_CASH, initial_cash=INITIAL_CASH)
            self.db.add(acc)
            self.db.commit()
            self.db.refresh(acc)
        return acc

    def _price(self, symbol: str) -> float | None:
        try:
            q = self.provider.get_quote(symbol)  # type: ignore[attr-defined]
            p = q.get("price")
            return float(p) if p is not None else None
        except Exception:  # noqa: BLE001
            return None

    def _position(self, account_id: int, symbol: str) -> PaperPosition | None:
        return self.db.scalar(
            select(PaperPosition).where(
                PaperPosition.account_id == account_id, PaperPosition.symbol == symbol
            )
        )

    # ------------------------------------------------------------ operar
    def buy(self, user_id: str, symbol: str, amount: float) -> None:
        symbol = symbol.upper().strip()
        acc = self.get_or_create_account(user_id)
        if amount <= 0:
            raise PaperError("El monto debe ser mayor a 0.")
        if amount > acc.cash + _EPS:
            raise PaperError(
                f"Saldo insuficiente. Tenés {acc.cash:.2f} y querés invertir {amount:.2f}."
            )
        price = self._price(symbol)
        if price is None or price <= 0:
            raise PaperError(f"No encontramos el precio de '{symbol}'. Revisá el símbolo.")
        qty = amount / price

        pos = self._position(acc.id, symbol)
        if pos is None:
            pos = PaperPosition(account_id=acc.id, symbol=symbol, quantity=qty, avg_cost=price)
            self.db.add(pos)
        else:
            new_qty = pos.quantity + qty
            pos.avg_cost = (pos.quantity * pos.avg_cost + amount) / new_qty
            pos.quantity = new_qty

        acc.cash -= amount
        self.db.add(PaperTransaction(
            account_id=acc.id, symbol=symbol, side="buy",
            quantity=qty, price=price, amount=amount,
        ))
        self.db.commit()

    def sell(self, user_id: str, symbol: str, amount: float | None = None,
             sell_all: bool = False) -> None:
        symbol = symbol.upper().strip()
        acc = self.get_or_create_account(user_id)
        pos = self._position(acc.id, symbol)
        if pos is None or pos.quantity <= 0:
            raise PaperError(f"No tenés {symbol} para vender.")
        price = self._price(symbol)
        if price is None or price <= 0:
            raise PaperError(f"No encontramos el precio de '{symbol}'.")

        if sell_all or amount is None:
            qty_to_sell = pos.quantity
        else:
            qty_to_sell = min(amount / price, pos.quantity)
        proceeds = qty_to_sell * price

        pos.quantity -= qty_to_sell
        acc.cash += proceeds
        if pos.quantity <= _EPS:
            self.db.delete(pos)
        self.db.add(PaperTransaction(
            account_id=acc.id, symbol=symbol, side="sell",
            quantity=qty_to_sell, price=price, amount=proceeds,
        ))
        self.db.commit()

    def buy_portfolio(self, user_id: str, allocations: list[dict],
                      amount: float | None = None) -> list[str]:
        """Compra una canasta repartiendo un monto por pesos. Devuelve avisos."""
        acc = self.get_or_create_account(user_id)
        total = amount if amount is not None else acc.cash
        total = min(total, acc.cash)
        weights_sum = sum(max(a["weight"], 0) for a in allocations) or 1.0
        notes: list[str] = []
        for a in allocations:
            amt = round(total * (max(a["weight"], 0) / weights_sum), 2)
            if amt <= 0:
                continue
            try:
                self.buy(user_id, a["symbol"], amt)
            except PaperError as e:
                notes.append(f"{a['symbol']}: {e}")
        return notes

    def reset(self, user_id: str) -> None:
        acc = self.get_or_create_account(user_id)
        self.db.execute(delete(PaperPosition).where(PaperPosition.account_id == acc.id))
        self.db.execute(delete(PaperTransaction).where(PaperTransaction.account_id == acc.id))
        acc.cash = acc.initial_cash
        self.db.commit()

    # ------------------------------------------------------------ snapshot
    def snapshot(self, user_id: str) -> PaperSnapshot:
        acc = self.get_or_create_account(user_id)
        positions = self.db.scalars(
            select(PaperPosition).where(PaperPosition.account_id == acc.id)
        ).all()

        pos_out: list[PositionOut] = []
        positions_value = 0.0
        invested = 0.0
        for p in positions:
            price = self._price(p.symbol)
            eff_price = price if price is not None else p.avg_cost  # fallback: sin P&L
            market_value = p.quantity * eff_price
            cost_basis = p.quantity * p.avg_cost
            pnl = market_value - cost_basis
            pnl_pct = (market_value / cost_basis - 1) if cost_basis > 0 else None
            positions_value += market_value
            invested += cost_basis
            pos_out.append(PositionOut(
                symbol=p.symbol, quantity=round(p.quantity, 6), avg_cost=round(p.avg_cost, 4),
                price=round(price, 4) if price is not None else None,
                market_value=round(market_value, 2), cost_basis=round(cost_basis, 2),
                pnl=round(pnl, 2), pnl_pct=round(pnl_pct, 4) if pnl_pct is not None else None,
            ))
        pos_out.sort(key=lambda x: x.market_value, reverse=True)

        total_value = acc.cash + positions_value
        total_return = (total_value / acc.initial_cash - 1) if acc.initial_cash > 0 else 0.0

        txns = self.db.scalars(
            select(PaperTransaction)
            .where(PaperTransaction.account_id == acc.id)
            .order_by(PaperTransaction.created_at.desc())
            .limit(30)
        ).all()
        tx_out = [
            TransactionOut(
                symbol=t.symbol, side=t.side, quantity=round(t.quantity, 6),
                price=round(t.price, 4), amount=round(t.amount, 2), created_at=t.created_at,
            )
            for t in txns
        ]

        return PaperSnapshot(
            base_currency=acc.base_currency,
            cash=round(acc.cash, 2), initial_cash=acc.initial_cash,
            invested=round(invested, 2), positions_value=round(positions_value, 2),
            total_value=round(total_value, 2), total_return=round(total_return, 4),
            positions=pos_out, transactions=tx_out,
        )

    # ------------------------------------------------------------ evolución
    def value_history(self, user_id: str, max_points: int = 180, engine=None) -> PaperHistory:
        """Reconstruye el valor de la cartera de práctica día a día (desde el histórico)."""
        acc = self.get_or_create_account(user_id)
        txns = self.db.scalars(
            select(PaperTransaction)
            .where(PaperTransaction.account_id == acc.id)
            .order_by(PaperTransaction.created_at)
        ).all()
        if not txns:
            return PaperHistory(initial_cash=acc.initial_cash, base_currency=acc.base_currency, points=[])

        symbols = sorted({t.symbol for t in txns})
        engine = engine or MarketDataEngine(self.db)
        series: dict[str, pd.Series] = {}
        for s in symbols:
            engine.sync_prices(s)
            df = engine.get_price_dataframe(s)
            if not df.empty:
                series[s] = df["adj_close"]
        if not series:
            return PaperHistory(initial_cash=acc.initial_cash, base_currency=acc.base_currency, points=[])

        start = min(t.created_at.date() for t in txns)
        days = pd.date_range(start=start, end=date.today(), freq="D")
        if len(days) == 0:
            days = pd.DatetimeIndex([pd.Timestamp(date.today())])

        price_df = pd.DataFrame({s: v for s, v in series.items()})
        price_df.index = pd.DatetimeIndex(price_df.index)
        price_df = price_df.reindex(price_df.index.union(days)).sort_index().ffill().reindex(days).ffill().bfill()

        qty_delta = {s: pd.Series(0.0, index=days) for s in symbols}
        cash_delta = pd.Series(0.0, index=days)
        for t in txns:
            ts = pd.Timestamp(t.created_at.date())
            if ts < days[0]:
                ts = days[0]
            qty_delta[t.symbol].loc[ts] += t.quantity if t.side == "buy" else -t.quantity
            cash_delta.loc[ts] += t.amount if t.side == "sell" else -t.amount

        value = acc.initial_cash + cash_delta.cumsum()
        for s in symbols:
            if s in price_df.columns:
                value = value + qty_delta[s].cumsum() * price_df[s].fillna(0.0)

        pts = [(d.date().isoformat(), float(v)) for d, v in value.items() if pd.notna(v)]
        # Downsample si hay muchos puntos (dejando siempre el último).
        if len(pts) > max_points:
            step = len(pts) // max_points + 1
            pts = pts[::step] + [pts[-1]]
        return PaperHistory(
            initial_cash=acc.initial_cash,
            base_currency=acc.base_currency,
            points=[HistoryPoint(date=d, value=round(v, 2)) for d, v in pts],
        )
