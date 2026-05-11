import Link from "next/link";

const FEATURES = [
  {
    icon: "🎵",
    title: "Semantic search",
    desc: "Describe what you need in plain English — mood, key, era, instrumentation — and Cadence finds it.",
  },
  {
    icon: "🤖",
    title: "AI-powered tagging",
    desc: "Claude automatically extracts mood, key, tempo, era, and instrumentation from every upload.",
  },
  {
    icon: "📄",
    title: "PDF & audio",
    desc: "Upload sheet music PDFs or audio files. Cadence processes both and makes them searchable.",
  },
  {
    icon: "🔒",
    title: "Your library, private",
    desc: "Every piece belongs to you. Your library is only visible to you.",
  },
];

export default function HomePage() {
  return (
    <div className="home">
      {/* Hero */}
      <section className="hero">
        <h1 className="hero__title">
          Your music library,<br />semantically searchable.
        </h1>
        <p className="hero__sub">
          Upload sheet music and audio. Cadence tags everything with AI and lets you search by feel, not filename.
        </p>
        <div className="hero__cta">
          <Link href="/sign-up" className="btn hero__btn--primary">Get started free</Link>
          <Link href="/sign-in" className="btn btn--ghost hero__btn--secondary">Log in</Link>
        </div>
      </section>

      {/* Features */}
      <section className="features">
        {FEATURES.map((f) => (
          <div key={f.title} className="feature-card">
            <span className="feature-card__icon">{f.icon}</span>
            <h3 className="feature-card__title">{f.title}</h3>
            <p className="feature-card__desc">{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Bottom CTA */}
      <section className="home-cta">
        <h2>Ready to find your music faster?</h2>
        <p>Free to start. No credit card required.</p>
        <Link href="/sign-up" className="btn">Create your library →</Link>
      </section>
    </div>
  );
}
