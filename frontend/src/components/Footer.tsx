"use client";

import Link from "next/link";
import { useTheme, type Accent } from "@/lib/theme";

const ACCENTS: { id: Accent; label: string }[] = [
  { id: "bondi",      label: "Bondi"      },
  { id: "grape",      label: "Grape"      },
  { id: "tangerine",  label: "Tangerine"  },
  { id: "lime",       label: "Lime"       },
  { id: "strawberry", label: "Strawberry" },
];

export default function Footer() {
  const { accent, set } = useTheme();

  return (
    <footer className="footer">
      <div className="footer__inner">

        {/* Brand */}
        <div className="footer__brand-block">
          <span className="footer__logo">cadence</span>
          <p className="footer__tagline">Semantic search for your music library</p>
        </div>

        {/* Colour-theme picker */}
        <div className="footer__theme-picker">
          <span className="footer__theme-label">Theme</span>
          <div className="footer__swatches">
            {ACCENTS.map((c) => (
              <button
                key={c.id}
                className={`f-swatch f-swatch--${c.id}${accent === c.id ? " f-swatch--active" : ""}`}
                onClick={() => set(c.id)}
                title={c.label}
                aria-label={`${c.label} theme`}
              />
            ))}
          </div>
        </div>

        {/* Links */}
        <nav className="footer__links">
          <Link href="/"        className="footer__link">Search</Link>
          <Link href="/upload"  className="footer__link">Upload</Link>
          <Link href="/library" className="footer__link">Library</Link>
          <span className="footer__divider" />
          <a href="#" className="footer__link">Privacy</a>
          <a href="#" className="footer__link">Terms</a>
        </nav>

      </div>
      <div className="footer__bar">
        © {new Date().getFullYear()} Cadence · Powered by Voyage AI &amp; Claude
      </div>
    </footer>
  );
}
