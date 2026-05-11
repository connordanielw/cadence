import type { Piece, PieceWithScore } from "@/lib/api";

interface Props {
  piece: Piece | PieceWithScore;
  onDelete?: () => void;
}

function ScorePill({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const cls = pct >= 75 ? "score-pill--high" : "score-pill--mid";
  return <span className={`score-pill ${cls}`}>{pct}%</span>;
}

function StatusDot({ status }: { status: string }) {
  const cls =
    status === "ready"      ? "status-dot--ready" :
    status === "processing" ? "status-dot--processing" :
    status === "failed"     ? "status-dot--failed" : "";
  return <span className={`status-dot ${cls}`} />;
}

const ERA_SHORT: Record<string, string> = {
  "Baroque": "Baroque", "Classical": "Classical", "Romantic": "Romantic",
  "Impressionist": "Impressionist", "Modern": "Modern", "Contemporary": "Contemporary",
  "Jazz": "Jazz",
};

export default function PieceCard({ piece, onDelete }: Props) {
  const score = "score" in piece ? piece.score : undefined;
  const tags  = piece.llm_tags ?? {};

  // Build a compact inline tag string: key · era · tempo
  const inlineTags = [
    tags.key,
    tags.era ? (ERA_SHORT[tags.era] ?? tags.era) : null,
    tags.tempo_feel,
  ].filter(Boolean).join(" · ");

  // Mood + instrumentation as pills (cap at 4)
  const pills = [
    ...(tags.mood ?? []),
    ...(tags.instrumentation ?? []),
  ].slice(0, 4);

  return (
    <article className="card">
      {/* ── Top row: title + score ── */}
      <div className="pc-head">
        <h2 className="pc-title">{piece.title.replace(/\.[^.]+$/, "")}</h2>
        {score !== undefined && <ScorePill score={score} />}
      </div>

      {/* ── Second row: status + inline tags ── */}
      <div className="pc-meta">
        <StatusDot status={piece.status} />
        <span className="pc-meta__status">
          {piece.status === "processing" ? "Processing…" :
           piece.status === "failed"     ? "Failed" :
           piece.source_type === "pdf"   ? "Sheet music" : "Audio"}
        </span>
        {inlineTags && <span className="pc-meta__sep">·</span>}
        {inlineTags && <span className="pc-meta__tags">{inlineTags}</span>}
      </div>

      {/* ── Description (clamped to 2 lines) ── */}
      {piece.description && piece.status === "ready" && (
        <p className="pc-desc">{piece.description}</p>
      )}

      {piece.status === "failed" && piece.error && (
        <p className="piece-card__error">{piece.error}</p>
      )}

      {/* ── Mood / instrumentation pills ── */}
      {pills.length > 0 && (
        <div className="pc-pills">
          {pills.map((p) => <span key={p} className="tag">{p}</span>)}
        </div>
      )}

      {/* ── Actions ── */}
      {onDelete && (
        <button className="pc-delete" onClick={onDelete} title="Delete">
          ✕
        </button>
      )}
    </article>
  );
}
