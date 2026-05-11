"use client";

import { useCallback, useEffect, useState } from "react";
import PieceCard      from "@/components/PieceCard";
import UploadDropzone from "@/components/UploadDropzone";
import { getPiece, upload, type Piece } from "@/lib/api";

const STEPS = [
  { n: "01", title: "Drop your file",         desc: "PDF, MP3, WAV, FLAC, M4A, OGG, or AIFF — drop it in or click to browse." },
  { n: "02", title: "Cadence processes it",   desc: "Audio is transcribed; PDFs are parsed for notation and structure." },
  { n: "03", title: "Claude generates tags",  desc: "Mood, key, era, tempo, instrumentation — extracted automatically." },
  { n: "04", title: "Search semantically",    desc: "Describe what you want in plain English and Cadence finds the closest match." },
];

export default function UploadPage() {
  const [pending, setPending] = useState<Piece[]>([]);
  const [busy,    setBusy]    = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  async function handle(files: File[]) {
    setBusy(true); setError(null);
    try {
      const created = await Promise.all(files.map((f) => upload(f)));
      setPending((prev) => [...created, ...prev]);
    }
    catch (e) { setError(e instanceof Error ? e.message : "Unknown error"); }
    finally   { setBusy(false); }
  }

  // Poll for status updates on pieces that are still in-flight
  const refreshPending = useCallback(async () => {
    const inFlight = pending.filter((p) => p.status === "pending" || p.status === "processing");
    if (inFlight.length === 0) return;
    const updated = await Promise.all(inFlight.map((p) => getPiece(p.id).catch(() => p)));
    setPending((prev) =>
      prev.map((p) => updated.find((u) => u.id === p.id) ?? p)
    );
  }, [pending]);

  useEffect(() => {
    const inFlight = pending.some((p) => p.status === "pending" || p.status === "processing");
    if (!inFlight) return;
    const id = setInterval(() => void refreshPending(), 3000);
    return () => clearInterval(id);
  }, [pending, refreshPending]);

  return (
    <div>
      {/* Window */}
      <div className="win">
        <div className="win__bar">
          <h1>Upload</h1>
          <p>Add sheet music or audio to your library. Cadence tags it with Claude and makes it semantically searchable.</p>
        </div>

        <div className="win__body win__body--split">
          {/* Left — how it works */}
          <div>
            <h3 style={{ marginBottom: 18, fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>How it works</h3>
            <div className="process-steps">
              {STEPS.map((s) => (
                <div key={s.n} className="process-step">
                  <div className="process-step__num">{s.n}</div>
                  <div>
                    <p className="process-step__title">{s.title}</p>
                    <p className="process-step__desc">{s.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right — dropzone */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <UploadDropzone onUpload={handle} busy={busy} />
            {error && <p style={{ color: "var(--strawberry)", fontSize: 14, margin: 0 }}>{error}</p>}
          </div>
        </div>
      </div>

      {/* Just added */}
      {pending.length > 0 && (
        <div>
          <h2 style={{ marginBottom: 6, fontSize: 16 }}>Just added</h2>
          <p className="muted" style={{ marginBottom: 16, fontSize: 14 }}>
            {pending.some((p) => p.status === "pending" || p.status === "processing")
              ? "Processing…"
              : "Done — head to the Library to search."}
          </p>
          <div className="results">
            {pending.map((p) => <PieceCard key={p.id} piece={p} />)}
          </div>
        </div>
      )}
    </div>
  );
}
