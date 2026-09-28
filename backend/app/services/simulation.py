"""SimulationService: Monte Carlo + stress tests sobre la cartera recomendada."""
from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from app.models.portfolio import RiskProfile
from app.quant.expected import annualized_covariance, historical_expected_returns
from app.quant.monte_carlo import (
    simulate_bootstrap,
    simulate_gaussian,
    simulate_student_t,
    summarize_terminal,
    yearly_bands,
)
from app.quant.formulas import formulas_subset
from app.quant.optimization import portfolio_for_risk_level, portfolio_stats
from app.quant.scenarios import HISTORICAL_CRISES, portfolio_scenario_return
from app.schemas.optimization import ProposedWeight
from app.schemas.simulation import (
    ScenarioImpact,
    SimulationResponse,
    TerminalDistribution,
    YearBand,
)
from app.services.analysis import PortfolioAnalyzer
from app.services.market_data.engine import MarketDataEngine
from app.services.optimizer import (
    InsufficientDataError,
    PortfolioOptimizer,
    resolve_risk_level,
)

# Cobertura mínima para reportar una crisis (evita números engañosos por
# activos que aún no existían en esa ventana).
MIN_SCENARIO_COVERAGE = 0.99


class SimulationService:
    def __init__(self, db: Session, engine: MarketDataEngine | None = None) -> None:
        self.db = db
        self.mde = engine or MarketDataEngine(db)
        self.optimizer = PortfolioOptimizer(db, engine=self.mde)

    def simulate(
        self,
        symbols: list[str],
        risk_profile: RiskProfile | None = None,
        initial_capital: float = 0.0,
        monthly_contribution: float = 0.0,
        years: int = 10,
        target_wealth: float | None = None,
        method: str = "gaussian",
        n_simulations: int = 10_000,
        student_t_df: int = 5,
        base_currency: str = "USD",
        max_weight: float | None = None,
        seed: int | None = None,
        risk_level: float | None = None,
    ) -> SimulationResponse:
        level, risk_profile = resolve_risk_level(risk_profile, risk_level)
        aligned, names, currencies = self.optimizer._load_aligned_returns(symbols)
        if len(aligned.columns) < 2:
            raise InsufficientDataError(
                "Se necesitan al menos 2 activos con datos para simular."
            )

        ordered = list(aligned.columns)
        mu = historical_expected_returns(aligned).to_numpy()
        cov = annualized_covariance(aligned).to_numpy()
        rf = PortfolioAnalyzer(self.db, engine=self.mde).get_risk_free_rate()

        weights = portfolio_for_risk_level(mu, cov, level, max_weight)
        stats = portfolio_stats(weights, mu, cov, rf)
        mu_annual = stats["expected_return"]
        sigma_annual = stats["volatility"]

        # --- Monte Carlo ---
        if method == "gaussian":
            paths = simulate_gaussian(
                mu_annual, sigma_annual, initial_capital, monthly_contribution,
                years, n_sims=n_simulations, seed=seed,
            )
        elif method == "student_t":
            paths = simulate_student_t(
                mu_annual, sigma_annual, initial_capital, monthly_contribution,
                years, n_sims=n_simulations, df=student_t_df, seed=seed,
            )
        elif method == "bootstrap":
            port_daily = pd.Series(
                aligned.to_numpy() @ weights, index=pd.to_datetime(aligned.index)
            )
            monthly = ((1.0 + port_daily).resample("ME").prod() - 1.0).dropna()
            paths = simulate_bootstrap(
                monthly.to_numpy(), initial_capital, monthly_contribution,
                years, n_sims=n_simulations, seed=seed,
            )
        else:  # pragma: no cover - validado por el schema
            raise ValueError(f"Método desconocido: {method}")

        term = summarize_terminal(paths, target=target_wealth)
        terminal = TerminalDistribution(**term)
        bands = [YearBand(**b) for b in yearly_bands(paths)]

        # --- Escenarios históricos (precios reales) ---
        price_frames = {
            s: self.mde.get_price_dataframe(s)["adj_close"] for s in ordered
        }
        weights_by_symbol = {s: float(w) for s, w in zip(ordered, weights)}
        scenarios: list[ScenarioImpact] = []
        for name, (start, end) in HISTORICAL_CRISES.items():
            ret, coverage = portfolio_scenario_return(
                price_frames, weights_by_symbol, start, end
            )
            if ret is not None and coverage >= MIN_SCENARIO_COVERAGE:
                scenarios.append(
                    ScenarioImpact(
                        name=name, start=start, end=end,
                        portfolio_return=round(ret, 4),
                    )
                )

        # --- Notas ---
        notes: list[str] = [
            "Los retornos esperados salen del histórico; son un supuesto, no "
            "una garantía. Rendimientos pasados no aseguran rendimientos futuros.",
            "Simulación con pasos mensuales; el aporte se suma cada mes.",
        ]
        if len(currencies) > 1:
            notes.append(
                f"Activos en distintas monedas ({', '.join(sorted(currencies))}); "
                f"cálculo en moneda nativa (FX a {base_currency} pendiente)."
            )
        skipped = len(HISTORICAL_CRISES) - len(scenarios)
        if skipped > 0:
            notes.append(
                f"{skipped} crisis histórica(s) se omitieron por falta de datos "
                "de algún activo en esa ventana (ETFs que aún no existían)."
            )

        weight_list = sorted(
            (
                ProposedWeight(symbol=s, name=names.get(s), weight=round(float(w), 4))
                for s, w in zip(ordered, weights)
                if w >= 5e-4
            ),
            key=lambda p: p.weight,
            reverse=True,
        )

        return SimulationResponse(
            base_currency=base_currency,
            risk_profile=risk_profile,
            method=method,
            n_simulations=n_simulations,
            horizon_years=years,
            initial_capital=initial_capital,
            monthly_contribution=monthly_contribution,
            total_contributed=round(initial_capital + monthly_contribution * years * 12, 2),
            expected_annual_return=round(mu_annual, 4),
            annual_volatility=round(sigma_annual, 4),
            weights=weight_list,
            terminal=terminal,
            yearly_bands=bands,
            historical_scenarios=scenarios,
            formulas=formulas_subset(["retorno_esperado", "volatilidad", "monte_carlo"]),
            notes=notes,
        )
