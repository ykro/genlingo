/** Request validation. Error messages are user-facing, so they are in Spanish. */

import { AGE_RANGES, COUNTRIES, type Country, DIRECTIONS, type Direction, MAX_CHARS, MAX_WORDS } from "./model";

export class ValidationError extends Error {}

type Body = Record<string, unknown>;

function text(body: Body, field: string, label: string): string {
  const v = body[field];
  if (typeof v !== "string" || !v.trim()) throw new ValidationError(`Falta ${label}.`);
  const t = v.trim().replace(/\s+/g, " ");
  if (t.length > MAX_CHARS || t.split(" ").length > MAX_WORDS)
    throw new ValidationError(`${label[0].toUpperCase()}${label.slice(1)} debe tener como máximo ${MAX_WORDS} palabras.`);
  return t;
}

function direction(body: Body): Direction {
  const d = body.direction;
  if (!DIRECTIONS.includes(d as Direction)) throw new ValidationError("Elige una dirección: Gen Z → papás o papás → Gen Z.");
  return d as Direction;
}

function country(body: Body): Country {
  const c = body.country ?? "LATAM";
  if (!COUNTRIES.includes(c as Country)) throw new ValidationError("País no soportado.");
  return c as Country;
}

export function parsePhrase(body: Body) {
  return { text: text(body, "text", "la frase"), direction: direction(body), country: country(body) };
}

export function parsePair(body: Body) {
  const out = {
    source: text(body, "source", "la frase original"),
    target: text(body, "target", "la traducción"),
    direction: direction(body),
    country: country(body),
    ageRange: typeof body.ageRange === "string" && (AGE_RANGES as readonly string[]).includes(body.ageRange) ? body.ageRange : "unknown",
  };
  if (out.source.toLowerCase() === out.target.toLowerCase()) throw new ValidationError("La traducción no puede ser igual a la frase.");
  return out;
}

/** Firestore document ids we accept: auto-ids (20 chars) and the duel's round ids (12 hex). No paths. */
export const DOC_ID = /^[A-Za-z0-9_-]{1,64}$/;

export function parseDocId(id: unknown, label = "el id"): string {
  if (typeof id !== "string" || !DOC_ID.test(id)) throw new ValidationError(`${label[0].toUpperCase()}${label.slice(1)} no es válido.`);
  return id;
}

export function parseVote(body: Body) {
  if (typeof body.roundId !== "string" || !body.roundId) throw new ValidationError("Falta la ronda.");
  parseDocId(body.roundId, "la ronda");
  if (body.choice !== "david" && body.choice !== "goliath") throw new ValidationError("Vota por David o por Goliat.");
  return { roundId: body.roundId, choice: body.choice as "david" | "goliath" };
}

export function parseReview(body: Body) {
  if (body.action !== "approve" && body.action !== "reject") throw new ValidationError("Acción no válida.");
  return { action: body.action as "approve" | "reject" };
}
