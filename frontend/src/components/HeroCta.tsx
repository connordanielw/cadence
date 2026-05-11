"use client";

import Link from "next/link";
import { useUser } from "@clerk/nextjs";

interface Props {
  /** Extra top margin, e.g. for the "How it works" section */
  marginTop?: number;
}

export default function HeroCta({ marginTop }: Props) {
  const { isSignedIn, isLoaded } = useUser();

  // Don't flash buttons while Clerk loads, and hide entirely once signed in
  if (!isLoaded || isSignedIn) return null;

  return (
    <div className="hero__cta" style={marginTop != null ? { marginTop } : undefined}>
      <Link href="/sign-up" className="hero__btn-primary">Get started free</Link>
      <Link href="/sign-in" className="hero__btn-ghost">Log in →</Link>
    </div>
  );
}
