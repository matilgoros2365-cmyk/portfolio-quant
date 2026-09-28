import type {
  AnalysisDetail,
  AnalysisSummary,
  FactorResponse,
  FormInputs,
  OptimizeResponse,
  RiskResponse,
  RobustnessResponse,
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
