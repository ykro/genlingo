"use client";

import { useEffect, useState } from "react";

export interface PublicConfig {
  firebase: { apiKey: string; authDomain: string; projectId: string; appId: string };
  database: string;
  event: string;
  country: "MX" | "GT" | "CO" | "LATAM";
  audienceUrl: string;
  duelUrl: string;
}

let cached: Promise<PublicConfig> | null = null;

export function loadConfig(): Promise<PublicConfig> {
  cached ??= fetch("/api/config", { cache: "no-store" }).then((r) => {
    if (!r.ok) throw new Error(`config ${r.status}`);
    return r.json();
  });
  cached.catch(() => (cached = null)); // allow a retry after a failed load
  return cached;
}

export function useConfig() {
  const [config, setConfig] = useState<PublicConfig | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let alive = true;
    loadConfig()
      .then((c) => alive && setConfig(c))
      .catch((e) => alive && setError(e));
    return () => {
      alive = false;
    };
  }, [attempt]);
  return { config, error, retry: () => (setError(null), setAttempt((n) => n + 1)) };
}

export const DIRECTION_LABEL = {
  genz_to_parent: "Gen Z → papás",
  parent_to_genz: "Papás → Gen Z",
} as const;

export const COUNTRY_LABEL = { MX: "México", GT: "Guatemala", CO: "Colombia", LATAM: "Latinoamérica" } as const;
