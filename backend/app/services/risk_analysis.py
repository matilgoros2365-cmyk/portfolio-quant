"""RiskAnalyzer: análisis de riesgo avanzado de la cartera recomendada.

Junta VaR/CVaR, contribución al riesgo, concentración, look-through y
solapamiento de ETFs sobre la cartera que sale del perfil de riesgo.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.portfolio import RiskProfile
from app.quant.concentration import concentration_summary, look_through_exposures
from app.quant.expected import annualized_covariance, historical_expected_returns
from app.quant.optimization import portfolio_for_risk_level
from app.quant.overlap import weight_overlap
from app.quant.risk import (
    conditional_var_gaussian,
    conditional_var_historical,
    risk_contribution,
    value_at_risk_gaussian,
    value_at_risk_historical,
)
from app.quant.volatility import volatility
from app.schemas.optimization import ProposedWeight
from app.schemas.risk import (
    ConcentrationMetrics,
    ExposureItem,
    OverlapItem,
    RiskAnalysisResponse,
    RiskContributionItem,
    ValueAtRisk,
)
from app.services.analysis import PortfolioAnalyzer
from app.services.market_data.engine import MarketDataEngine
from app.services.market_data.holdings import FundHoldingsService
from app.services.optimizer import (
    InsufficientDataError,
    PortfolioOptimizer,
    resolve_risk_level,
)


def _clean(value: float) -> float | None:
    if value is None:
        return None
    f = float(value)
    return None if (math.isnan(f) or math.isinf(f)) else f


class RiskAnalyzer:
    def __init__(self, db: Session, engine: MarketDataEngine | None = None) -> None:
        self.db = db
        self.mde = engine or MarketDataEngine(db)
        self.optimizer = PortfolioOptimizer(db, engine=self.mde)
        self.holdings = FundHoldingsService(db, provider=self.mde.price_provider)

    def analyze(
        self,
        symbols: list[str],
        risk_profile: RiskProfile | None = None,
        base_currency: str = "USD",
        confidence: float = 0.95,
        max_weight: float | None = None,
        risk_level: float | None = None,
    ) -> RiskAnalysisResponse:
        level, risk_profile = resolve_risk_level(risk_profile, risk_level)
        aligned, names, currencies = self.optimizer._load_aligned_returns(symbols)
        if len(aligned.columns) < 2:
            raise InsufficientDataError(
                "Se necesitan al menos 2 activos con datos para el análisis de riesgo."
            )

        ordered = list(aligned.columns)
        mu = historical_expected_returns(aligned).to_numpy()
        cov = annualized_covariance(aligned).to_numpy()
        rf = PortfolioAnalyzer(self.db, engine=self.mde).get_risk_free_rate()

        weights = portfolio_for_risk_level(mu, cov, level, max_weight)
        weights_by_symbol = {s: float(w) for s, w in zip(ordered, weights)}

        # --- VaR / CVaR sobre los retornos diarios de la cartera ---
        port_daily = pd.Series(aligned.to_numpy() @ weights, index=aligned.index)
        value_at_risk = ValueAtRisk(
            confidence_level=confidence,
            var_historical=_clean(value_at_risk_historical(port_daily, confidence)),
            cvar_historical=_clean(conditional_var_historical(port_daily, confidence)),
            var_gaussian=_clean(value_at_risk_gaussian(port_daily, confidence)),
            cvar_gaussian=_clean(conditional_var_gaussian(port_daily, confidence)),
        )
        ann_vol = float(volatility(port_daily))

        # --- Contribución al riesgo ---
        rc = risk_contribution(weights, cov)
        contributions = [
            RiskContributionItem(
                symbol=s, weight=round(float(w), 4), risk_contribution=round(float(c), 4)
            )
            for s, w, c in zip(ordered, weights, rc)
            if w >= 5e-4
        ]
        contributions.sort(key=lambda x: x.risk_contribution, reverse=True)

        # --- Concentración ---
        conc = concentration_summary(weights)
        concentration = ConcentrationMetrics(
            herfindahl_index=round(conc["herfindahl_index"], 4),
            effective_num_assets=round(conc["effective_num_assets"], 2),
            max_weight=round(conc["max_weight"], 4),
            top3_weight=round(conc["top3_weight"], 4),
        )

        # --- Tenencias, look-through y solapamiento ---
        holdings_map: dict[str, dict[str, float]] = {}
        holding_names: dict[str, str | None] = {}
        for symbol in ordered:
            self.holdings.sync_holdings(symbol)
            h = self.holdings.get_holdings(symbol)
            if h:
                holdings_map[symbol] = h
                holding_names.update(self.holdings.get_holding_names(symbol))

        exposures, coverage_frac = look_through_exposures(
            weights_by_symbol, holdings_map
        )
        top_exposures = sorted(
            (
                ExposureItem(
                    symbol=sym,
                    name=holding_names.get(sym),
                    exposure=round(exp, 4),
                )
                for sym, exp in exposures.items()
                if sym != "_no_cubierto"
            ),
            key=lambda e: e.exposure,
            reverse=True,
        )[:10]

        overlaps: list[OverlapItem] = []
        funds = [s for s in ordered if s in holdings_map]
        for i in range(len(funds)):
            for j in range(i + 1, len(funds)):
                ov = weight_overlap(holdings_map[funds[i]], holdings_map[funds[j]])
                if ov > 0:
                    overlaps.append(
                        OverlapItem(
                            symbol_a=funds[i],
                            symbol_b=funds[j],
                            weight_overlap=round(ov, 4),
                        )
                    )
        overlaps.sort(key=lambda o: o.weight_overlap, reverse=True)

        # --- Notas ---
        notes: list[str] = []
        if len(currencies) > 1:
            notes.append(
                f"Activos en distintas monedas ({', '.join(sorted(currencies))}); "
                f"el riesgo se calcula en moneda nativa (FX a {base_currency} pendiente)."
            )
        if holdings_map:
            notes.append(
                "El solapamiento y el look-through usan solo las principales "
                "tenencias disponibles (datos gratuitos), así que son una "
                f"aproximación: se pudo desagregar el {coverage_frac * 100:.0f}% "
                "de la cartera."
            )
        else:
            notes.append(
                "No se obtuvieron tenencias de los ETFs (datos no disponibles), "
                "así que no hay análisis de solapamiento ni look-through."
            )
        notes.append("VaR/CVaR son diarios (horizonte de 1 día).")

        weight_list = sorted(
            (
                ProposedWeight(symbol=s, name=names.get(s), weight=round(float(w), 4))
                for s, w in zip(ordered, weights)
                if w >= 5e-4
            ),
            key=lambda p: p.weight,
            reverse=True,
        )

        as_of = aligned.index[-1] if len(aligned.index) else None

        return RiskAnalysisResponse(
            base_currency=base_currency,
            risk_profile=risk_profile,
            as_of=as_of,
            n_assets=len(ordered),
            weights=weight_list,
            annualized_volatility=round(ann_vol, 4),
            value_at_risk=value_at_risk,
            risk_contributions=contributions,
            concentration=concentration,
            lookthrough_coverage=round(coverage_frac, 4),
            lookthrough_top=top_exposures,
            etf_overlap=overlaps,
            notes=notes,
        )
