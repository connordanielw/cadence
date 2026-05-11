import Link from "next/link";

const FEATURES = [
  {
    label: "01",
    title: "Describe, don't filename",
    desc: "Search by mood, key, era, or instrumentation in plain language. No folders, no guessing.",
  },
  {
    label: "02",
    title: "Claude reads the music",
    desc: "Every upload is analysed by Claude — mood, tonality, tempo, instrumentation extracted automatically.",
  },
  {
    label: "03",
    title: "PDF & audio",
    desc: "Drop in sheet music PDFs or audio files. Cadence handles both and indexes everything.",
  },
  {
    label: "04",
    title: "Yours alone",
    desc: "Your library is private. No one else can see, search, or access your pieces.",
  },
];

export default function HomePage() {
  return (
    <div className="home">

      {/* ── Hero ────────────────────────────────────────────────── */}
      <section className="hero">
        <div className="hero__glow" />
        <p className="hero__eyebrow">AI-powered music library</p>
        <h1 className="hero__title">
          Find your music<br />by how it <em>feels</em>.
        </h1>
        <p className="hero__sub">
          Upload sheet music and audio. Cadence tags everything with AI
          and lets you search by feel, key, mood, or era — not by filename.
        </p>
        <div className="hero__cta">
          <Link href="/sign-up" className="hero__btn-primary">Get started free</Link>
          <Link href="/sign-in" className="hero__btn-ghost">Log in →</Link>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────── */}
      <section className="lp-features">
        <p className="lp-section-label">What Cadence does</p>
        <div className="lp-feature-grid">
          {FEATURES.map((f) => (
            <div key={f.label} className="lp-feature">
              <span className="lp-feature__num">{f.label}</span>
              <h3 className="lp-feature__title">{f.title}</h3>
              <p className="lp-feature__desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────────── */}
      <section className="lp-how">
        <div className="lp-how__copy">
          <p className="lp-section-label">How it works</p>
          <h2 className="lp-how__title">Three steps from upload to searchable.</h2>
          <ol className="lp-steps">
            <li><strong>Drop a file.</strong> PDF, MP3, WAV, FLAC — any format.</li>
            <li><strong>Claude analyses it.</strong> Mood, key, era, instrumentation — all extracted.</li>
            <li><strong>Search naturally.</strong> "Melancholy Romantic piano" returns exactly that.</li>
          </ol>
          <Link href="/sign-up" className="hero__btn-primary" style={{ display: "inline-flex", marginTop: 8 }}>
            Try it free
          </Link>
        </div>
        <div className="lp-how__demo">
          <div className="demo-card">
            <div className="demo-card__bar">
              <span className="demo-dot" />
              <span className="demo-dot" />
              <span className="demo-dot" />
              <span className="demo-card__title">Search</span>
            </div>
            <div className="demo-card__body">
              <div className="demo-query">&ldquo;sparse melancholy piano, minor key&rdquo;</div>
              <div className="demo-results">
                <div className="demo-result">
                  <span className="demo-result__score">97%</span>
                  <div>
                    <div className="demo-result__name">Gymnopédie No.1</div>
                    <div className="demo-result__tags">melancholy · E major · Romantic</div>
                  </div>
                </div>
                <div className="demo-result">
                  <span className="demo-result__score">91%</span>
                  <div>
                    <div className="demo-result__name">Clair de Lune</div>
                    <div className="demo-result__tags">introspective · D♭ major · Impressionist</div>
                  </div>
                </div>
                <div className="demo-result demo-result--dim">
                  <span className="demo-result__score">84%</span>
                  <div>
                    <div className="demo-result__name">Nocturne Op.9 No.2</div>
                    <div className="demo-result__tags">lyrical · E♭ major · Romantic</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────── */}
      <section className="lp-cta">
        <div className="lp-cta__glow" />
        <h2 className="lp-cta__title">Your library is waiting.</h2>
        <p className="lp-cta__sub">Free to start. No credit card required.</p>
        <Link href="/sign-up" className="hero__btn-primary lp-cta__btn">Create your library →</Link>
      </section>

    </div>
  );
}
