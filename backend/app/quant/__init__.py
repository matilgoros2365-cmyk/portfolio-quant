"""Motor cuantitativo: funciones puras, aisladas de DB/API."""
from app.quant.concentration import (
    concentration_summary,
    effective_number_of_assets,
    herfindahl_index,
    look_through_exposures,
    top_n_concentration,
)
from app.quant.correlation import (
    HIGH_CORRELATION_THRESHOLD,
    correlation_matrix,
    covariance_matrix,
    high_correlation_pairs,
)
from app.quant.monte_carlo import (
    simulate_bootstrap,
    simulate_gaussian,
    simulate_student_t,
    summarize_terminal,
    yearly_bands,
)
from app.quant.scenarios import (
    HISTORICAL_CRISES,
    portfolio_scenario_return,
    window_return,
)
from app.quant.overlap import (
    coverage,
    overlapping_holdings,
    weight_overlap,
)
from app.quant.black_litterman import (
    black_litterman_returns,
    implied_equilibrium_returns,
    market_implied_risk_aversion,
)
from app.quant.expected import (
    align_returns,
    annualized_covariance,
    historical_expected_returns,
)
from app.quant.factors import FactorRegressionResult, factor_regression
from app.quant.stability import StabilityResult, resampled_optimization
from app.quant.optimization import (
    OptimizationError,
    efficient_frontier,
    max_return_weights,
    max_sharpe_weights,
    min_variance_for_target,
    min_variance_weights,
    portfolio_for_risk_level,
    portfolio_stats,
    risk_parity_weights,
)
from app.quant.returns import (
    TRADING_DAYS_PER_YEAR,
    annualized_return,
    cagr,
    cumulative_returns,
    geometric_mean_return,
    log_returns,
    simple_returns,
    total_return,
)
from app.quant.risk import (
    DrawdownInfo,
    calmar_ratio,
    conditional_var_gaussian,
    conditional_var_historical,
    drawdown_series,
    max_drawdown,
    max_drawdown_details,
    risk_contribution,
    sharpe_ratio,
    sortino_ratio,
    value_at_risk_gaussian,
    value_at_risk_historical,
    wealth_index,
)
from app.quant.volatility import (
    downside_deviation,
    rolling_volatility,
    volatility,
)

__all__ = [
    "TRADING_DAYS_PER_YEAR",
    "HIGH_CORRELATION_THRESHOLD",
    # returns
    "simple_returns",
    "log_returns",
    "total_return",
    "cumulative_returns",
    "geometric_mean_return",
    "annualized_return",
    "cagr",
    # volatility
    "volatility",
    "downside_deviation",
    "rolling_volatility",
    # correlation
    "correlation_matrix",
    "covariance_matrix",
    "high_correlation_pairs",
    # risk
    "wealth_index",
    "drawdown_series",
    "max_drawdown",
    "max_drawdown_details",
    "DrawdownInfo",
    "sharpe_ratio",
    "sortino_ratio",
    "calmar_ratio",
    # VaR / CVaR / contribución
    "value_at_risk_historical",
    "conditional_var_historical",
    "value_at_risk_gaussian",
    "conditional_var_gaussian",
    "risk_contribution",
    # concentración
    "herfindahl_index",
    "effective_number_of_assets",
    "top_n_concentration",
    "concentration_summary",
    "look_through_exposures",
    # overlap
    "weight_overlap",
    "overlapping_holdings",
    "coverage",
    # monte carlo
    "simulate_gaussian",
    "simulate_student_t",
    "simulate_bootstrap",
    "summarize_terminal",
    "yearly_bands",
    # scenarios
    "HISTORICAL_CRISES",
    "window_return",
    "portfolio_scenario_return",
    # factors
    "factor_regression",
    "FactorRegressionResult",
    # black-litterman
    "implied_equilibrium_returns",
    "black_litterman_returns",
    "market_implied_risk_aversion",
    # stability
    "resampled_optimization",
    "StabilityResult",
    # expected returns
    "historical_expected_returns",
    "annualized_covariance",
    "align_returns",
    # optimization
    "min_variance_weights",
    "max_sharpe_weights",
    "risk_parity_weights",
    "max_return_weights",
    "min_variance_for_target",
    "efficient_frontier",
    "portfolio_for_risk_level",
    "portfolio_stats",
    "OptimizationError",
]
