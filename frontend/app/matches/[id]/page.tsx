import { getFixture } from "@/lib/api";
import PredictionCard from "@/components/PredictionCard";
import SirKimForm from "@/components/SirKimForm";
import TeamLogo from "@/components/TeamLogo";
import MatchContextDebug from "@/components/MatchContextDebug";
import Link from "next/link";

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const fixture = await getFixture(parseInt(id));

  if (!fixture) {
    return (
      <div className="text-center py-20 text-wc-muted">
        Fixture not found.{" "}
        <Link href="/matches" className="text-wc-gold hover:underline">
          Back to matches
        </Link>
      </div>
    );
  }

  return (
    <div>
      <Link href="/matches" className="text-sm text-wc-muted hover:text-wc-gold transition-colors">
        ← Matches
      </Link>

      <div className="mt-4 mb-8">
        <div className="text-xs text-wc-gold uppercase tracking-widest">{fixture.league}</div>
        <div className="flex items-center gap-3 mt-1 flex-wrap">
          <TeamLogo src={fixture.home_team_crest} alt={fixture.home_team} className="w-10 h-10" />
          <h1 className="text-3xl font-bold text-white">{fixture.home_team}</h1>
          <span className="text-xl text-wc-muted">vs</span>
          <h1 className="text-3xl font-bold text-white">{fixture.away_team}</h1>
          <TeamLogo src={fixture.away_team_crest} alt={fixture.away_team} className="w-10 h-10" />
        </div>
        <div className="mt-2 flex items-center gap-4 text-sm text-wc-muted">
          <span>{formatDate(fixture.kickoff_at)}</span>
          {fixture.status === "finished" && fixture.result && (
            <span className="bg-wc-blue/30 text-white text-xs px-2 py-0.5 rounded-full capitalize border border-wc-blue">
              Result: {fixture.result} ({fixture.home_goals}–{fixture.away_goals})
            </span>
          )}
        </div>
      </div>

      {fixture.predictions.length === 0 ? (
        <SirKimForm
          fixtureId={fixture.id}
          homeTeam={fixture.home_team}
          awayTeam={fixture.away_team}
          homeTeamCrest={fixture.home_team_crest}
          awayTeamCrest={fixture.away_team_crest}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {fixture.predictions.map((p) => (
            <PredictionCard key={p.id} prediction={p} />
          ))}
        </div>
      )}

      {fixture.predictions.length > 0 && (
        <MatchContextDebug predictions={fixture.predictions} />
      )}
    </div>
  );
}
