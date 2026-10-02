/**
 * What the audience API does, independent of HTTP and of Firestore (the store is injected).
 * Each function returns { status, body } so route handlers stay one-liners.
 */

import { blockedReason } from "./blocklist";
import { retryMessage } from "./rate-limit";
import type { AudienceStore } from "./store";
import { parsePair, parsePhrase, parseReview, parseVote, ValidationError } from "./validation";

export interface Ctx {
  store: AudienceStore;
  uid: string;
  event: string;
  now: number;
  /** Phrases that pass the blocklist go straight to the stage queue (no human needed). */
  autoApprove?: boolean;
}

export type Result = { status: number; body: Record<string, unknown> };

function guard(fn: () => Promise<Result>): Promise<Result> {
  return fn().catch((err) => {
    if (err instanceof ValidationError) return { status: 400, body: { error: err.message } };
    throw err;
  });
}

export function submitPhrase(ctx: Ctx, body: Record<string, unknown>): Promise<Result> {
  return guard(async () => {
    const p = parsePhrase(body);
    const reason = blockedReason(p.text);
    if (reason) return { status: 422, body: { error: "Esa frase no pasa el filtro. Prueba con otra.", reason } };
    // Rate limit after validation: a typo shouldn't cost you 20 seconds.
    const slot = await ctx.store.claimSubmission(ctx.uid, ctx.now);
    if (!slot.ok) return { status: 429, body: { error: retryMessage(slot.retryAfterMs), retryAfterMs: slot.retryAfterMs } };
    if (ctx.autoApprove) {
      const id = await ctx.store.addPhrase({ ...p, uid: ctx.uid, event: ctx.event, status: "approved", createdAt: ctx.now, approvedAt: ctx.now });
      return { status: 201, body: { id, status: "approved", message: "¡Lista! Puede salir en la pantalla en cualquier ronda." } };
    }
    const id = await ctx.store.addPhrase({ ...p, uid: ctx.uid, event: ctx.event, status: "pending", createdAt: ctx.now });
    return { status: 201, body: { id, status: "pending", message: "¡Listo! Tu frase espera aprobación." } };
  });
}

export function submitPair(ctx: Ctx, body: Record<string, unknown>): Promise<Result> {
  return guard(async () => {
    const p = parsePair(body);
    const reason = blockedReason(p.source) ?? blockedReason(p.target);
    if (reason) return { status: 422, body: { error: "Ese par no pasa el filtro. Prueba con otro.", reason } };
    const slot = await ctx.store.claimSubmission(ctx.uid, ctx.now);
    if (!slot.ok) return { status: 429, body: { error: retryMessage(slot.retryAfterMs), retryAfterMs: slot.retryAfterMs } };
    const id = await ctx.store.addPair({ ...p, uid: ctx.uid, event: ctx.event, status: "pending", createdAt: ctx.now });
    return { status: 201, body: { id, status: "pending", message: "¡Gracias! Tu par ayudará a entrenar a David." } };
  });
}

export function castVote(ctx: Ctx, body: Record<string, unknown>): Promise<Result> {
  return guard(async () => {
    const v = parseVote(body);
    const round = await ctx.store.getRound(v.roundId);
    if (!round || round.event !== ctx.event) return { status: 404, body: { error: "Esa ronda no existe." } };
    if (round.status !== "voting") return { status: 409, body: { error: "La votación de esta ronda ya cerró." } };
    const ok = await ctx.store.addVote(v.roundId, ctx.uid, v.choice, ctx.now);
    if (!ok) return { status: 409, body: { error: "Ya votaste en esta ronda." } };
    return { status: 201, body: { ok: true } };
  });
}

export function listQueue(ctx: Ctx, kind: "phrases" | "pairs"): Promise<Result> {
  return guard(async () => ({ status: 200, body: { items: await ctx.store.listPending(kind, ctx.event) } }));
}

export function reviewItem(ctx: Ctx, kind: "phrases" | "pairs", id: string, body: Record<string, unknown>): Promise<Result> {
  return guard(async () => {
    const { action } = parseReview(body);
    const ok = await ctx.store.review(kind, id, action === "approve" ? "approved" : "rejected", ctx.now);
    return ok ? { status: 200, body: { id, status: action === "approve" ? "approved" : "rejected" } } : { status: 404, body: { error: "No encontrado." } };
  });
}
