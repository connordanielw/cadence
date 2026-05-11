import type { Piece, PieceWithScore } from "@/lib/api";

interface Props {
  piece: Piece | PieceWithScore;
  onDelete?: () => void;
}

function ScorePill({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const cls = pct >= 75 ? "score-pill--high" : pct >= 50 ? "score-pill--mid" : "score-pill--low";
  return <span className={`score-pill ${cls}`}>{pct}%</span>;
}

function StatusDot({ status }: { status: string }) {
  const cls =
    status === "ready"      ? "status-dot--ready" :
    status === "processing" ? "status-dot--processing" :
    status === "failed"     ? "status-dot--failed" : "";
  return <span className={`status-dot ${cls}`} />;
}

const STATUS_LABEL: Record<string, string> = {
  pending:    "Pending",
  processing: "Processing…",
  ready:      "Ready",
  failed:     "Failed",
};

export default function PieceCard({ piece, onDelete }: Props) {
  const score = "score" in piece ? piece.score : undefined;
  const tags  = piece.llm_tags ?? {};

  return (
    <article className="card">
      <header className="piece-card__head">
        <h2 className="piece-card__title">{piece.title}</h2>
        <div className="piece-card__meta">
          {score !== undefined && <ScorePill score={score} />}
        </div>
      </header>

      <div className="piece-card__status">
        <StatusDot status={piece.status} />
        <span>{STATUS_LABEL[piece.status] ?? piece.status}</span>
        <span style={{ opacity: 0.3 }}>·</span>
        <span style={{ textTransform: "capitalize" }}>{piece.source_type}</span>
      </div>

      {piece.description && (
        <p className="piece-card__desc">{piece.description}</p>
      )}

      {piece.status === "failed" && piece.error && (
        <p className="piece-card__error">{piece.error}</p>
      )}

      <div className="piece-card__tags">
        {tags.mood?.map((m: string)         => <span key={`m-${m}`} className="tag">{m}</span>)}
        {tags.key                            && <span className="tag">{tags.key}</span>}
        {tags.tempo_feel                     && <span className="tag">{tags.tempo_feel}</span>}
        {tags.era                            && <span className="tag">{tags.era}</span>}
        {tags.instrumentation?.map((i: string) => <span key={`i-${i}`} className="tag">{i}</span>)}
      </div>

      {onDelete && (
        <div className="piece-card__actions">
          <button className="btn btn--danger" onClick={onDelete}>Delete</button>
        </div>
      )}
    </article>
  );
}
