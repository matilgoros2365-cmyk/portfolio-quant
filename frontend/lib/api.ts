import type {
  AnalysisDetail,
  AnalysisSummary,
  AppUser,
  ArgentinaMarket,
  AssessmentResult,
  AssetDetail,
  FactorResponse,
  FormInputs,
  MarketCatalog,
  OptimizeResponse,
  PaperSnapshot,
  Recommendation,
  RiskResponse,
  RobustnessResponse,
  SearchResult,
  SimulateResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json() as Promise<T>;
}

async function errorDetail(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (data?.detail)
      return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
  } catch {
    /* ignore */
  }
  return `Error ${res.status}`;
}

export function optimize(inputs: FormInputs) {
  return post<OptimizeResponse>("/portfolio/optimize", inputs);
}

export function analyzeRisk(inputs: FormInputs) {
  return post<RiskResponse>("/portfolio/risk", { ...inputs, confidence_level: 0.95 });
}

export function simulate(inputs: FormInputs) {
  return post<SimulateResponse>("/portfolio/simulate", {
    ...inputs,
    method: inputs.method,
    n_simulations: inputs.n_simulations,
    random_seed: 42,
  });
}

export function analyzeFactors(inputs: FormInputs) {
  return post<FactorResponse>("/portfolio/factors", inputs);
}

export function analyzeRobustness(inputs: FormInputs) {
  return post<RobustnessResponse>("/portfolio/robustness", {
    ...inputs,
    n_resamples: 200,
    random_seed: 42,
  });
}

export function listAnalyses(limit = 50) {
  return get<AnalysisSummary[]>(`/analyses?limit=${limit}`);
}

export function getAnalysis(id: number) {
  return get<AnalysisDetail>(`/analyses/${id}`);
}

// ---- Perfiles locales / onboarding ----
export function listUsers() {
  return get<AppUser[]>("/users");
}

export function createUser(name: string, avatar_color?: string) {
  return post<AppUser>("/users", { name, avatar_color });
}

export function createAssessment(userId: string, answers: Record<string, unknown>) {
  return post<AssessmentResult>(`/users/${userId}/assessments`, { answers });
}

export async function getCurrentAssessment(userId: string): Promise<AssessmentResult | null> {
  try {
    return await get<AssessmentResult>(`/users/${userId}/assessments/current`);
  } catch {
    return null; // 404 = todavía no completó el cuestionario
  }
}

export function getRecommendation(userId: string) {
  return get<Recommendation>(`/users/${userId}/recommendation`);
}

export function getAssetDetail(symbol: string) {
  return get<AssetDetail>(`/market-data/${symbol}/detail`);
}

export function getArgentinaMarket() {
  return get<ArgentinaMarket>("/market/argentina");
}

// ---- Modo práctica (paper trading) ----
export function getPaper(userId: string) {
  return get<PaperSnapshot>(`/users/${userId}/paper`);
}
export function paperBuy(userId: string, symbol: string, amount: number) {
  return post<PaperSnapshot>(`/users/${userId}/paper/buy`, { symbol, amount });
}
export function paperSell(userId: string, symbol: string, opts: { amount?: number; all?: boolean }) {
  return post<PaperSnapshot>(`/users/${userId}/paper/sell`, { symbol, ...opts });
}
export function paperBuyPortfolio(
  userId: string,
  allocations: { symbol: string; weight: number }[],
  amount?: number
) {
  return post<PaperSnapshot>(`/users/${userId}/paper/buy-portfolio`, { allocations, amount });
}
export function paperReset(userId: string) {
  return post<PaperSnapshot>(`/users/${userId}/paper/reset`, {});
}
export function searchMarket(q: string) {
  return get<SearchResult[]>(`/market/search?q=${encodeURIComponent(q)}`);
}
export function getCatalog() {
  return get<MarketCatalog>("/market/catalog");
}
