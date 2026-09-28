"""Paquete de modelos ORM.

Importar todos los modelos aquí asegura que queden registrados en
`Base.metadata` antes de crear las tablas.
"""
from app.models.analysis_run import AnalysisRun
from app.models.asset import Asset, AssetType
from app.models.daily_price import DailyPrice
from app.models.fund_holding import FundHolding
from app.models.macro_series import MacroSeries
from app.models.portfolio import Portfolio, RiskProfile

__all__ = [
    "AnalysisRun",
    "Asset",
    "AssetType",
    "DailyPrice",
    "FundHolding",
    "MacroSeries",
    "Portfolio",
    "RiskProfile",
]
