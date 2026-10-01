"use client";

import { useEffect, useState } from "react";

const KEY = "genlingo.nextSubmitAt";

/**
 * Client-side mirror of the server's 20 s rule: only for showing a countdown. The server is the
 * one that enforces it (a refresh or a second tab can't get around it).
 */
export function useCooldown() {
  // Forms render only on the client (after sign-in), so reading storage here is safe.
  const [until, setUntil] = useState<number>(() => {
    try {
      return Number(sessionStorage.getItem(KEY)) || 0;
    } catch {
      return 0; // storage blocked: the countdown starts at 0, the server still enforces
    }
  });
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (until <= now) return;
    const t = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(t);
  }, [until, now]);

  const start = (ms: number) => {
    const t = Date.now() + ms;
    setUntil(t);
    setNow(Date.now());
    try {
      sessionStorage.setItem(KEY, String(t));
    } catch {
      /* ignore */
    }
  };
  const remainingMs = Math.max(0, until - now);
  return { remainingMs, seconds: Math.ceil(remainingMs / 1000), start };
}
