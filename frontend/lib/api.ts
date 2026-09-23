import type {
  FormInputs,
  OptimizeResponse,
  RiskResponse,
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
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
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
    method: "gaussian",
    n_simulations: 20000,
    random_seed: 42,
  });
}
