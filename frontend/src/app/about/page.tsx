import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="win" style={{ maxWidth: 680, margin: "0 auto" }}>
      <div className="win__bar">
        <h1>About Cadence</h1>
        <p>Semantic search for musicians and composers.</p>
      </div>
      <div className="win__body" style={{ padding: "28px 32px" }}>
        <p style={{ marginBottom: 16 }}>
          Cadence is a personal music library tool that uses AI to tag and semantically index your sheet music and audio files. Instead of searching by filename, you describe what you&apos;re looking for — the feel, the key, the era — and Cadence finds it.
        </p>
        <p style={{ marginBottom: 16 }}>
          Built with Next.js, FastAPI, PostgreSQL with pgvector, Claude (Anthropic), and VoyageAI embeddings.
        </p>
        <Link href="/sign-up" className="btn" style={{ display: "inline-block", marginTop: 8 }}>
          Get started →
        </Link>
      </div>
    </div>
  );
}
