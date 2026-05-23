const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Fixture = {
  id: number;
  external_id: string;
  home_team: string;
  away_team: string;
  home_team_id: number | null;
  away_team_id: number | null;
  home_team_crest: string | null;
  away_team_crest: string | null;
  league: string;
  kickoff_at: string;
  status: "scheduled" | "finished";
  result: "home" | "draw" | "away" | null;
  home_goals: number | null;
  away_goals: number | null;
};

export type Prediction = {
  id: number;
  fixture_id: number;
  model_name: string;
  home_prob: number;
  draw_prob: number;
  away_prob: number;
  bet_on: "home" | "draw" | "away";
  confidence: number;
  expected_value: number;
  stake: number;
  odds: number;
  reasoning: string;
  prompt_snapshot: string | null;
  status: "pending" | "won" | "lost" | "void";
  profit_loss: number | null;
  settled_at: string | null;
  created_at: string;
  home_value_score: number | null;
  draw_value_score: number | null;
  away_value_score: number | null;
};

export type FixtureWithPredictions = Fixture & { predictions: Prediction[] };

export type ModelPerformance = {
  model_name: string;
  bankroll: number;
  total_bets: number;
  won: number;
  lost: number;
  pending: number;
  win_rate: number;
  roi: number;
  total_profit_loss: number;
};

export async function getFixtures(): Promise<Fixture[]> {
  try {
    const res = await fetch(`${API_URL}/fixtures/`, { cache: "no-store" });
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
}

export async function getFixture(id: number): Promise<FixtureWithPredictions | null> {
  try {
    const res = await fetch(`${API_URL}/fixtures/${id}`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

export async function syncFixtures(): Promise<Fixture[]> {
  const res = await fetch(`${API_URL}/fixtures/sync`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function requestPredictions(fixtureId: number): Promise<Prediction[]> {
  const res = await fetch(`${API_URL}/predictions/request/${fixtureId}`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPredictions(): Promise<Prediction[]> {
  try {
    const res = await fetch(`${API_URL}/predictions/`, { cache: "no-store" });
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
}

export async function getAllFixtures(): Promise<Fixture[]> {
  try {
    const res = await fetch(`${API_URL}/fixtures/?include_past=true`, { cache: "no-store" });
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
}

export type SirKimInput = {
  bet_on: "home" | "draw" | "away";
  stake: number;
};

export async function submitSirKimPrediction(
  fixtureId: number,
  data: SirKimInput,
): Promise<Prediction[]> {
  const res = await fetch(`${API_URL}/predictions/sirkim/${fixtureId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPerformance(): Promise<ModelPerformance[]> {
  try {
    const res = await fetch(`${API_URL}/performance/`, { cache: "no-store" });
    if (!res.ok) return [];
    return res.json();
  } catch { return []; }
}

export type JUserData = {
  current_streak: number;
  longest_streak: number;
  last_reset_at: string | null;
  reset_dates: string[];
};

export type JTrackerData = {
  sir_kim: JUserData;
  me: JUserData;
};

export async function getJTracker(): Promise<JTrackerData | null> {
  try {
    const res = await fetch(`${API_URL}/j-tracker/`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

export async function resetJStreak(user: string): Promise<{ grok_response: string }> {
  const res = await fetch(`${API_URL}/j-tracker/${user}/reset`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

