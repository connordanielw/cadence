"use client";

import { useCallback, useState } from "react";

interface Props {
  onUpload: (files: File[]) => Promise<void>;
  busy: boolean;
}

const ACCEPT = ".pdf,.mp3,.wav,.flac,.m4a,.ogg,.aiff,.aif";

export default function UploadDropzone({ onUpload, busy }: Props) {
  const [hot, setHot] = useState(false);

  const handle = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      void onUpload(Array.from(files));
    },
    [onUpload],
  );

  return (
    <label
      className={`dropzone ${hot ? "dropzone--hot" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setHot(true); }}
      onDragLeave={() => setHot(false)}
      onDrop={(e) => { e.preventDefault(); setHot(false); handle(e.dataTransfer.files); }}
    >
      <input
        type="file"
        accept={ACCEPT}
        multiple
        hidden
        onChange={(e) => handle(e.target.files)}
        disabled={busy}
      />
      <span className="dropzone__icon">{busy ? "⏳" : "🎵"}</span>
      <div className="dropzone__label">
        {busy ? "Uploading…" : "Drop files here, or click to browse"}
      </div>
      <div className="dropzone__hint">PDF · MP3 · WAV · FLAC · M4A · OGG · AIFF</div>
    </label>
  );
}
