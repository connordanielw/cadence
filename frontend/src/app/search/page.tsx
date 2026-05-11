"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import PieceCard from "@/components/PieceCard";
import SearchBar from "@/components/SearchBar";
import { search, type PieceWithScore } from "@/lib/api";

const EXAMPLES = [
  { q: "sparse melancholy piano, minor key",   color: "bondi"      },
  { q: "lively Baroque string ensemble",       color: "grape"      },
  { q: "dramatic late-Romantic orchestra",     color: "tangerine"  },
  { q: "gentle Impressionist solo",            color: "lime"       },
  { q: "energetic jazz combo, brass-forward",  color: "strawberry" },
];

export default function SearchPage() {
  const { getToken, isLoaded } = useAuth();
  const [results,     setResults]     = useState<PieceWithScore[]>([]);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  async function run(q: string, filters: { mood?: string; key?: string; era?: string }) {
    if (!isLoaded) return;
    setLoading(true); setError(null); setHasSearched(true);
    try   {
      const token = await getToken();
      setResults(await search(q, filters, token));
    }
    catch (e) { setError(e instanceof Error ? e.message : "Unknown error"); }
    finally   { setLoading(false); }
  }

  return (
    <div>
      {/* Window */}
      <div className="win">
        <div className="win__bar">
          <h1>Search your library</h1>
          <p>Describe what you&apos;re looking for — mood, key, era, instrumentation — and Cadence finds the closest match semantically.</p>
        </div>
        <div className="win__body">
          <SearchBar onSearch={run} loading={loading} />
          {error && <p style={{ color: "var(--strawberry)", marginTop: 12, fontSize: 14 }}>{error}</p>}
        </div>
      </div>

      {/* Example chips */}
      {!hasSearched && (
        <div className="examples-block">
          <p className="examples-label">Try searching for</p>
          <div className="examples-chips">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.q}
                className={`example-chip example-chip--${ex.color}`}
                onClick={() => run(ex.q, {})}
              >
                {ex.q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* No results */}
      {hasSearched && !loading && results.length === 0 && !error && (
        <div className="empty-state">
          <span className="empty-state__icon">🔍</span>
          <div className="empty-state__title">No matches found</div>
          <div className="empty-state__body">
            Try rephrasing your query, or upload more pieces to your library first.
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div className="results">
          {results.map((p) => <PieceCard key={p.id} piece={p} />)}
        </div>
      )}
    </div>
  );
}
