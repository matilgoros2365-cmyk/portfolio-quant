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
  method: "gaussian" | "student_t" | "bootstrap";
  n_simulations: number;
}

export interface ProposedWeight {
  symbol: string;
  name: string | null;
  weight: number;
}

export interface OptimizedPortfolio {
  strategy: string;
  label: string | null;
  expected_return: number;
  volatility: number;
  sharpe_ratio: number | null;
  weights: ProposedWeight[];
}

export interface Formula {
  formula: string;
  descripcion: string;
}

export interface OptimizationCalculations {
  risk_free_rate: number;
  symbols: string[];
  expected_returns: Record<string, number>;
  volatilities: Record<string, number>;
  correlation_matrix: Record<string, Record<string, number | null>>;
  covariance_matrix: Record<string, Record<string, number | null>>;
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
  analysis_id: number | null;
  recommended: OptimizedPortfolio;
  alternatives: OptimizedPortfolio[];
  reference_portfolios: Record<string, OptimizedPortfolio>;
  efficient_frontier: FrontierPoint[];
  calculations: OptimizationCalculations | null;
  formulas: Record<string, Formula>;
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
  analysis_id: number | null;
  method: string;
  n_simulations: number;
  horizon_years: number;
  total_contributed: number;
  expected_annual_return: number;
  annual_volatility: number;
  terminal: TerminalDistribution;
  yearly_bands: YearBand[];
  historical_scenarios: ScenarioImpact[];
  formulas: Record<string, Formula>;
  notes: string[];
}

export type SimMethod = "gaussian" | "student_t" | "bootstrap";

// ---- Factores ----
export interface FactorExposure {
  factor: string;
  beta: number;
  t_stat: number | null;
}
export interface FactorProfile {
  symbol: string;
  name: string | null;
  alpha_annualized: number | null;
  r_squared: number | null;
  n_obs: number;
  exposures: FactorExposure[];
}
export interface FactorResponse {
  base_currency: string;
  risk_profile: RiskProfile;
  analysis_id: number | null;
  factors: string[];
  factor_legend: Record<string, string>;
  portfolio: FactorProfile;
  assets: FactorProfile[];
  notes: string[];
}

// ---- Robustez ----
export interface ExpectedReturnComparison {
  symbol: string;
  historical: number;
  black_litterman: number;
}
export interface StabilityItem {
  symbol: string;
  recommended_weight: number;
  mean_weight: number;
  std_weight: number;
}
export interface RobustnessResponse {
  base_currency: string;
  risk_profile: RiskProfile;
  analysis_id: number | null;
  risk_aversion: number;
  instability: number;
  n_resamples: number;
  expected_returns: ExpectedReturnComparison[];
  historical_weights: ProposedWeight[];
  black_litterman_weights: ProposedWeight[];
  stability: StabilityItem[];
  notes: string[];
}

// ---- Historial ----
export interface AnalysisSummary {
  id: number;
  kind: string;
  created_at: string;
  risk_profile: string | null;
  base_currency: string | null;
  label: string | null;
}
export interface AnalysisDetail extends AnalysisSummary {
  inputs: Record<string, unknown>;
  result: Record<string, unknown>;
}

// ---- Perfiles locales / onboarding ----
export interface AppUser {
  id: string;
  name: string;
  avatar_color: string | null;
  created_at: string;
}

export interface ProfileResult {
  risk_level: number;
  risk_label: string;
  max_weight: number;
  techo_capacidad: number;
  tolerancia: number;
  capacity_binding: boolean;
  tolerance_binding: boolean;
  overall_confidence: number;
  horizon_years: number | null;
  mc_contribution_factor: number;
  goal_priority: string | null;
  goal_alarm_prob: number;
  exclusions: string[];
  dimensions: Array<{
    name: string;
    score: number;
    confidence: number;
    evidence_count: number;
    contributions: Array<Record<string, unknown>>;
  }>;
}

export interface AssessmentResult {
  id: number;
  user_id: string;
  created_at: string;
  is_current: boolean;
  answers: Record<string, any>;
  profile: ProfileResult;
  derived: Record<string, any>;
}

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
  rationale: string;
  risks: string;
}
export interface ModelPortfolio extends ModelInfo {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number | null;
  weights: ProposedWeight[];
}
export interface GoalReconciliation {
  current_prob: number;
  target_prob: number;
  needs_action: boolean;
  achievable_target: number | null;
  monthly_needed: number | null;
  extra_per_month: number | null;
  years_needed: number | null;
  extra_years: number | null;
}

export interface Recommendation {
  resolved_inputs: Record<string, any>;
  advisor: string; // "ai" | "curated"
  primary_model: ModelInfo;
  optimization: OptimizeResponse;
  simulation: SimulateResponse;
  alternatives: ModelPortfolio[];
  goal_reconciliation: GoalReconciliation | null;
}

// ---- Detalle de activo (precio + qué hay adentro) ----
export interface Quote {
  price: number | null;
  previous_close: number | null;
  change_pct: number | null;
  currency: string;
}
export interface AssetDetail {
  symbol: string;
  quote: Quote;
  composition: {
    kind: string;
    name: string | null;
    category: string | null;
    sector: string | null;
    industry: string | null;
    country: string | null;
    summary: string | null;
    sector_weights: { sector: string; weight: number }[];
    top_holdings: { symbol: string; name: string | null; weight: number }[];
  };
}

// ---- Modo práctica (paper trading) ----
export interface PaperPosition {
  symbol: string;
  quantity: number;
  avg_cost: number;
  price: number | null;
  market_value: number;
  cost_basis: number;
  pnl: number;
  pnl_pct: number | null;
}
export interface PaperTransaction {
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  amount: number;
  created_at: string;
}
export interface PaperSnapshot {
  base_currency: string;
  cash: number;
  initial_cash: number;
  invested: number;
  positions_value: number;
  total_value: number;
  total_return: number;
  positions: PaperPosition[];
  transactions: PaperTransaction[];
}
export interface SearchResult {
  symbol: string;
  name: string;
  type: string;
  exchange: string | null;
}
export interface MarketCatalog {
  categorias: Record<string, { symbol: string; name: string }[]>;
  carteras: { id: string; name: string; tickers: string[]; description: string }[];
}

// ---- Mercado argentino ----
export interface DollarRate {
  name: string;
  buy: number | null;
  sell: number | null;
}
export interface ArgentinaMarket {
  dollars: DollarRate[];
  merval: Quote | null;
  source: string;
  note: string | null;
}
