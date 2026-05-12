"use client";

import { useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import PieceCard from "@/components/PieceCard";
import { upload, type Piece } from "@/lib/api";

const ACCEPT = ".pdf,.mp3,.wav,.flac,.m4a,.ogg,.aiff,.aif";

export default function UploadPage() {
  const { getToken, isLoaded } = useAuth();

  // Step 1: file selected
  const [file, setFile]         = useState<File | null>(null);
  const [hot,  setHot]          = useState(false);
  const inputRef                = useRef<HTMLInputElement>(null);

  // Step 2: description
  const [description, setDesc]  = useState("");

  // Submission
  const [busy,    setBusy]      = useState(false);
  const [error,   setError]     = useState<string | null>(null);
  const [added,   setAdded]     = useState<Piece[]>([]);

  function pickFile(files: FileList | null) {
    if (!files || files.length === 0) return;
    setFile(files[0]);
    setError(null);
  }

  function reset() {
    setFile(null);
    setDesc("");
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  async function submit() {
    if (!file || !description.trim() || !isLoaded) return;
    setBusy(true);
    setError(null);
    try {
      const token  = await getToken();
      const piece  = await upload(file, description.trim(), token);
      setAdded(prev => [piece, ...prev]);
      reset();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  const canSubmit = !!file && description.trim().length >= 10 && !busy;

  return (
    <div>
      <div className="win">
        <div className="win__bar">
          <h1>Upload</h1>
          <p>Add a piece to your library. Drop the file, describe what it sounds like, and Cadence makes it searchable.</p>
        </div>

        <div className="win__body">
          {!file ? (
            /* ── Step 1: pick a file ── */
            <label
              className={`dropzone ${hot ? "dropzone--hot" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setHot(true); }}
              onDragLeave={() => setHot(false)}
              onDrop={(e) => { e.preventDefault(); setHot(false); pickFile(e.dataTransfer.files); }}
            >
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPT}
                hidden
                onChange={(e) => pickFile(e.target.files)}
              />
              <span className="dropzone__icon">🎵</span>
              <div className="dropzone__label">Drop a file here, or click to browse</div>
              <div className="dropzone__hint">PDF · MP3 · WAV · FLAC · M4A · OGG · AIFF</div>
            </label>
          ) : (
            /* ── Step 2: describe it ── */
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div className="upload-file-row">
                <span className="upload-file-name">{file.name}</span>
                <button className="btn btn--ghost" style={{ fontSize: 12, padding: "3px 10px" }} onClick={reset} disabled={busy}>
                  Change
                </button>
              </div>

              <div>
                <label className="upload-label">
                  Describe this piece
                  <span className="upload-label__hint"> — instruments, mood, tempo, feel. The more specific, the better the search.</span>
                </label>
                <textarea
                  className="upload-desc-input"
                  rows={4}
                  placeholder={
                    file.name.match(/\.pdf$/i)
                      ? "e.g. Baroque keyboard suite in D minor, ornate and precise, lots of counterpoint"
                      : "e.g. Dark, dense strings with driving rhythm — tense and cinematic, builds throughout"
                  }
                  value={description}
                  onChange={(e) => setDesc(e.target.value)}
                  disabled={busy}
                  autoFocus
                />
                <p className="upload-char-hint" style={{ opacity: description.length < 10 ? 1 : 0 }}>
                  At least a few words to go on
                </p>
              </div>

              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <button className="btn" onClick={submit} disabled={!canSubmit}>
                  {busy ? "Adding to library…" : "Add to library"}
                </button>
                {busy && <span className="muted" style={{ fontSize: 13 }}>Claude is expanding your description…</span>}
              </div>
            </div>
          )}

          {error && (
            <p style={{ color: "var(--strawberry)", fontSize: 14, marginTop: 12 }}>{error}</p>
          )}
        </div>
      </div>

      {added.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h2 style={{ marginBottom: 6, fontSize: 16 }}>Just added</h2>
          <p className="muted" style={{ marginBottom: 16, fontSize: 14 }}>Head to the Library to search.</p>
          <div className="results">
            {added.map((p) => <PieceCard key={p.id} piece={p} />)}
          </div>
        </div>
      )}
    </div>
  );
}
