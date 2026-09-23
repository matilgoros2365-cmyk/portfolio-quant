// Tipos que reflejan las respuestas del backend (solo los campos que usamos).

export type RiskProfile =
  | "VERY_CONSERVATIVE"
  | "CONSERVATIVE"
  | "MODERATE"
  | "AGGRESSIVE"
  | "VERY_AGGRESSIVE";

export interface FormInputs {
  initial_capital: number;
  monthly_contribution: number;
  investment_horizon_years: number;
  base_currency: string;
  risk_profile: RiskProfile;
  target_wealth: number | null;
  custom_asset_universe: string[];
  max_weight: number | null;
}

export interface ProposedWeight {
  symbol: string;
  name: string | null;
  weight: number;
}

export interface OptimizedPortfolio {
  strategy: string;
  expected_return: number;
  volatility: number;
  sharpe_ratio: number | null;
  weights: ProposedWeight[];
}

export interface FrontierPoint {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number | null;
}

export interface OptimizeResponse {
  base_currency: string;
  risk_profile: RiskProfile;
  risk_free_rate: number;
  as_of: string | null;
  n_assets: number;
  recommended: OptimizedPortfolio;
  reference_portfolios: Record<string, OptimizedPortfolio>;
  efficient_frontier: FrontierPoint[];
  notes: string[];
}

export interface ValueAtRisk {
  confidence_level: number;
  var_historical: number | null;
  cvar_historical: number | null;
  var_gaussian: number | null;
  cvar_gaussian: number | null;
}

export interface RiskContributionItem {
  symbol: string;
  weight: number;
  risk_contribution: number;
}

export interface ConcentrationMetrics {
  herfindahl_index: number;
  effective_num_assets: number;
  max_weight: number;
  top3_weight: number;
}

export interface ExposureItem {
  symbol: string;
  name: string | null;
  exposure: number;
}

export interface OverlapItem {
  symbol_a: string;
  symbol_b: string;
  weight_overlap: number;
}

export interface RiskResponse {
  annualized_volatility: number;
  value_at_risk: ValueAtRisk;
  risk_contributions: RiskContributionItem[];
  concentration: ConcentrationMetrics;
  lookthrough_coverage: number;
  lookthrough_top: ExposureItem[];
  etf_overlap: OverlapItem[];
  notes: string[];
}

export interface TerminalDistribution {
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
  mean: number;
  prob_reaching_target: number | null;
}

export interface YearBand {
  year: number;
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
}

export interface ScenarioImpact {
  name: string;
  start: string;
  end: string;
  portfolio_return: number;
}

export interface SimulateResponse {
  method: string;
  n_simulations: number;
  horizon_years: number;
  total_contributed: number;
  expected_annual_return: number;
  annual_volatility: number;
  terminal: TerminalDistribution;
  yearly_bands: YearBand[];
  historical_scenarios: ScenarioImpact[];
  notes: string[];
}
