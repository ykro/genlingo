/** Typed client for the local duel service (duel/, FastAPI on the stage laptop). */

export type Side = "david" | "goliath";
export type Direction = "genz_to_parent" | "parent_to_genz";

export interface ContenderResult {
  name: Side;
  model: string;
  status: "ok" | "offline" | "error";
  text: string;
  latency_ms: number | null;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  chrf: number | null;
  error: string | null;
  price: { input_per_million: number; output_per_million: number; effective_from: string | null } | null;
}

export interface Round {
  id: string;
  number: number | null;
  round_type: "evaluation" | "audience";
  phrase: string;
  direction: Direction;
  country: string;
  reference: string | null;
  david_tag: string;
  david: ContenderResult;
  goliath: ContenderResult;
  winner: Side | "draw" | null;
  win_reason: string | null;
  votes_david: number;
  votes_goliath: number;
}

export interface SideSummary {
  wins: number;
  avg_chrf: number | null;
  p50_latency_ms: number | null;
  cost_usd: number;
  votes: number;
  offline_rounds: number;
}

export interface Scoreboard {
  rounds: number;
  draws: number;
  david: SideSummary;
  goliath: SideSummary;
  david_tag: string;
  david_training: { estimated_cost_usd: number | null; duration_s: number | null; machine: string | null } | null;
}

export interface Health {
  online: boolean;
  ollama: boolean;
  mock: boolean;
  david_tag: string;
  goliath_model: string;
  audience_feed: boolean;
}

export interface QueuedPhrase {
  phrase_id: string;
  text: string;
  direction: Direction;
  country: string;
}

export class DuelClient {
  constructor(private base: string) {}

  private async call<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${this.base}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${res.status}`);
    return data as T;
  }

  health = () => this.call<Health>("/health");
  scoreboard = () => this.call<Scoreboard>("/scoreboard");
  queue = () => this.call<QueuedPhrase[]>("/queue");
  latest = () => this.call<Round[]>("/rounds?limit=1").then((r) => r[0] ?? null);
  duel = (body: { phrase: string; direction: Direction; country: string; phrase_id?: string }) => this.call<Round>("/duel", body);
  evaluation = () => this.call<Round>("/rounds/evaluation", {});
  votes = (id: string) => this.call<{ david: number; goliath: number; live: boolean }>(`/rounds/${id}/votes`);
  close = (id: string) => this.call<Round>(`/rounds/${id}/close`, {});
}
