import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "@/app/globals.css";
import Nav    from "@/components/Nav";
import Footer from "@/components/Footer";
import { ThemeProvider } from "@/lib/theme";

export const metadata: Metadata = {
  title: "Cadence — Semantic Music Search",
  description: "Semantic search for your sheet music and audio library.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider afterSignOutUrl="/sign-in">
      <html lang="en">
        <body>
          <ThemeProvider>
            <div className="app-shell">
              <Nav />
              <main className="container">{children}</main>
              <Footer />
            </div>
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
