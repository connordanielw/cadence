"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";

const links = [
  { href: "/",        label: "Search",  color: "bondi"     },
  { href: "/upload",  label: "Upload",  color: "tangerine" },
  { href: "/library", label: "Library", color: "grape"     },
];

export default function Nav() {
  const pathname = usePathname();
  return (
    <nav className="nav">
      <Link href="/" className="nav__brand">cadence</Link>
      <div className="nav__links">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={`nav__link nav__link--${l.color}`}
            aria-current={pathname === l.href ? "page" : undefined}
          >
            {l.label}
          </Link>
        ))}
        <SignedOut>
          <Link href="/sign-in" className="btn btn--ghost" style={{ padding: "5px 14px", fontSize: 13 }}>Log in</Link>
          <Link href="/sign-up" className="btn" style={{ padding: "5px 14px", fontSize: 13 }}>Sign up</Link>
        </SignedOut>
        <SignedIn>
          <UserButton />
        </SignedIn>
      </div>
    </nav>
  );
}
