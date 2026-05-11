"use client";

import { useState } from "react";

interface Props {
  onSearch: (q: string, filters: { mood?: string; key?: string; era?: string }) => void;
  loading: boolean;
}

export default function SearchBar({ onSearch, loading }: Props) {
  const [q, setQ] = useState("");
  const [mood, setMood] = useState("");
  const [era, setEra] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    onSearch(q.trim(), {
      mood: mood.trim() || undefined,
      era: era.trim() || undefined,
    });
  }

  const hasFilters = mood || era;

  return (
    <form className="col" onSubmit={submit} style={{ gap: 10 }}>
      <div className="search-input-row">
        <textarea
          className="textarea"
          rows={2}
          placeholder="e.g. sparse melancholy piano, minor key, late Romantic"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (q.trim() && !loading) submit(e as unknown as React.FormEvent);
            }
          }}
        />
        <button
          type="submit"
          className="btn"
          style={{ alignSelf: "flex-end" }}
          disabled={loading || !q.trim()}
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      <div>
        <button
          type="button"
          className="filters-toggle"
          onClick={() => setShowFilters((v) => !v)}
        >
          <span style={{ fontSize: 10 }}>{showFilters ? "▾" : "▸"}</span>
          Filters
          {hasFilters && !showFilters && (
            <span style={{ color: "var(--tangerine-solid)", marginLeft: 2 }}>●</span>
          )}
        </button>
      </div>

      {showFilters && (
        <div className="filter-inputs">
          <div>
            <label className="filter-label">Mood</label>
            <input className="input" placeholder="e.g. melancholy"
              value={mood} onChange={(e) => setMood(e.target.value)} />
          </div>
          <div>
            <label className="filter-label">Era</label>
            <input className="input" placeholder="e.g. Romantic"
              value={era} onChange={(e) => setEra(e.target.value)} />
          </div>
        </div>
      )}
    </form>
  );
}
