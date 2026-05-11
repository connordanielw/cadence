"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import PieceCard from "@/components/PieceCard";
import { deletePiece, listLibrary, type Piece } from "@/lib/api";

export default function LibraryPage() {
  const { getToken } = useAuth();
  const [pieces,     setPieces]     = useState<Piece[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try   {
      const token = await getToken();
      setPieces(await listLibrary(token));
    }
    catch (e) { setError(e instanceof Error ? e.message : "Unknown error"); }
    finally   { setLoading(false); }
  }, [getToken]);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    const stillWorking = pieces.some((p) => p.status === "pending" || p.status === "processing");
    if (!stillWorking) return;
    const id = setInterval(() => void load(), 3000);
    return () => clearInterval(id);
  }, [pieces, load]);

  async function onDelete(id: number) {
    setDeletingId(id);
    try   {
      const token = await getToken();
      await deletePiece(id, token);
      setPieces((prev) => prev.filter((p) => p.id !== id));
    }
    finally { setDeletingId(null); }
  }

  const ready      = pieces.filter((p) => p.status === "ready").length;
  const processing = pieces.filter((p) => p.status === "pending" || p.status === "processing").length;
  const failed     = pieces.filter((p) => p.status === "failed").length;

  return (
    <div>
      {/* Window */}
      <div className="win">
        <div className="win__bar">
          <div className="row" style={{ alignItems: "flex-start" }}>
            <div>
              <h1 style={{ marginBottom: 6 }}>Library</h1>
              <p>Every piece you&apos;ve uploaded, newest first. Pieces are searchable once their status is Ready.</p>
            </div>
            <button
              className="btn btn--ghost"
              onClick={load}
              disabled={loading}
              style={{ marginLeft: "auto", flexShrink: 0, marginTop: 4 }}
            >
              {loading ? "Loading…" : "↻ Refresh"}
            </button>
          </div>
        </div>

        {/* Stats in the window body */}
        {!loading && pieces.length > 0 && (
          <div className="win__body" style={{ paddingBottom: 20 }}>
            <div className="stats-bar">
              <div className="stat-pill">
                <span className="stat-pill__num">{pieces.length}</span>
                <span className="stat-pill__label">Total pieces</span>
              </div>
              <div className="stat-pill stat-pill--ready">
                <span className="stat-pill__num">{ready}</span>
                <span className="stat-pill__label">Ready to search</span>
              </div>
              {processing > 0 && (
                <div className="stat-pill stat-pill--processing">
                  <span className="stat-pill__num">{processing}</span>
                  <span className="stat-pill__label">Processing</span>
                </div>
              )}
              {failed > 0 && (
                <div className="stat-pill stat-pill--failed">
                  <span className="stat-pill__num">{failed}</span>
                  <span className="stat-pill__label">Failed</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {error && <p style={{ color: "var(--strawberry)", marginBottom: 16, fontSize: 14 }}>{error}</p>}

      {/* Empty */}
      {!loading && pieces.length === 0 && (
        <div className="empty-state">
          <span className="empty-state__icon">🎼</span>
          <div className="empty-state__title">Your library is empty</div>
          <div className="empty-state__body">
            Upload sheet music PDFs or audio files and Cadence will tag and index them for semantic search.
          </div>
          <Link href="/upload" className="btn" style={{ marginTop: 22, display: "inline-block" }}>
            Upload your first piece →
          </Link>
        </div>
      )}

      {pieces.length > 0 && (
        <div className="results">
          {pieces.map((p) => (
            <PieceCard
              key={p.id}
              piece={p}
              onDelete={deletingId === p.id ? undefined : () => onDelete(p.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
