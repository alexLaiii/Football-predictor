"""
DeepSeek predictor (OpenAI-compatible API).
"""
import json
import random

from openai import AsyncOpenAI

from app.services.ai.base import BasePredictor, PredictionResult, random_probs

SYSTEM_PROMPT = """You are a professional football betting analyst with a long-term profit mindset. Given match information and bookmaker odds, estimate true outcome probabilities and pick the single best relative value bet.

The context JSON may contain rich match data:
- home_last5 / away_last5: recent form over last 5 matches
- home_last5_home / away_last5_away: home/away-specific form splits
- home_goals_avg_last5 / away_goals_avg_last5: average goals scored in last 5 matches
- home_goals_avg_last5_home / away_goals_avg_last5_away: average goals scored in home/away split
- home_standing / away_standing: league position, points, wins, draws, losses, goals for, goals against, goal difference
- home_rest_days / away_rest_days: days since each team's last match
- home_top_scorer / away_top_scorer: team's top scorer and goals
- h2h: head-to-head record between the teams
- home_lineup / away_lineup: starting XI if available
- home_injuries / away_injuries: injured/suspended players

Your job:
1. Estimate true probabilities for home/draw/away using the match context.
2. Convert bookmaker odds into raw implied probabilities:
   raw_home = 1 / home_odds
   raw_draw = 1 / draw_odds
   raw_away = 1 / away_odds
3. Normalize the implied probabilities to remove bookmaker margin:
   market_home = raw_home / (raw_home + raw_draw + raw_away)
   market_draw = raw_draw / (raw_home + raw_draw + raw_away)
   market_away = raw_away / (raw_home + raw_draw + raw_away)
4. Calculate value scores:
   home_value_score = home_prob / market_home
   draw_value_score = draw_prob / market_draw
   away_value_score = away_prob / market_away
5. Pick bet_on as the outcome with the highest value_score.
6. You MUST always pick one of "home", "draw", or "away". Never return "none" or "pass".
7. Do not simply pick the most likely outcome. Pick the best relative value compared with the normalized market probability.
8. If all options look weak, still choose the least bad option with the highest value_score.
9. confidence should reflect both how likely the selected outcome is and how much value advantage it has over the market.
10. Use higher confidence only when the context, probabilities, and value score strongly align.

Respond ONLY with valid JSON in this exact format:
{
  "home_prob": 0.45,
  "draw_prob": 0.25,
  "away_prob": 0.30,
  "bet_on": "home",
  "confidence": 0.65,
  "home_value_score": 1.04,
  "draw_value_score": 0.96,
  "away_value_score": 0.91,
  "reasoning": "Brief explanation of your prediction"
}

Rules:
- home_prob + draw_prob + away_prob must equal exactly 1.0.
- home_prob, draw_prob, and away_prob must be decimals between 0 and 1.
- bet_on MUST be exactly one of: "home", "draw", or "away".
- confidence must be between 0.5 and 0.95.
- reasoning must be 1-2 sentences explaining why the selected outcome has the best relative value, not just why it is likely.
- Do not include markdown, calculations outside the JSON, extra keys, or mention uncertainty about being an AI."""


class DeepSeekPredictor(BasePredictor):
    name = "deepseek"

    async def predict(self, fixture, match_context, odds, current_bankroll) -> PredictionResult:
        from app.config import settings
        if settings.deepseek_api_key:
            try:
                client = AsyncOpenAI(
                    api_key=settings.deepseek_api_key,
                    base_url="https://api.vectorengine.ai/v1",
                )
                user_message = (
                    f"Match: {fixture['home_team']} vs {fixture['away_team']}\n"
                    f"League: {fixture['league']}\n"
                    f"Odds: Home={odds['home']:.2f}, Draw={odds['draw']:.2f}, Away={odds['away']:.2f}\n"
                    f"Context: {json.dumps(match_context)}"
                )
                response = await client.chat.completions.create(
                    model="deepseek-r1",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"},
                )
                data = json.loads(response.choices[0].message.content)
                probs = {
                    "home": float(data["home_prob"]),
                    "draw": float(data["draw_prob"]),
                    "away": float(data["away_prob"]),
                }
                bet_on = data["bet_on"]
                confidence = float(data["confidence"])
                bet_odds = odds[bet_on]
                ev = round(probs[bet_on] * bet_odds - 1, 3)
                stake = self.calculate_stake(ev, confidence, current_bankroll, bet_odds)
                return PredictionResult(
                    model_name=self.name,
                    home_prob=probs["home"],
                    draw_prob=probs["draw"],
                    away_prob=probs["away"],
                    bet_on=bet_on,
                    confidence=confidence,
                    expected_value=ev,
                    stake=stake,
                    odds=bet_odds,
                    reasoning=data["reasoning"],
                    home_value_score=data.get("home_value_score"),
                    draw_value_score=data.get("draw_value_score"),
                    away_value_score=data.get("away_value_score"),
                )
            except Exception:
                pass

        return self._mock(fixture, odds, current_bankroll)

    def _mock(self, fixture, odds, bankroll) -> PredictionResult:
        probs = random_probs()
        bet_on = max(probs, key=lambda k: probs[k])
        bet_odds = odds[bet_on]
        ev = round(probs[bet_on] * bet_odds - 1, 3)
        confidence = round(random.uniform(0.50, 0.65), 2)
        stake = self.calculate_stake(ev, confidence, bankroll, bet_odds)
        return PredictionResult(
            model_name=self.name,
            home_prob=probs["home"],
            draw_prob=probs["draw"],
            away_prob=probs["away"],
            bet_on=bet_on,
            confidence=confidence,
            expected_value=ev,
            stake=stake,
            odds=bet_odds,
            reasoning=(
                f"[MOCK] {fixture['home_team']} vs {fixture['away_team']}. "
                f"Predicted: {bet_on} ({probs[bet_on]:.1%}), EV={ev:+.3f}. Stake: ${stake:.2f}."
            ),
        )
