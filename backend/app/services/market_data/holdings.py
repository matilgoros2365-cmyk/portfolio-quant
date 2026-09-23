"""Servicio de tenencias de fondos: descarga (una vez) y cachea en la base."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.fund_holding import FundHolding
from app.services.market_data.yahoo import YahooFinanceProvider


class FundHoldingsService:
    def __init__(self, db: Session, provider: object | None = None) -> None:
        self.db = db
        self.provider = provider or YahooFinanceProvider()

    def sync_holdings(self, fund_symbol: str) -> int:
        """Descarga las tenencias si no las tenemos cacheadas. Devuelve cuántas insertó."""
        fund = fund_symbol.upper()
        existing = self.db.scalar(
            select(FundHolding).where(FundHolding.fund_symbol == fund)
        )
        if existing is not None:
            return 0  # ya cacheado

        getter = getattr(self.provider, "get_fund_holdings", None)
        if getter is None:
            return 0
        data = getter(fund)
        rows = [
            FundHolding(
                fund_symbol=fund,
                holding_symbol=holding,
                holding_name=meta.get("name"),
                weight=float(meta["weight"]),
            )
            for holding, meta in data.items()
        ]
        if rows:
            self.db.add_all(rows)
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                return 0
        return len(rows)

    def get_holdings(self, fund_symbol: str) -> dict[str, float]:
        rows = self.db.scalars(
            select(FundHolding).where(
                FundHolding.fund_symbol == fund_symbol.upper()
            )
        ).all()
        return {r.holding_symbol: r.weight for r in rows}

    def get_holding_names(self, fund_symbol: str) -> dict[str, str | None]:
        rows = self.db.scalars(
            select(FundHolding).where(
                FundHolding.fund_symbol == fund_symbol.upper()
            )
        ).all()
        return {r.holding_symbol: r.holding_name for r in rows}
