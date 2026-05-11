"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Accent = "bondi" | "grape" | "tangerine" | "lime" | "strawberry";

interface ThemeCtx { accent: Accent; set: (a: Accent) => void; }
const Ctx = createContext<ThemeCtx>({ accent: "bondi", set: () => {} });

function applyAccent(a: Accent) {
  document.documentElement.dataset.accent = a;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [accent, setA] = useState<Accent>("bondi");

  useEffect(() => {
    const saved = (localStorage.getItem("cadence-accent") ?? "bondi") as Accent;
    setA(saved);
    applyAccent(saved);
  }, []);

  function set(a: Accent) {
    setA(a);
    localStorage.setItem("cadence-accent", a);
    applyAccent(a);
  }

  return <Ctx.Provider value={{ accent, set }}>{children}</Ctx.Provider>;
}

export const useTheme = () => useContext(Ctx);
