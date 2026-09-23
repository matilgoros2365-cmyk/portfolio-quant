"""Motor cuantitativo: funciones puras, aisladas de DB/API."""
from app.quant.correlation import (
    HIGH_CORRELATION_THRESHOLD,
    correlation_matrix,
    covariance_matrix,
    high_correlation_pairs,
)
from app.quant.expected import (
    align_returns,
    annualized_covariance,
    historical_expected_returns,
)
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
    drawdown_series,
    max_drawdown,
    max_drawdown_details,
    sharpe_ratio,
    sortino_ratio,
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
