"use client";

import Link from "next/link";
import { useUser } from "@clerk/nextjs";

export default function LpBottomCta() {
  const { isSignedIn, isLoaded } = useUser();

  if (!isLoaded || isSignedIn) return null;

  return (
    <section className="lp-cta">
      <div className="lp-cta__glow" />
      <h2 className="lp-cta__title">Your library is waiting.</h2>
      <p className="lp-cta__sub">Free to start. No credit card required.</p>
      <Link href="/sign-up" className="hero__btn-primary lp-cta__btn">Create your library →</Link>
    </section>
  );
}
