"use client";

import { useState } from "react";
import type { Prediction, Fixture } from "@/lib/api";
import PredictionDetailModal from "@/components/PredictionDetailModal";

const PREDICTORS: { key: string; label: string; color: string }[] = [
  { key: "sirkim",   label: "Sir Kim",  color: "bg-yellow-500" },
  { key: "claude",   label: "Claude",   color: "bg-violet-500" },
  { key: "gpt5",     label: "ChatGPT",  color: "bg-green-500"  },
  { key: "gemini",   label: "Gemini",   color: "bg-blue-500"   },
  { key: "grok",     label: "Grok",     color: "bg-orange-500" },
  { key: "deepseek", label: "DeepSeek", color: "bg-cyan-500"   },
];

const STATUS_STYLE: Record<string, string> = {
  won:     "text-green-400",
  lost:    "text-red-400",
  pending: "text-wc-muted",
  void:    "text-wc-muted/50",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function cutoff3Days() {
  const d = new Date();
  d.setDate(d.getDate() - 3);
  return d;
}

type Props = {
  predictions: Prediction[];
  fixtureMap: Record<number, Fixture>;
};

function PredictorSection({
  predictor,
  predictions,
  fixtureMap,
}: {
  predictor: (typeof PREDICTORS)[number];
  predictions: Prediction[];
  fixtureMap: Record<number, Fixture>;
}) {
  const [open, setOpen] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [selected, setSelected] = useState<Prediction | null>(null);

  const threshold = cutoff3Days();
  const recent = predictions.filter((p) => new Date(p.created_at) >= threshold);
  const displayed = showAll ? predictions : recent;
  const hiddenCount = predictions.length - recent.length;

  return (
    <div className="rounded-xl border border-wc-border overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-wc-card hover:bg-wc-blue/10 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${predictor.color}`} />
          <span className="text-sm font-semibold text-white">{predictor.label}</span>
          <span className="text-xs text-wc-muted">
            ({predictions.length} bet{predictions.length !== 1 ? "s" : ""})
          </span>
        </div>
        <span className="text-wc-muted text-xs">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div>
          {displayed.length === 0 ? (
            <div className="bg-wc-navy px-4 py-8 text-center text-sm text-wc-muted">
              No bets in the last 3 days.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-wc-navy text-wc-muted text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-2 text-left">Date</th>
                    <th className="px-4 py-2 text-left">Match</th>
                    <th className="px-4 py-2 text-left">Bet</th>
                    <th className="px-4 py-2 text-right">Odds</th>
                    <th className="px-4 py-2 text-right">Stake</th>
                    <th className="px-4 py-2 text-right">P&amp;L</th>
                    <th className="px-4 py-2 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-wc-border">
                  {displayed.map((p) => {
                    const f = fixtureMap[p.fixture_id];
                    return (
                      <tr
                        key={p.id}
                        onClick={() => setSelected(p)}
                        className="bg-wc-navy hover:bg-wc-card transition-colors cursor-pointer"
                      >
                        <td className="px-4 py-3 text-wc-muted whitespace-nowrap">
                          {formatDate(p.created_at)}
                        </td>
                        <td className="px-4 py-3 text-white whitespace-nowrap">
                          {f ? `${f.home_team} vs ${f.away_team}` : `Fixture #${p.fixture_id}`}
                        </td>
                        <td className="px-4 py-3 capitalize text-white">{p.bet_on}</td>
                        <td className="px-4 py-3 text-right font-mono text-wc-muted">
                          {p.odds.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-wc-muted">
                          ${p.stake.toFixed(2)}
                        </td>
                        <td
                          className={`px-4 py-3 text-right font-mono ${
                            p.profit_loss !== null
                              ? p.profit_loss >= 0
                                ? "text-green-400"
                                : "text-red-400"
                              : "text-wc-muted"
                          }`}
                        >
                          {p.profit_loss !== null
                            ? `${p.profit_loss >= 0 ? "+" : ""}$${p.profit_loss.toFixed(2)}`
                            : "—"}
                        </td>
                        <td
                          className={`px-4 py-3 text-right capitalize ${
                            STATUS_STYLE[p.status] ?? "text-wc-muted"
                          }`}
                        >
                          {p.status}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {hiddenCount > 0 && !showAll && (
            <div className="px-4 py-3 bg-wc-navy border-t border-wc-border text-center">
              <button
                onClick={() => setShowAll(true)}
                className="text-xs text-wc-gold hover:underline"
              >
                View More ({hiddenCount} older bet{hiddenCount !== 1 ? "s" : ""})
              </button>
            </div>
          )}
        </div>
      )}

      {selected && (
        <PredictionDetailModal
          prediction={selected}
          fixture={fixtureMap[selected.fixture_id]}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}

export default function HistoryClient({ predictions, fixtureMap }: Props) {
  return (
    <div className="space-y-3">
      {PREDICTORS.map((predictor) => (
        <PredictorSection
          key={predictor.key}
          predictor={predictor}
          predictions={predictions.filter((p) => p.model_name === predictor.key)}
          fixtureMap={fixtureMap}
        />
      ))}
    </div>
  );
}
