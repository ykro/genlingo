/**
 * "One phrase every 20 s per person", enforced on the server.
 *
 * The check and the update happen in one Firestore transaction, so two requests fired at the
 * same time from the same phone can't both pass. The client only ever sees the answer.
 */

import { RATE_LIMIT_MS } from "./model";

export type RateDecision = { ok: true } | { ok: false; retryAfterMs: number };

export function decide(lastMs: number | undefined, nowMs: number, windowMs = RATE_LIMIT_MS): RateDecision {
  if (lastMs === undefined || nowMs - lastMs >= windowMs) return { ok: true };
  return { ok: false, retryAfterMs: windowMs - (nowMs - lastMs) };
}

export function retryMessage(retryAfterMs: number): string {
  const s = Math.ceil(retryAfterMs / 1000);
  return `Espera ${s} ${s === 1 ? "segundo" : "segundos"} antes de enviar otra frase.`;
}
