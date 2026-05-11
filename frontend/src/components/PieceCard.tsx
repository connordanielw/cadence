"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { useAuth } from "@clerk/nextjs";
import type { Piece, PieceTags, PieceWithScore } from "@/lib/api";
import { patchPiece } from "@/lib/api";

interface Props {
  piece: Piece | PieceWithScore;
  onDelete?: () => void;
  onUpdate?: (updated: Piece) => void;
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

export default function PieceCard({ piece, onDelete, onUpdate }: Props) {
  const { getToken } = useAuth();
  const score   = "score" in piece ? piece.score : undefined;
  const tags    = piece.llm_tags ?? {};

  const [expanded, setExpanded]   = useState(false);
  const [editing,  setEditing]    = useState(false);
  const [saving,   setSaving]     = useState(false);

  // Editable copies
  const [editDesc, setEditDesc]   = useState(piece.description ?? "");
  const [editMood, setEditMood]   = useState<string[]>(tags.mood ?? []);
  const [editInst, setEditInst]   = useState<string[]>(tags.instrumentation ?? []);
  const [editKey,  setEditKey]    = useState(tags.key ?? "");
  const [editEra,  setEditEra]    = useState(tags.era ?? "");
  const [editTempo,setEditTempo]  = useState(tags.tempo_feel ?? "");
  const [editBpm,  setEditBpm]    = useState(tags.bpm?.toString() ?? "");
  const [newTag,   setNewTag]     = useState("");
  const [tagTarget,setTagTarget]  = useState<"mood"|"instrumentation">("mood");
  const newTagRef = useRef<HTMLInputElement>(null);

  const inlineTags = [
    editKey,
    editEra,
    editTempo,
    editBpm ? `${editBpm} bpm` : null,
  ].filter(Boolean).join(" · ");
  const pills = [...editMood, ...editInst].slice(0, editing ? 999 : 4);

  function startEdit() {
    setEditDesc(piece.description ?? "");
    setEditMood(tags.mood ?? []);
    setEditInst(tags.instrumentation ?? []);
    setEditKey(tags.key ?? "");
    setEditEra(tags.era ?? "");
    setEditTempo(tags.tempo_feel ?? "");
    setEditBpm(tags.bpm?.toString() ?? "");
    setEditing(true);
    setExpanded(true);
  }

  function cancelEdit() {
    setEditing(false);
  }

  async function save() {
    setSaving(true);
    try {
      const token = await getToken();
      const updated = await patchPiece(piece.id, {
        description: editDesc,
        llm_tags: {
          mood: editMood,
          instrumentation: editInst,
          key: editKey || null,
          era: editEra || null,
          tempo_feel: editTempo || null,
          bpm: editBpm ? parseInt(editBpm, 10) : null,
          summary: tags.summary,
        } as PieceTags,
      }, token);
      onUpdate?.(updated);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  function removeTag(list: string[], setList: (v: string[]) => void, val: string) {
    setList(list.filter(t => t !== val));
  }

  function addTag(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key !== "Enter" || !newTag.trim()) return;
    e.preventDefault();
    const val = newTag.trim();
    if (tagTarget === "mood" && !editMood.includes(val))    setEditMood([...editMood, val]);
    if (tagTarget === "instrumentation" && !editInst.includes(val)) setEditInst([...editInst, val]);
    setNewTag("");
  }

  return (
    <article className="card">
      {/* ── Top row ── */}
      <div className="pc-head">
        <h2 className="pc-title">{piece.title.replace(/\.[^.]+$/, "")}</h2>
        <div className="pc-head-right">
          {score !== undefined && <ScorePill score={score} />}
          {piece.status === "ready" && !editing && (
            <button className="pc-edit-btn" onClick={startEdit} title="Edit tags">✎</button>
          )}
          {onDelete && !editing && (
            <button className="pc-delete" onClick={onDelete} title="Delete">✕</button>
          )}
        </div>
      </div>

      {/* ── Meta row ── */}
      <div className="pc-meta">
        <StatusDot status={piece.status} />
        <span className="pc-meta__status">
          {piece.status === "processing" ? "Processing…" :
           piece.status === "failed"     ? "Failed" :
           piece.source_type === "pdf"   ? "Sheet music" : "Audio"}
        </span>
        {!editing && inlineTags && <><span className="pc-meta__sep">·</span><span className="pc-meta__tags">{inlineTags}</span></>}
      </div>

      {/* ── Inline field editors (key / era / tempo) ── */}
      {editing && (
        <div className="pc-inline-fields">
          <input className="pc-field-input" placeholder="Key (e.g. C minor)" value={editKey}   onChange={e => setEditKey(e.target.value)} />
          <input className="pc-field-input" placeholder="Era"                value={editEra}   onChange={e => setEditEra(e.target.value)} />
          <input className="pc-field-input" placeholder="Tempo feel"         value={editTempo} onChange={e => setEditTempo(e.target.value)} />
          <input className="pc-field-input" placeholder="BPM"  type="number" value={editBpm}   onChange={e => setEditBpm(e.target.value)} style={{ maxWidth: 80 }} />
        </div>
      )}

      {/* ── Description ── */}
      {piece.status === "ready" && (
        editing ? (
          <textarea
            className="pc-desc-edit"
            value={editDesc}
            onChange={e => setEditDesc(e.target.value)}
            rows={4}
          />
        ) : piece.description ? (
          <>
            <p className={`pc-desc${expanded ? " pc-desc--expanded" : ""}`}>{piece.description}</p>
            <button className="pc-expand-btn" onClick={() => setExpanded(v => !v)}>
              {expanded ? "Show less ↑" : "Show more ↓"}
            </button>
          </>
        ) : null
      )}

      {piece.status === "failed" && piece.error && (
        <p className="piece-card__error">{piece.error}</p>
      )}

      {/* ── Pills ── */}
      {(pills.length > 0 || editing) && (
        <div className="pc-pills">
          {editMood.map(m => (
            <span key={`m-${m}`} className="tag">
              {m}{editing && <button className="tag-remove" onClick={() => removeTag(editMood, setEditMood, m)}>×</button>}
            </span>
          ))}
          {editInst.map(i => (
            <span key={`i-${i}`} className={`tag tag--inst`}>
              {i}{editing && <button className="tag-remove" onClick={() => removeTag(editInst, setEditInst, i)}>×</button>}
            </span>
          ))}

          {editing && (
            <div className="pc-add-tag">
              <select className="pc-tag-select" value={tagTarget} onChange={e => setTagTarget(e.target.value as "mood"|"instrumentation")}>
                <option value="mood">mood</option>
                <option value="instrumentation">instrument</option>
              </select>
              <input
                ref={newTagRef}
                className="pc-tag-input"
                placeholder="Add tag, press Enter"
                value={newTag}
                onChange={e => setNewTag(e.target.value)}
                onKeyDown={addTag}
              />
            </div>
          )}
        </div>
      )}

      {/* ── Edit actions ── */}
      {editing && (
        <div className="pc-edit-actions">
          <button className="btn btn--ghost" style={{ fontSize: 13, padding: "4px 12px" }} onClick={cancelEdit} disabled={saving}>Cancel</button>
          <button className="btn" style={{ fontSize: 13, padding: "4px 14px" }} onClick={save} disabled={saving}>{saving ? "Saving…" : "Save"}</button>
        </div>
      )}
    </article>
  );
}
